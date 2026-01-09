from django.views.generic import ListView, DetailView, TemplateView
from core.permissions import PermissionRequiredMixin
from .models import EngagementEvent, NextBestAction, EngagementStatus
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from core.permissions import PermissionRequiredMixin
from .models import NextBestAction, EngagementEvent,EngagementWorkflow,EngagementEventComment,PlaybookExecution,PlaybookStepExecution,PlaybookStep,EngagementPlaybook,NextBestActionComment,WebhookDeliveryLog
from .forms import NextBestActionForm, EngagementEventForm,EngagementWorkflowForm
from .services import DuplicateDetectionService, EventMergingService
from django.shortcuts import get_object_or_404
from accounts.models import Account
# apps/engagement/views.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg
# Function-based view for API compatibility (if needed)
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Q
import json
import logging

from .models import EngagementPlaybook, PlaybookStep
from .forms import EngagementPlaybookForm, PlaybookStepForm  # Need to create these forms



from django.db.models import Count, Avg, Sum, F
from django.db.models.functions import ExtractHour, ExtractWeekDay
from datetime import timedelta


class EngagementLeaderboardView(PermissionRequiredMixin, TemplateView):
    """
    Display a leaderboard of team members based on their engagement activities.
    
    The leaderboard ranks users by their total engagement scores generated through
    various engagement events. It provides motivation and visibility into team performance.
    """
    template_name = 'engagement/leaderboard.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        now = timezone.now()
        
        # Default to last 30 days
        days = int(self.request.GET.get('days', 30))
        start_date = now - timedelta(days=days)
        
        # Store period for display
        context['period'] = f"Last {days} days"
        
        # Get top engagers based on total engagement score
        # We aggregate by created_by (the user who created the engagement events)
        leaderboard_data = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).values(
            'created_by__id',
            'created_by__first_name',
            'created_by__last_name',
            'created_by__email'
        ).annotate(
            event_count=Count('id'),
            total_score=Sum('engagement_score')
        ).order_by('-total_score')
        
        context['leaderboard'] = leaderboard_data
        
        return context


class EngagementFeedView(PermissionRequiredMixin, ListView):
    model = EngagementEvent
    template_name = 'engagement/feed.html'
    context_object_name = 'events'
    paginate_by = 50
    required_permission = 'engagement:read'

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'account', 'account_company', 'lead', 'task', 'opportunity', 'created_by', 'contact', 'case'
        )
        
        # Filters
        event_type = self.request.GET.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
            
        account_id = self.request.GET.get('account_id')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        # Filter by tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_types'] = EngagementEvent._meta.get_field('event_type').choices
        return context

class EngagementDashboardView(PermissionRequiredMixin, TemplateView):
    template_name = 'engagement/dashboard.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        now = timezone.now()
        
        # Date range (default 30 days)
        days = int(self.request.GET.get('days', 30))
        start_date = now - timedelta(days=days)
        
        # Engagement Events
        events = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).select_related('account', 'account_company', 'lead', 'task', 'opportunity', 'contact', 'case')
        
        context['total_events'] = events.count()
        context['important_events'] = events.filter(is_important=True).count()
        context['recent_events'] = events.order_by('-created_at')[:10]
        
        # Engagement Score
        avg_score = events.aggregate(avg=Avg('engagement_score'))['avg']
        context['engagement_score'] = avg_score or 0.0
        
        # Get pending actions as a list for template use
        pending_actions = NextBestAction.objects.filter(
            tenant_id=tenant_id,
            completed=False
        ).select_related('account', 'assigned_to', 'contact')
        # Next Best Actions
        actions = NextBestAction.objects.filter(
            tenant_id=tenant_id,
            completed=False
        )
        context['pending_actions'] = pending_actions[:10]  # Limit for display
        context['pending_actions_count'] = pending_actions.count()  # For KPI card
        context['overdue_actions'] = actions.filter(due_date__lt=now).count()
        
        # Trend calculations (compare with previous period)
        prev_start = start_date - timedelta(days=days)
        prev_events = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=prev_start,
            created_at__lt=start_date
        )
        prev_total = prev_events.count()
        prev_important = prev_events.filter(is_important=True).count()
        prev_avg_score = prev_events.aggregate(avg=Avg('engagement_score'))['avg'] or 0.0
        
        # Calculate trends
        context['events_trend'] = self.calculate_trend(context['total_events'], prev_total)
        context['important_events_trend'] = self.calculate_trend(context['important_events'], prev_important)
        context['engagement_score_trend'] = self.calculate_trend(context['engagement_score'], prev_avg_score)
        
        # Chart data (Dynamic based on selected days)
        chart_labels = []
        chart_data = []
        event_type_data = []
        event_type_labels = []
        
        # Calculate daily counts
        for i in range(days - 1, -1, -1):
            date = now - timedelta(days=i)
            date_str = date.strftime('%m/%d')
            count = events.filter(created_at__date=date.date()).count()
            chart_labels.append(date_str)
            chart_data.append(count)
        
        # Event type distribution
        event_types = events.values('event_type').annotate(count=Count('event_type')).order_by('-count')[:7]
        for et in event_types:
            event_type_labels.append(dict(EngagementEvent.EVENT_TYPES).get(et['event_type'], et['event_type']))
            event_type_data.append(et['count'])

        # Heatmap Data: Activity by Hour of Day
        heatmap_data_qs = (
            EngagementEvent.objects.filter(tenant_id=tenant_id, created_at__gte=start_date)
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        
        # Initialize 24 hours with 0
        hourly_counts = [0] * 24
        for entry in heatmap_data_qs:
            if entry['hour'] is not None:
                hourly_counts[entry['hour']] = entry['count']
            
        context['heatmap_data'] = hourly_counts
        
        # ROI Analytics Data
        from .analytics import calculate_engagement_roi
        # Pass tenant_id if multi-tenant context is available (assuming view accounts for it)
        # For now, simplistic call
        context['roi_data'] = calculate_engagement_roi()

        context['chart_labels'] = chart_labels
        context['chart_data'] = chart_data
        context['event_type_labels'] = event_type_labels
        context['event_type_data'] = event_type_data
        context['now'] = now
        
        # NEW: Account-specific engagement timeline data
        context['account_timeline_data'] = self.get_account_engagement_timeline(tenant_id, start_date)
        
        # NEW: Contact-level engagement history data
        context['contact_history_data'] = self.get_contact_engagement_history(tenant_id, start_date)
        
        # NEW: Opportunity engagement journey data
        context['opportunity_journey_data'] = self.get_opportunity_engagement_journey(tenant_id, start_date)
        
        # NEW: Engagement comparison data
        context['engagement_comparison_data'] = self.get_engagement_comparison_data(tenant_id, start_date, days, now)
        
        # NEW: Engagement journey data
        context['engagement_journey_data'] = self.get_engagement_journey_data(tenant_id, start_date)
        
        # NEW: Engagement flow data for Sankey diagram
        context['engagement_flow_data'] = self.get_engagement_flow_data(tenant_id, start_date)
        
        # NEW: Relationship network data
        context['relationship_network_data'] = self.get_relationship_network_data(tenant_id, start_date)
        
        # NEW: Multi-dimensional heatmap data (7x24)
        context['heatmap_2d_data'] = self.get_engagement_heatmap_data(tenant_id, start_date)
        
        # NEW: Geographic engagement data
        context['geographic_data'] = self.get_geographic_engagement_data(tenant_id, start_date)
        
        return context

    
 

    def get_engagement_journey_data(self, tenant_id, start_date):
        """Get data for engagement journey mapping."""
        from django.db.models import Count
        
        # Get sequence of events for each account
        journey_data = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).values(
            'account_id',
            'event_type'
        ).annotate(
            event_count=Count('id')
        ).order_by('account_id', 'created_at')
        
        # Process into journey paths
        journeys = {}
        for event in journey_data:
            account_id = event['account_id']
            if account_id not in journeys:
                journeys[account_id] = []
            journeys[account_id].append({
                'event_type': event['event_type'],
                'count': event['event_count']
            })
            
        # Aggregate common paths
        path_counts = {}
        for account_id, path in journeys.items():
            path_key = ' -> '.join([p['event_type'] for p in path[:5]])  # First 5 events
            path_counts[path_key] = path_counts.get(path_key, 0) + 1
            
        # Return top paths
        sorted_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{'path': path, 'count': count} for path, count in sorted_paths]

    def get_engagement_flow_data(self, tenant_id, start_date):
        """Get data for Sankey diagram of engagement flows."""
        from django.db.models import Count
        
        # Get transitions between event types for each account
        events = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).order_by('account_id', 'created_at')
        
        transitions = {}
        prev_event_type = None
        prev_account_id = None
        
        event_type_display = dict(EngagementEvent.EVENT_TYPES)
        
        for event in events:
            current_type = event_type_display.get(event.event_type, event.event_type)
            if prev_account_id == event.account_id and prev_event_type:
                if prev_event_type != current_type: # Only track transitions between different types
                    transition_key = (prev_event_type, current_type)
                    transitions[transition_key] = transitions.get(transition_key, 0) + 1
                
            prev_event_type = current_type
            prev_account_id = event.account_id
            
        # Format for Sankey diagram
        nodes_list = []
        node_indices = {}
        links = []
        
        def get_node_index(name):
            if name not in node_indices:
                node_indices[name] = len(nodes_list)
                nodes_list.append({"name": name})
            return node_indices[name]
        
        for (source, target), count in transitions.items():
            if count > 2: # Filter out noise
                links.append({
                    'source': get_node_index(source),
                    'target': get_node_index(target),
                    'value': count
                })
            
        return {
            'nodes': nodes_list,
            'links': links
        }

    def get_relationship_network_data(self, tenant_id, start_date):
        """Get data for relationship network graph."""
        from django.db.models import Count
        from accounts.models import Account, Contact
        
        # Get accounts with engagement activity
        active_account_ids = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).values_list('account_id', flat=True).distinct()
        
        accounts = Account.objects.filter(tenant_id=tenant_id, id__in=active_account_ids)
        events = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).select_related('account', 'contact')
        
        nodes = []
        links = []
        node_ids = set()
        
        # Add account nodes
        for account in accounts:
            node_id = f"account_{account.id}"
            nodes.append({
                'id': node_id,
                'name': account.name,
                'type': 'account',
                'size': 25
            })
            node_ids.add(node_id)
            
        # Add contact nodes and links
        link_counts = {}
        for event in events:
            if event.contact and event.account:
                contact_node_id = f"contact_{event.contact.id}"
                account_node_id = f"account_{event.account.id}"
                
                # Add contact node if not exists
                if contact_node_id not in node_ids:
                    nodes.append({
                        'id': contact_node_id,
                        'name': f"{event.contact.first_name} {event.contact.last_name}",
                        'type': 'contact',
                        'size': 12
                    })
                    node_ids.add(contact_node_id)
                    
                # Track interaction strength
                link_key = (contact_node_id, account_node_id)
                link_counts[link_key] = link_counts.get(link_key, 0) + 1
        
        for (source, target), value in link_counts.items():
            links.append({
                'source': source,
                'target': target,
                'value': value
            })
                
        return {
            'nodes': nodes,
            'links': links
        }



    def calculate_trend(self, current, previous):
        """Calculate percentage trend."""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    def get_account_engagement_timeline(self, tenant_id, start_date):
        """Get account-specific engagement timeline data."""
        from accounts.models import Account
        from django.db.models import Avg
        
        # Get top 5 accounts by engagement score
        top_accounts = Account.objects.filter(tenant_id=tenant_id)[:5]
        
        timeline_data = []
        for account in top_accounts:
            # Get engagement events for this account over time
            events = EngagementEvent.objects.filter(
                account=account,
                tenant_id=tenant_id,
                created_at__gte=start_date
            ).extra(select={'date': 'date(created_at)'}).values('date').annotate(
                avg_score=Avg('engagement_score')
            ).order_by('date')
            
            timeline_data.append({
                'account_name': account.name,
                'data': list(events)
            })
            
        return timeline_data
    

    def get_contact_engagement_history(self, tenant_id, start_date):
        """Get contact-level engagement history data."""
        from accounts.models import Contact
        from django.db.models import Avg, Count
        
        # Get top 10 contacts by engagement activity
        top_contacts = Contact.objects.filter(
            account__tenant_id=tenant_id
        ).annotate(
            event_count=Count('engagementevent')
        ).filter(event_count__gt=0).order_by('-event_count')[:10]
        
        contact_data = []
        for contact in top_contacts:
            # Get engagement events for this contact
            events = EngagementEvent.objects.filter(
                contact=contact,
                tenant_id=tenant_id,
                created_at__gte=start_date
            ).aggregate(
                total_events=Count('id'),
                avg_score=Avg('engagement_score')
            )
            
            contact_data.append({
                'contact_name': f"{contact.first_name} {contact.last_name}",
                'account_name': contact.account.name if contact.account else "No Account",
                'total_events': events['total_events'] or 0,
                'avg_score': round(events['avg_score'] or 0, 2)
            })
            
        return contact_data
# ... existing code ...
    
    def get_opportunity_engagement_journey(self, tenant_id, start_date):
        """Get opportunity engagement journey data."""
        from opportunities.models import Opportunity
        from django.db.models import Avg, Count
        
        # Get opportunities with engagement events
        opportunities = Opportunity.objects.filter(
            tenant_id=tenant_id
        ).annotate(
            event_count=Count('engagement_events')
        ).filter(event_count__gt=0).order_by('-created_at')[:10]
        
        journey_data = []
        for opportunity in opportunities:
            # Get engagement events for this opportunity
            events = EngagementEvent.objects.filter(
                opportunity=opportunity,
                tenant_id=tenant_id,
                created_at__gte=start_date
            ).extra(select={'date': 'date(created_at)'}).values('date').annotate(
                avg_score=Avg('engagement_score'),
                count=Count('id')
            ).order_by('date')
            
            journey_data.append({
                'opportunity_name': opportunity.opportunity_name,
                'account_name': opportunity.account.name if opportunity.account else "No Account",
                'stage': opportunity.stage.opportunity_stage_name if opportunity.stage else "No Stage",
                'event_timeline': list(events)
            })
            
        return journey_data

    def get_engagement_comparison_data(self, tenant_id, start_date, days, now):
        """Get engagement comparison data (account vs account, period vs period)."""
        from accounts.models import Account
        from django.db.models import Avg, Count
        
        # Account vs Account comparison
        accounts_comparison = Account.objects.filter(
            tenant_id=tenant_id
        ).annotate(
            event_count=Count('contacts__engagementevent'),
            avg_score=Avg('contacts__engagementevent__engagement_score')
        ).filter(event_count__gt=0).order_by('-avg_score')[:10]
        
        # Period vs Period comparison (current vs previous period)
        prev_start = start_date - timedelta(days=days)
        current_period = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).aggregate(
            event_count=Count('id'),
            avg_score=Avg('engagement_score')
        )
        
        previous_period = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=prev_start,
            created_at__lt=start_date
        ).aggregate(
            event_count=Count('id'),
            avg_score=Avg('engagement_score')
        )
        
        return {
            'accounts_comparison': [
                {
                    'account_name': account.account_name,
                    'event_count': account.event_count,
                    'avg_score': round(account.avg_score or 0, 2)
                }
                for account in accounts_comparison
            ],
            'period_comparison': {
                'current': {
                    'event_count': current_period['event_count'] or 0,
                    'avg_score': round(current_period['avg_score'] or 0, 2)
                },
                'previous': {
                    'event_count': previous_period['event_count'] or 0,
                    'avg_score': round(previous_period['avg_score'] or 0, 2)
                },
                'current_timeline': self.get_period_timeline_data(tenant_id, start_date, now),
                'previous_timeline': self.get_period_timeline_data(tenant_id, prev_start, start_date)
            }
        }

    def get_period_timeline_data(self, tenant_id, start_date, end_date):
        """Get daily aggregation for a period for visual comparison."""
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        
        timeline = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date,
            created_at__lt=end_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return list(timeline)

    def get_engagement_heatmap_data(self, tenant_id, start_date):
        """Get 7x24 grid of engagement activity (Day of Week vs Hour)."""
        from django.db.models import Count
        from django.db.models.functions import ExtractWeekDay, ExtractHour
        
        heatmap_qs = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).annotate(
            weekday=ExtractWeekDay('created_at'),
            hour=ExtractHour('created_at')
        ).values('weekday', 'hour').annotate(
            count=Count('id')
        )
        
        # Initialize 7x24 grid with 0s
        # weekday: 1 (Sun) to 7 (Sat) according to Django ExtractWeekDay
        data = [[0 for _ in range(24)] for _ in range(7)]
        
        for entry in heatmap_qs:
            # Adjust weekday to 0-indexed (0=Sun, 6=Sat)
            w = entry['weekday'] - 1
            h = entry['hour']
            if 0 <= w < 7 and 0 <= h < 24:
                data[w][h] = entry['count']
            
        return data

    def get_geographic_engagement_data(self, tenant_id, start_date):
        """Get engagement count by country."""
        from django.db.models import Count
        
        geo_counts = {}
        
        try:
            # Engagement from Leads directly
            lead_data = EngagementEvent.objects.filter(
                tenant_id=tenant_id,
                created_at__gte=start_date,
                lead__isnull=False
            ).values('lead__country').annotate(
                count=Count('id')
            )
            
            for entry in lead_data:
                country = entry['lead__country']
                if country:
                    geo_counts[country] = geo_counts.get(country, 0) + entry['count']
        except Exception as e:
            logger.error(f"Error getting lead geographic data: {e}")

        try:
            # Note: Account model currently doesn't have a country field directly.
            # If countries are added to Account later, this can be updated.
            pass
        except Exception as e:
            logger.error(f"Error getting account geographic data: {e}")
            
        return [{'country': c, 'count': v} for c, v in geo_counts.items()]


class EngagementAccountBreakdownView(PermissionRequiredMixin, TemplateView):
    """
    Display detailed account breakdowns for engagement analytics.
    
    This view shows detailed engagement data broken down by accounts, contacts,
    and opportunities, separated from the main dashboard for better organization.
    """
    template_name = 'engagement/account_breakdowns.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        now = timezone.now()
        
        # Date range (default 30 days)
        days = int(self.request.GET.get('days', 30))
        start_date = now - timedelta(days=days)
        
        # Add all the detailed data that was previously in the dashboard
        dashboard_view = EngagementDashboardView()
        
        # Account-specific engagement timeline data
        context['account_timeline_data'] = dashboard_view.get_account_engagement_timeline(tenant_id, start_date)
        
        # Contact-level engagement history data
        context['contact_history_data'] = dashboard_view.get_contact_engagement_history(tenant_id, start_date)
        
        # Opportunity engagement journey data
        context['opportunity_journey_data'] = dashboard_view.get_opportunity_engagement_journey(tenant_id, start_date)
        
        # Engagement comparison data
        context['engagement_comparison_data'] = dashboard_view.get_engagement_comparison_data(tenant_id, start_date, days, now)
        
        # Engagement journey data
        context['engagement_journey_data'] = dashboard_view.get_engagement_journey_data(tenant_id, start_date)
        
        # Engagement flow data for Sankey diagram
        context['engagement_flow_data'] = dashboard_view.get_engagement_flow_data(tenant_id, start_date)
        
        # Relationship network data
        context['relationship_network_data'] = dashboard_view.get_relationship_network_data(tenant_id, start_date)
        
        return context


class EngagementEventDetailView(PermissionRequiredMixin, DetailView):
    model = EngagementEvent
    template_name = 'engagement/event_detail.html'
    context_object_name = 'event'
    required_permission = 'engagement:read'

class EngagementEventUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing engagement event.
    
    This view allows authorized users to edit engagement event details
    while maintaining data integrity and tenant isolation.
    """
    model = EngagementEvent
    form_class = EngagementEventForm
    template_name = 'engagement/event_form.html'
    context_object_name = 'event'
    permission_required = 'engagement.change_engagementevent'
    raise_exception = True  # Return 403 instead of redirecting to login

    def get_queryset(self):
        """Ensure users can only access events in their tenant."""
        qs = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            qs = qs.filter(tenant_id=self.request.user.tenant_id)
        return qs

    def get_form_kwargs(self):
        """Pass user to form for tenant-aware dropdowns."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Handle successful form submission."""
        # Preserve tenant_id if not set in form
        if not form.instance.tenant_id and hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
            
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f"Engagement event '{form.instance.title}' updated successfully!"
        )
        return response

    def get_success_url(self):
        """Redirect to event detail page after update."""
        return reverse_lazy('engagement:event_detail', kwargs={'pk': self.object.pk})

    def handle_no_permission(self):
        """Handle permission denied with user-friendly message."""
        messages.error(
            self.request, 
            "You don't have permission to edit this engagement event."
        )
        # Redirect to detail page or feed if user can at least view it
        if self.request.user.has_perm('engagement.view_engagementevent'):
            event_pk = self.kwargs.get('pk')
            if event_pk:
                return redirect('engagement:event_detail', pk=event_pk)
        return redirect('engagement:feed')



class NextBestActionListView(PermissionRequiredMixin, ListView):
    """
    Display paginated list of Next Best Actions with filtering capabilities.
    
    Features:
    - Multi-tenant isolation
    - Comprehensive filtering (completed, priority, action type, overdue, account)
    - Performance optimization with select_related
    - User-friendly pagination
    """
    model = NextBestAction
    template_name = 'engagement/next_best_action.html'
    context_object_name = 'actions'
    paginate_by = 25
    permission_required = 'engagement.view_nextbestaction'
    raise_exception = True

    def get_queryset(self):
        """
        Build filtered queryset with tenant isolation and performance optimization.
        
        Filters available:
        - show_completed: Show/hide completed actions (default: hide)
        - priority: Filter by priority level
        - action_type: Filter by action type
        - overdue: Show only overdue actions
        - account: Filter by specific account
        - search: Full-text search across description and account name
        """
        # Base queryset with tenant isolation and performance optimization
        queryset = NextBestAction.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).select_related(
            'account', 'opportunity', 'assigned_to', 'contact', 'engagement_event', 'lead'
        ).order_by('-due_date', 'priority')

        
       
        
        # Filter completed actions (default: hide completed)
        show_completed = self.request.GET.get('show_completed', 'false').lower() == 'true'
        if not show_completed:
            queryset = queryset.filter(completed=False)
        
        # Priority filter
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        # Action type filter
        action_type = self.request.GET.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
            
        # Overdue filter (only uncompleted overdue actions)
        overdue = self.request.GET.get('overdue')
        if overdue:
            queryset = queryset.filter(due_date__lt=timezone.now(), completed=False)
            
        # Account filter
        account_id = self.request.GET.get('account')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(account__name__icontains=search) |
                Q(opportunity__name__icontains=search) |
                Q(contact__first_name__icontains=search) |
                Q(contact__last_name__icontains=search)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        """
        Add filter options and current filter state to template context.
        
        Provides:
        - Priority and action type choices for filter dropdowns
       
        - Current filter values for active filter indicators
        - Account list for account filter dropdown
        - Search term for search input persistence
        """
        context = super().get_context_data(**kwargs)
        context['priority_choices'] = NextBestAction._meta.get_field('priority').choices
        context['action_types'] = NextBestAction._meta.get_field('action_type').choices
        context['show_completed'] = self.request.GET.get('show_completed', 'false').lower() == 'true'
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_action_type'] = self.request.GET.get('action_type', '')
        context['current_overdue'] = self.request.GET.get('overdue', '') == 'true'
        context['current_account'] = self.request.GET.get('account', '')
        context['current_search'] = self.request.GET.get('search', '')

       
        
        # Add accounts for account filter dropdown (limited to avoid performance issues)
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        context['accounts'] = Account.objects.filter(
            tenant_id=tenant_id
        ).order_by('account_name')[:100]  # Limit to 100 accounts
        
        # Smart Insight (Best Time to Engage)
        if context['current_account']:
            try:
                from .utils import get_best_engagement_time
                # Use the Account model that's already imported at the top of the file
                selected_account = Account.objects.get(id=context['current_account'])
                context['selected_account'] = selected_account
                context['best_time_to_engage'] = get_best_engagement_time(selected_account)
            except (Account.DoesNotExist, ValueError):
                pass
        
        return context


class NextBestActionDetailView(PermissionRequiredMixin, DetailView):
    """
    Display detailed view of a single Next Best Action.
    
    Features:
    - Tenant isolation
    - Permission checking
    - Related object prefetching for performance
    """
    model = NextBestAction
    template_name = 'engagement/next_best_action_detail.html'
    context_object_name = 'action'
    permission_required = 'engagement.view_nextbestaction'
    raise_exception = True

    def get_queryset(self):
        """Ensure tenant isolation and optimize related object loading."""
        return NextBestAction.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).select_related(
            'account', 'opportunity', 'assigned_to', 'contact', 'engagement_event'
        )


class NextBestActionCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new Next Best Action with proper defaults and validation.
    
    Features:
    - Automatic tenant assignment
    - Default assignment to current user
    - Default source as 'Manual Entry'
    - Success messaging
    - Proper redirect handling
    """
    model = NextBestAction
    form_class = NextBestActionForm
    template_name = 'engagement/next_best_action_form.html'
    permission_required = 'engagement.add_nextbestaction'
    raise_exception = True

    def get_success_url(self):
        """Redirect to NBA detail page after creation for better user experience."""
        return reverse_lazy('engagement:next_best_action_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        """Pass current user to form for tenant-aware dropdowns."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        Set tenant_id, assigned_to, and source before saving.
        
        Also creates an engagement event to track the creation of this action.
        """
        with transaction.atomic():
            # Set required fields
            form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
            form.instance.assigned_to = self.request.user
            if not form.instance.source:
                form.instance.source = 'Manual Entry'
            form.instance.status = 'open'  # Default status
            
            response = super().form_valid(form)
            
            # Create engagement event for action creation
            try:
                EngagementEvent.objects.create(
                    event_type='next_best_action_created',
                    title=f'Next Best Action Created: {self.object.get_action_type_display()}',
                    description=f'Next best action "{self.object.description}" was created by {self.request.user.email}',
                    account=self.object.account,
                    opportunity=self.object.opportunity,
                    contact=self.object.contact,
                    created_by=self.request.user,
                    tenant_id=self.object.tenant_id,
                    priority=self.object.priority,
                    engagement_score=15.0,  # Lower score for creation vs completion
                    is_important=False,
                    source='Manual Creation'
                )
            except Exception as e:
                # Log error but don't fail the main action creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create engagement event for NBA creation: {e}")
            
            messages.success(
                self.request, 
                f"Next best action '{self.object.get_action_type_display()}' created successfully!"
            )
            return response

    def form_invalid(self, form):
        """Add error messaging for form validation failures."""
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class NextBestActionUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing Next Best Action with validation and logging.
    
    Features:
    - Tenant isolation
    - Permission checking
    - Success messaging
    - Proper redirect handling
    """
    model = NextBestAction
    form_class = NextBestActionForm
    template_name = 'engagement/next_best_action_form.html'
    permission_required = 'engagement.change_nextbestaction'
    raise_exception = True

    def get_queryset(self):
        """Ensure tenant isolation."""
        return NextBestAction.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )

    def get_form_kwargs(self):
        """Pass current user to form for tenant-aware dropdowns."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        """Redirect to NBA detail page after update."""
        return reverse_lazy('engagement:next_best_action_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        """Add success messaging and handle updates."""
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f"Next best action '{self.object.get_action_type_display()}' updated successfully!"
        )
        return response

    def form_invalid(self, form):
        """Add error messaging for form validation failures."""
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class NextBestActionDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete a Next Best Action with confirmation and logging.
    
    Features:
    - Tenant isolation
    - Permission checking
    - Success messaging
    - Safe deletion with confirmation
    """
    model = NextBestAction
    template_name = 'engagement/next_best_action_confirm_delete.html'
    permission_required = 'engagement.delete_nextbestaction'
    raise_exception = True

    def get_queryset(self):
        """Ensure tenant isolation."""
        return NextBestAction.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )

    def get_success_url(self):
        """Redirect to NBA list after deletion."""
        return reverse_lazy('engagement:next_best_action')

    def delete(self, request, *args, **kwargs):
        """Add success messaging and create engagement event for deletion."""
        action = self.get_object()
        
        with transaction.atomic():
            response = super().delete(request, *args, **kwargs)
            
            # Create engagement event for action deletion
            try:
                EngagementEvent.objects.create(
                    event_type='next_best_action_deleted',
                    title=f'Next Best Action Deleted: {action.get_action_type_display()}',
                    description=f'Next best action "{action.description}" was deleted by {request.user.email}',
                    account=action.account,
                    opportunity=action.opportunity,
                    contact=action.contact,
                    created_by=request.user,
                    tenant_id=action.tenant_id,
                    priority=action.priority,
                    engagement_score=5.0,  # Very low score for deletion
                    is_important=False,
                    source='Manual Deletion'
                )
            except Exception as e:
                # Log error but don't fail the main deletion
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create engagement event for NBA deletion: {e}")
            
            messages.success(
                request, 
                f"Next best action '{action.get_action_type_display()}' deleted successfully!"
            )
            return response

logger = logging.getLogger(__name__)
class CompleteNextBestActionView(PermissionRequiredMixin, View):
    """
    Unified endpoint to complete a Next Best Action with comprehensive features.
    
    This single view handles all completion scenarios:
    - Basic completion (AJAX or form POST)
    - Completion with notes
    - Engagement event creation
    - Proper error handling and logging
    - Tenant isolation and permission checking
    
    Supports both JSON (AJAX) and form-encoded (traditional POST) requests.
    """
    permission_required = 'engagement.change_nextbestaction'
    raise_exception = True

    def post(self, request):
        """
        Handle completion request from any client (AJAX, form, API).
        
        Accepts multiple input formats:
        1. JSON payload: {"action_id": 123, "completion_note": "optional note"}
        2. Form data: action_id=123&completion_note=optional+note
        
        Returns:
        - JSON response for AJAX requests
        - Redirect for traditional form submissions 
        """
        try:
            # Parse request data based on content type
            action_id, completion_note = self._parse_request_data(request)
            
            # Validate required fields
            if not action_id:
                return self._handle_error('Action ID is required', 400, request)
            
            # Get action with tenant isolation
            action = get_object_or_404(
                NextBestAction,
                id=action_id,
                tenant_id=getattr(request.user, 'tenant_id', None)
            )
            
            # Permission check: assigned user or global permission
            if action.assigned_to != request.user and not request.user.has_perm('engagement.change_nextbestaction'):
                return self._handle_error('Permission denied', 403, request)
            
            # Prevent duplicate completion
            if action.completed:
                return self._handle_error('Action is already completed', 400, request)
            
            # Complete the action with atomic transaction
            completion_result = self._complete_action(action, completion_note, request.user)
            
            # Handle response based on request type
            return self._handle_success(completion_result, request)
            
        except json.JSONDecodeError:
            return self._handle_error('Invalid JSON payload', 400, request)
        except NextBestAction.DoesNotExist:
            return self._handle_error('Action not found', 404, request)
        except Exception as e:
            logger.error(f"Error completing next best action: {e}", exc_info=True)
            return self._handle_error('An unexpected error occurred', 500, request)

    def _parse_request_data(self, request):
        """Parse action_id and completion_note from request data."""
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            action_id = data.get('action_id')
            completion_note = data.get('completion_note', '').strip()
        else:
            # Handle form-encoded data
            action_id = request.POST.get('action_id') or request.POST.get('pk')
            completion_note = request.POST.get('completion_note', '').strip()
        
        return action_id, completion_note

    def _complete_action(self, action, completion_note, user):
        """Complete the action with all side effects in atomic transaction."""
        with transaction.atomic():
            # Update action status
            action.completed = True
            action.completed_at = timezone.now()
            action.status = 'resolved'
            update_fields = ['completed', 'completed_at', 'status']
            
            # Add completion note if provided
            if completion_note:
                action.description += f"\n\n--- Completion Note ({timezone.now().strftime('%Y-%m-%d %H:%M')}) ---\n{completion_note}"
                update_fields.append('description')
            
            action.save(update_fields=update_fields)
            
            # Create engagement event
            engagement_event = EngagementEvent.objects.create(
                event_type='next_best_action_completed',
                title=f'Next Best Action Completed: {action.get_action_type_display()}',
                description=f'Next best action "{action.description.split("---")[0].strip()}" was completed by {user.email}',
                account=action.account,
                opportunity=action.opportunity,
                contact=action.contact,
                created_by=user,
                tenant_id=action.tenant_id,
                priority=action.priority,
                engagement_score=25.0,
                is_important=False,
                source='Action Completion'
            )
            
            # Link engagement event to action
            action.engagement_event = engagement_event
            action.save(update_fields=['engagement_event'])
            
            return {
                'action_id': action.id,
                'redirect_url': reverse_lazy('engagement:next_best_action_detail', kwargs={'pk': action.id})
            }

    def _handle_success(self, result, request):
        """Handle successful completion with appropriate response."""
        if self._is_ajax_request(request):
            return JsonResponse({
                'success': True,
                'message': 'Next best action completed successfully!',
                'redirect_url': str(result['redirect_url'])
            })
        else:
            from django.contrib import messages
            messages.success(request, 'Next best action completed successfully!')
            return self._redirect_to_success_url(result['action_id'])

    def _handle_error(self, message, status_code, request):
        """Handle errors with appropriate response format."""
        if self._is_ajax_request(request):
            return JsonResponse({'error': message}, status=status_code)
        else:
            from django.contrib import messages
            messages.error(request, message)
            # Redirect back to action detail or list
            if 'pk' in request.POST:
                from django.shortcuts import redirect
                return redirect('engagement:next_best_action_detail', pk=request.POST['pk'])
            else:
                from django.shortcuts import redirect
                return redirect('engagement:next_best_action')

    def _is_ajax_request(self, request):
        """Check if request is AJAX (works with fetch and jQuery)."""
        return request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               request.content_type == 'application/json'

    def _redirect_to_success_url(self, action_id):
        """Redirect to appropriate success URL."""
        from django.shortcuts import redirect
        return redirect('engagement:next_best_action_detail', pk=action_id)
@permission_required('engagement.change_nextbestaction', raise_exception=True)
def start_next_best_action_view(request, pk):
    action = get_object_or_404(NextBestAction, pk=pk, tenant_id=getattr(request.user, 'tenant_id', None))
    if action.status != 'in_progress':
        action.status = 'in_progress'
        action.save(update_fields=['status'])
        messages.success(request, f"Action '{action.get_action_type_display()}' marked as in progress!")
    return redirect('engagement:next_best_action_detail', pk=pk)

@permission_required('engagement.change_nextbestaction', raise_exception=True)
def complete_next_best_action_with_note_view(request, pk):
    action = get_object_or_404(NextBestAction, pk=pk, tenant_id=getattr(request.user, 'tenant_id', None))
    if request.method == 'POST' and not action.completed:
        completion_note = request.POST.get('completion_note', '').strip()
        action.completed = True
        action.completed_at = timezone.now()
        action.status = 'resolved'
        if completion_note:
            action.description += f"\n\n--- Completion Note ({timezone.now().strftime('%Y-%m-%d %H:%M')}) ---\n{completion_note}"
        action.save(update_fields=['completed', 'completed_at', 'status', 'description'])
        messages.success(request, f"Action '{action.get_action_type_display()}' completed with note!")
        return redirect('engagement:next_best_action_detail', pk=pk)


class DisengagedAccountsView(PermissionRequiredMixin, ListView):
    """
    Report view for accounts with low engagement or inactivity.
    """
    model = EngagementStatus
    template_name = 'engagement/disengaged_accounts.html'
    context_object_name = 'statuses'
    paginate_by = 50
    required_permission = 'engagement:read'
    
    def get_queryset(self):
        # Default thresholds
        score_threshold = float(self.request.GET.get('score_threshold', 30.0))
        days_inactive = int(self.request.GET.get('days_inactive', 14))
        
        inactive_date = timezone.now() - timedelta(days=days_inactive)
        
        # Base Query
        qs = EngagementStatus.objects.select_related('account').filter(
            account__tenant_id=getattr(self.request.user, 'tenant_id', None)
        )
        
        # Filter Logic: Either Low Score OR Inactive
        # User can toggle mode via GET param 'mode' (optional, defaulting to combined logic)
        
        qs = qs.filter(
            Q(engagement_score__lt=score_threshold) |
            Q(last_engaged_at__lt=inactive_date) | 
            Q(last_engaged_at__isnull=True)
        ).order_by('engagement_score', 'last_engaged_at')
        
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['score_threshold'] = self.request.GET.get('score_threshold', 30)
        context['days_inactive'] = self.request.GET.get('days_inactive', 14)
        
        # Add statistics for the report
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Total accounts
        total_accounts = EngagementStatus.objects.filter(
            account__tenant_id=tenant_id
        ).count()
        
        # Disengaged accounts count (using current filter criteria)
        disengaged_count = self.get_queryset().count()
        
        # Calculate percentages
        disengaged_percentage = (disengaged_count / total_accounts * 100) if total_accounts > 0 else 0
        
        context['total_accounts'] = total_accounts
        context['disengaged_count'] = disengaged_count
        context['disengaged_percentage'] = round(disengaged_percentage, 1)
        
        # Add export options
        context['export_formats'] = ['csv', 'excel', 'pdf']
        
        return context




class DisengagedAccountsExportView(PermissionRequiredMixin, View):
    """
    Export disengaged accounts report in various formats.
    """
    required_permission = 'engagement:read'
    
    def get(self, request, format):
        # Get the same queryset as the main report
        view = DisengagedAccountsView()
        view.request = request
        queryset = view.get_queryset()
        
        tenant_id = getattr(request.user, 'tenant_id', None)
        
        if format == 'csv':
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="disengaged_accounts.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Account Name', 'Email', 'Last Engaged', 'Days Since Last Engagement', 
                'Engagement Score', 'Status'
            ])
            
            for status in queryset:
                days_since_last_engaged = (
                    (timezone.now() - status.last_engaged_at).days 
                    if status.last_engaged_at else 'Never'
                )
                
                writer.writerow([
                    status.account.name,
                    status.account.email,
                    status.last_engaged_at.strftime('%Y-%m-%d %H:%M') if status.last_engaged_at else 'Never',
                    days_since_last_engaged,
                    status.engagement_score,
                    'Low Score' if status.engagement_score < float(request.GET.get('score_threshold', 30)) else 'Inactive'
                ])
            
            return response
            
        # Other formats could be implemented similarly
        else:
            from django.http import HttpResponse
            return HttpResponse(f"Export format '{format}' not yet implemented", status=501)


class TopEngagedAccountsView(PermissionRequiredMixin, ListView):
    """
    Report view for accounts with highest engagement scores.
    """
    model = EngagementStatus
    template_name = 'engagement/top_engaged_accounts.html'
    context_object_name = 'statuses'
    paginate_by = 50
    required_permission = 'engagement:read'
    
    def get_queryset(self):
        # Number of top accounts to show
        limit = int(self.request.GET.get('limit', 50))
        
        # Base Query
        qs = EngagementStatus.objects.select_related('account').filter(
            account__tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).order_by('-engagement_score')
        
        return qs[:limit]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['limit'] = self.request.GET.get('limit', 50)
        
        # Add statistics for the report
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Total accounts
        total_accounts = EngagementStatus.objects.filter(
            account__tenant_id=tenant_id
        ).count()
        
        # Top engaged accounts count (using current limit)
        top_engaged_count = self.get_queryset().count()
        
        context['total_accounts'] = total_accounts
        context['top_engaged_count'] = top_engaged_count
        
        # Add export options
        context['export_formats'] = ['csv', 'excel', 'pdf']
        
        return context


class TopEngagedAccountsExportView(PermissionRequiredMixin, View):
    """
    Export top engaged accounts report in various formats.
    """
    required_permission = 'engagement:read'
    
    def get(self, request, format):
        # Get the same queryset as the main report
        view = TopEngagedAccountsView()
        view.request = request
        queryset = view.get_queryset()
        
        if format == 'csv':
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="top_engaged_accounts.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Account Name', 'Email', 'Last Engaged', 'Engagement Score'
            ])
            
            for status in queryset:
                writer.writerow([
                    status.account.name,
                    status.account.email,
                    status.last_engaged_at.strftime('%Y-%m-%d %H:%M') if status.last_engaged_at else 'Never',
                    status.engagement_score
                ])
            
            return response
            
        # Other formats could be implemented similarly
        else:
            from django.http import HttpResponse
            return HttpResponse(f"Export format '{format}' not yet implemented", status=501)


# Playbook Views


class EngagementPlaybookListView(PermissionRequiredMixin, ListView):
    model = EngagementPlaybook
    template_name = 'engagement/playbook_list.html'
    context_object_name = 'playbooks'
    required_permission = 'engagement:read'

    def get_queryset(self):
        queryset = EngagementPlaybook.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).order_by('name')
        
        # Filter by industry if specified
        industry = self.request.GET.get('industry')
        if industry:
            queryset = queryset.filter(industry=industry)
            
        # Filter by type if specified
        playbook_type = self.request.GET.get('playbook_type')
        if playbook_type:
            queryset = queryset.filter(playbook_type=playbook_type)
            
        # Filter by template status if specified
        is_template = self.request.GET.get('is_template')
        if is_template:
            queryset = queryset.filter(is_template=is_template.lower() == 'true')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['industries'] = EngagementPlaybook.INDUSTRY_CHOICES
        context['playbook_types'] = EngagementPlaybook.PLAYBOOK_TYPES
        context['current_industry'] = self.request.GET.get('industry', '')
        context['current_type'] = self.request.GET.get('playbook_type', '')
        context['current_template'] = self.request.GET.get('is_template', '')
        return context


class EngagementPlaybookDetailView(PermissionRequiredMixin, DetailView):
    model = EngagementPlaybook
    template_name = 'engagement/playbook_detail.html'
    context_object_name = 'playbook'
    required_permission = 'engagement:read'

    def get_queryset(self):
        return EngagementPlaybook.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add execution statistics
        context['total_executions'] = self.object.executions.count()
        context['completed_executions'] = self.object.executions.filter(status='completed').count()
        context['steps'] = self.object.steps.all()
        return context




class EngagementPlaybookCreateView(PermissionRequiredMixin, CreateView):
    model = EngagementPlaybook
    form_class = EngagementPlaybookForm
    template_name = 'engagement/playbook_form.html'
    permission_required = 'engagement.add_engagementplaybook'
    raise_exception = True
    success_url = reverse_lazy('engagement:playbook_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        messages.success(self.request, f"Playbook '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class EngagementPlaybookUpdateView(PermissionRequiredMixin, UpdateView):
    model = EngagementPlaybook
    form_class = EngagementPlaybookForm
    template_name = 'engagement/playbook_form.html'
    permission_required = 'engagement.change_engagementplaybook'
    raise_exception = True
    success_url = reverse_lazy('engagement:playbook_list')

    def get_queryset(self):
        return EngagementPlaybook.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )

    def form_valid(self, form):
        messages.success(self.request, f"Playbook '{form.instance.name}' updated successfully!")
        return super().form_valid(form)


class PlaybookStepCreateView(PermissionRequiredMixin, CreateView):
    model = PlaybookStep
    form_class = PlaybookStepForm
    template_name = 'engagement/playbook_step_form.html'
    permission_required = 'engagement.add_playbookstep'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.playbook = get_object_or_404(
            EngagementPlaybook, 
            pk=kwargs['playbook_id'],
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['playbook'] = self.playbook
        return context

    def form_valid(self, form):
        form.instance.playbook = self.playbook
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        messages.success(self.request, "Step added successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engagement:playbook_detail', kwargs={'pk': self.playbook.pk})


class PlaybookStepUpdateView(PermissionRequiredMixin, UpdateView):
    model = PlaybookStep
    form_class = PlaybookStepForm
    template_name = 'engagement/playbook_step_form.html'
    permission_required = 'engagement.change_playbookstep'
    raise_exception = True

    def get_queryset(self):
        return PlaybookStep.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )

    def get_success_url(self):
        return reverse_lazy('engagement:playbook_detail', kwargs={'pk': self.object.playbook.pk})
    
    def form_valid(self, form):
        messages.success(self.request, "Step updated successfully!")
        return super().form_valid(form)


class PlaybookStepDeleteView(PermissionRequiredMixin, DeleteView):
    model = PlaybookStep
    template_name = 'engagement/playbook_step_confirm_delete.html'
    permission_required = 'engagement.delete_playbookstep'
    raise_exception = True

    def get_queryset(self):
        return PlaybookStep.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )

    def get_success_url(self):
        messages.success(self.request, "Step deleted successfully!")
        return reverse_lazy('engagement:playbook_detail', kwargs={'pk': self.object.playbook.pk})


class PlaybookExecutionStartView(PermissionRequiredMixin, CreateView):
    """
    Start executing a playbook for a specific account.
    """
    model = PlaybookExecution
    template_name = 'engagement/playbook_execution_start.html'
    fields = ['account', 'notes']
    permission_required = 'engagement.add_playbookexecution'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.playbook = get_object_or_404(
            EngagementPlaybook,
            pk=kwargs['pk'],
            tenant_id=getattr(self.request.user, 'tenant_id', None),
            is_active=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['playbook'] = self.playbook
        # Filter accounts by tenant
        context['accounts'] = Account.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).order_by('name')
        return context

    def form_valid(self, form):
        form.instance.playbook = self.playbook
        form.instance.started_by = self.request.user
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        form.instance.status = 'in_progress'
        
        response = super().form_valid(form)
        
        # Create step executions for each step in the playbook
        for step in self.playbook.steps.all():
            PlaybookStepExecution.objects.create(
                execution=self.object,
                step=step,
                tenant_id=form.instance.tenant_id
            )
        
        # Update playbook usage metrics
        self.playbook.increment_usage()
        
        messages.success(
            self.request, 
            f"Started executing playbook '{self.playbook.name}' for {form.instance.account.name}"
        )
        return response

    def get_success_url(self):
        return reverse_lazy('engagement:playbook_execution_detail', kwargs={'pk': self.object.pk})


class PlaybookExecutionDetailView(PermissionRequiredMixin, DetailView):
    """
    View details of a playbook execution.
    """
    model = PlaybookExecution
    template_name = 'engagement/playbook_execution_detail.html'
    context_object_name = 'execution'
    permission_required = 'engagement.view_playbookexecution'
    raise_exception = True

    def get_queryset(self):
        return PlaybookExecution.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).select_related('playbook', 'account', 'started_by')


class PlaybookExecutionCompleteView(PermissionRequiredMixin, UpdateView):
    """
    Complete a playbook execution and update metrics.
    """
    model = PlaybookExecution
    template_name = 'engagement/playbook_execution_complete.html'
    fields = ['completion_rate', 'effectiveness_score', 'notes']
    permission_required = 'engagement.change_playbookexecution'
    raise_exception = True

    def form_valid(self, form):
        form.instance.status = 'completed'
        form.instance.completed_at = timezone.now()
        
        response = super().form_valid(form)
        
        # Update playbook metrics
        form.instance.update_playbook_metrics()
        
        messages.success(
            self.request, 
            f"Completed execution of playbook '{form.instance.playbook.name}' for {form.instance.account.name}"
        )
        return response

    def get_success_url(self):
        return reverse_lazy('engagement:playbook_execution_detail', kwargs={'pk': self.object.pk})


class PlaybookCloneView(PermissionRequiredMixin, CreateView):
    """
    Clone a playbook template to create a new playbook instance.
    """
    model = EngagementPlaybook
    template_name = 'engagement/playbook_clone.html'
    fields = ['name', 'description']
    permission_required = 'engagement.add_engagementplaybook'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.template_playbook = get_object_or_404(
            EngagementPlaybook,
            pk=kwargs['pk'],
            tenant_id=getattr(self.request.user, 'tenant_id', None),
            is_template=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_playbook'] = self.template_playbook
        return context

    def form_valid(self, form):
        # Create new playbook based on template
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        form.instance.created_by = self.request.user
        form.instance.industry = self.template_playbook.industry
        form.instance.playbook_type = 'standard'  # Cloned playbooks are not templates
        form.instance.is_template = False
        
        response = super().form_valid(form)
        
        # Clone all steps from template
        for step in self.template_playbook.steps.all():
            PlaybookStep.objects.create(
                playbook=self.object,
                day_offset=step.day_offset,
                action_type=step.action_type,
                description=step.description,
                priority=step.priority,
                tenant_id=step.tenant_id
            )
        
        messages.success(
            self.request, 
            f"Successfully cloned playbook '{self.template_playbook.name}' as '{self.object.name}'"
        )
        return response

    def get_success_url(self):
        return reverse_lazy('engagement:playbook_detail', kwargs={'pk': self.object.pk})


# ... existing code ...

class EngagementWorkflowListView(PermissionRequiredMixin, ListView):
    """
    List all engagement workflows with filtering capabilities.
    """
    model = EngagementWorkflow
    template_name = 'engagement/workflow_list.html'
    context_object_name = 'workflows'
    required_permission = 'engagement:read'

    def get_queryset(self):
        queryset = EngagementWorkflow.objects.filter(
            tenant_ptr_id=getattr(self.request.user, 'tenant_id', None)
        ).order_by('workflow_name')
        return queryset



class EngagementWorkflowCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new engagement workflow.
    """
    model = EngagementWorkflow
    form_class = EngagementWorkflowForm
    template_name = 'engagement/workflow_form.html'
    required_permission = 'engagement:add_engagementworkflow'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.tenant_ptr_id = getattr(self.request.user, 'tenant_id', None)
        messages.success(self.request, f"Workflow '{form.instance.workflow_name}' created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engagement:workflow_list')


class EngagementWorkflowUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing engagement workflow.
    """
    model = EngagementWorkflow
    form_class = EngagementWorkflowForm
    template_name = 'engagement/workflow_form.html'
    required_permission = 'engagement:change_engagementworkflow'

    def form_valid(self, form):
        messages.success(self.request, f"Workflow '{form.instance.workflow_name}' updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('engagement:workflow_list')




class EngagementWorkflowDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete an engagement workflow.
    """
    model = EngagementWorkflow
    template_name = 'engagement/workflow_confirm_delete.html'
    required_permission = 'engagement:delete_engagementworkflow'

    def delete(self, request, *args, **kwargs):
        workflow = self.get_object()
        messages.success(request, f"Workflow '{workflow.workflow_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('engagement:workflow_list')



class AttributionReportView(PermissionRequiredMixin, TemplateView):
    """
    Display attribution reports for campaigns and sources.
    """
    template_name = 'engagement/attribution_report.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        now = timezone.now()
        
        # Date range (default 30 days)
        days = int(self.request.GET.get('days', 30))
        start_date = now - timedelta(days=days)
        
        # Get events with attribution data
        events = EngagementEvent.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        ).exclude(
            utm_source__isnull=True, 
            utm_medium__isnull=True,
            utm_campaign__isnull=True,
            referring_domain__isnull=True
        ).exclude(
            utm_source='', 
            utm_medium='',
            utm_campaign='',
            referring_domain=''
        )
        
        # Group by UTM source
        from django.db.models import Count, Sum
        source_data = events.values('utm_source').annotate(
            event_count=Count('id'),
            total_score=Sum('engagement_score')
        ).order_by('-event_count')
        
        # Group by campaign
        campaign_data = events.values('utm_campaign').annotate(
            event_count=Count('id'),
            total_score=Sum('engagement_score')
        ).order_by('-event_count')
        
        # Group by referring domain
        domain_data = events.values('referring_domain').annotate(
            event_count=Count('id'),
            total_score=Sum('engagement_score')
        ).order_by('-event_count')
        
        context.update({
            'source_data': source_data,
            'campaign_data': campaign_data,
            'domain_data': domain_data,
            'days': days,
        })
        
        return context


class EngagementEventCommentCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a comment on an engagement event with mention support.
    """
    model = EngagementEventComment
    fields = ['content']
    template_name = 'engagement/event_comment_form.html'
    permission_required = 'engagement.add_engagementeventcomment'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(
            EngagementEvent,
            pk=self.kwargs['event_pk'],
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.engagement_event = self.event
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Process mentions in content
        content = form.cleaned_data['content']
        mentioned_users = self.extract_mentions(content)
        response = super().form_valid(form)
        
        # Add mentions
        form.instance.mentions.set(mentioned_users)
        
        # Send notifications to mentioned users
        self.notify_mentioned_users(form.instance, mentioned_users)
        
        messages.success(self.request, "Comment added successfully!")
        return response

    def extract_mentions(self, content):
        """
        Extract mentioned users from content (looking for @username patterns).
        """
        import re
        from core.models import User
        
        # Find all @mentions in the content
        mentions = re.findall(r'@(\w+)', content)
        mentioned_users = []
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Look up users by username
        for username in mentions:
            try:
                user = User.objects.get(username=username, tenant_id=tenant_id)
                mentioned_users.append(user)
            except User.DoesNotExist:
                pass  # Skip invalid mentions
                
        return mentioned_users

    def notify_mentioned_users(self, comment, mentioned_users):
        """
        Send notifications to mentioned users.
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        event_url = self.request.build_absolute_uri(
            reverse_lazy('engagement:event_detail', kwargs={'pk': self.event.pk})
        )
        
        for user in mentioned_users:
            if user.email:
                try:
                    send_mail(
                        subject=f"You were mentioned in a comment on engagement event",
                        message=f"{comment.author.get_full_name()} mentioned you in a comment on engagement event: {self.event.title}\n\n"
                                f"Comment: {comment.content}\n\n"
                                f"View the event: {event_url}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    # Log error but don't fail the comment creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send mention notification: {e}")

    def get_success_url(self):
        return reverse_lazy('engagement:event_detail', kwargs={'pk': self.event.pk})


class NextBestActionCommentCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a comment on a Next Best Action with mention support.
    """
    model = NextBestActionComment
    fields = ['content']
    template_name = 'engagement/nba_comment_form.html'
    permission_required = 'engagement.add_nextbestactioncomment'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        self.nba = get_object_or_404(
            NextBestAction,
            pk=self.kwargs['nba_pk'],
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.next_best_action = self.nba
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Process mentions in content
        content = form.cleaned_data['content']
        mentioned_users = self.extract_mentions(content)
        response = super().form_valid(form)
        
        # Add mentions
        form.instance.mentions.set(mentioned_users)
        
        # Send notifications to mentioned users
        self.notify_mentioned_users(form.instance, mentioned_users)
        
        messages.success(self.request, "Comment added successfully!")
        return response

    def extract_mentions(self, content):
        """
        Extract mentioned users from content (looking for @username patterns).
        """
        import re
        from core.models import User
        
        # Find all @mentions in the content
        mentions = re.findall(r'@(\w+)', content)
        mentioned_users = []
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Look up users by username
        for username in mentions:
            try:
                user = User.objects.get(username=username, tenant_id=tenant_id)
                mentioned_users.append(user)
            except User.DoesNotExist:
                pass  # Skip invalid mentions
                
        return mentioned_users

    def notify_mentioned_users(self, comment, mentioned_users):
        """
        Send notifications to mentioned users.
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        nba_url = self.request.build_absolute_uri(
            reverse_lazy('engagement:next_best_action_detail', kwargs={'pk': self.nba.pk})
        )
        
        for user in mentioned_users:
            if user.email:
                try:
                    send_mail(
                        subject=f"You were mentioned in a comment on Next Best Action",
                        message=f"{comment.author.get_full_name()} mentioned you in a comment on Next Best Action: {self.nba.get_action_type_display()}\n\n"
                                f"Comment: {comment.content}\n\n"
                                f"View the NBA: {nba_url}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    # Log error but don't fail the comment creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send mention notification: {e}")

    def get_success_url(self):
        return reverse_lazy('engagement:next_best_action_detail', kwargs={'pk': self.nba.pk})

def validate_hmac_signature(request, secret_key, signature_header='X-SalesCompass-Signature'):
    """
    Validate HMAC signature for incoming webhook requests.
    """
    import hmac
    import hashlib
    
    # Get signature from header
    signature = request.META.get(f'HTTP_{signature_header.upper().replace("-", "_")}')
    if not signature:
        return False
    
    # Get request body
    body = request.body
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures using hmac.compare_digest for security
    return hmac.compare_digest(signature, expected_signature)


@method_decorator(csrf_exempt, name='dispatch')
class IncomingWebhookView(View):
    """
    Handle incoming webhooks with HMAC signature verification.
    """
    
    def post(self, request, webhook_id):
        import json
        from .models import EngagementWebhook, EngagementEvent
        
        try:
            # Get webhook
            webhook = EngagementWebhook.objects.get(id=webhook_id, engagement_webhook_is_active=True)
        except EngagementWebhook.DoesNotExist:
            return JsonResponse({'error': 'Webhook not found or inactive'}, status=404)
        
        # Validate HMAC signature if secret key is configured
        if webhook.secret_key:
            signature_header = webhook.headers.get('signature_header', 'X-SalesCompass-Signature')
            if not validate_hmac_signature(request, webhook.secret_key, signature_header):
                return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        try:
            # Parse JSON payload
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        # Process the webhook payload
        try:
            # Extract event data from payload
            event_type = payload.get('event_type', 'external_webhook_received')
            title = payload.get('title', 'External Webhook Event')
            description = payload.get('description', '')
            engagement_score = float(payload.get('score', 50.0))
            account_id = payload.get('account_id')
            priority = payload.get('priority', 'medium')
            
            # Validate account_id
            if not account_id:
                return JsonResponse({'error': 'Missing account_id'}, status=400)
            
            # Create engagement event
            event = EngagementEvent.objects.create(
                account_id=account_id,
                event_type=event_type,
                title=title,
                description=description,
                engagement_score=engagement_score,
                priority=priority,
                tenant_id=webhook.tenant_id,
            )
            
            # Log successful processing
            WebhookDeliveryLog.objects.create(
                webhook=webhook,
                event=event,
                payload=payload,
                success=True,
                status_code=200,
                response_body='Event created successfully',
                tenant_id=webhook.tenant_id
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Webhook processed successfully',
                'event_id': event.id
            })
            
        except Exception as e:
            # Log error
            WebhookDeliveryLog.objects.create(
                webhook=webhook,
                payload=payload,
                success=False,
                error_message=str(e),
                tenant_id=webhook.tenant_id
            )
            
            return JsonResponse({'error': f'Error processing webhook: {str(e)}'}, status=500)

class EngagementMergeView(PermissionRequiredMixin, View):
    """
    View for merging duplicate engagement events.
    Expected POST params: primary_id (int), secondary_ids (list of ints)
    """
    required_permission = 'engagement:update'

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            primary_id = data.get('primary_id')
            secondary_ids = data.get('secondary_ids', [])
            
            if not primary_id or not secondary_ids:
                return JsonResponse({'status': 'error', 'message': 'Missing IDs'}, status=400)
                
            primary_event = get_object_or_404(EngagementEvent, pk=primary_id, tenant_id=request.user.tenant_id)
            secondary_events = EngagementEvent.objects.filter(pk__in=secondary_ids, tenant_id=request.user.tenant_id)
            
            merged_event = EventMergingService.merge_events(primary_event, secondary_events)
            
            return JsonResponse({
                'status': 'success',
                'merged_id': merged_event.id,
                'message': f'Successfully merged {secondary_events.count()} events.'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class EngagementDataQualityView(PermissionRequiredMixin, TemplateView):
    """
    Dashboard for monitoring engagement data quality metrics.
    """
    template_name = 'engagement/data_quality.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = self.request.user.tenant_id
        
        # 1. Total Events
        context['total_count'] = EngagementEvent.objects.filter(tenant_id=tenant_id).count()
        
        # 2. Potential Duplicates (Naive count)
        # This is expensive, so in production we'd use a summary table
        context['potential_duplicates'] = 0  # Placeholder for complex query
        
        # 3. Invalid Scores (outside 0-100)
        context['invalid_scores'] = EngagementEvent.objects.filter(
            Q(engagement_score__lt=0) | Q(engagement_score__gt=100),
            tenant_id=tenant_id
        ).count()
        
        # 4. Orphaned Events (no entity linkage - though model validaton now prevents this)
        context['orphaned_events'] = EngagementEvent.objects.filter(
            account_company__isnull=True,
            lead__isnull=True,
            contact__isnull=True,
            tenant_id=tenant_id
        ).count()
        
        # 5. Recent Cleanup Actions
        context['recent_logs'] = WebhookDeliveryLog.objects.filter(tenant_id=tenant_id)[:10]
        
        return context
