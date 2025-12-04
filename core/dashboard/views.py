from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.urls import reverse_lazy
from tasks.models import Task
from leads.models import Lead
from accounts.models import Account
from cases.models import Case
from sales.models import Sale
from opportunities.models import Opportunity
from core.models import User
from datetime import timedelta
import json

class RevenueDashboardRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect to billing revenue overview dashboard"""
    pattern_name = 'billing:revenue_overview'
    permanent = False

class MainDashboardView(LoginRequiredMixin, TemplateView):
    """
    Main CRM dashboard with revenue charts, pipeline snapshot, activity feed, and stats.
    """
    template_name = 'dashboard/main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)
        
        # Quick Stats - Leads
        leads_qs = Lead.objects.for_user(user) if hasattr(Lead.objects, 'for_user') else Lead.objects.filter(owner=user)
        context['total_leads'] = leads_qs.filter(status__in=['new', 'contacted', 'qualified']).count()
        leads_last_month = leads_qs.filter(
            created_at__gte=last_month_start,
            created_at__lt=last_month_end
        ).count()
        context['leads_change'] = self._calc_change(context['total_leads'], leads_last_month)
        
        # Quick Stats - Opportunities
        opps_qs = Opportunity.objects.for_user(user) if hasattr(Opportunity.objects, 'for_user') else Opportunity.objects.filter(owner=user)
        open_opps = opps_qs.exclude(stage__is_won=True).exclude(stage__is_lost=True)
        context['total_opportunities'] = open_opps.count()
        context['opportunities_value'] = int(open_opps.aggregate(Sum('amount'))['amount__sum'] or 0)
        
        # Quick Stats - Cases
        cases_qs = Case.objects.for_user(user) if hasattr(Case.objects, 'for_user') else Case.objects.filter(owner=user)
        context['total_cases'] = cases_qs.filter(status__in=['new', 'in_progress']).count()
        cases_last_month = cases_qs.filter(
            created_at__gte=last_month_start,
            created_at__lt=last_month_end,
            status__in=['new', 'in_progress']
        ).count()
        context['cases_change'] = self._calc_change(context['total_cases'], cases_last_month)
        
        # Quick Stats - Revenue
        sales_this_month = Sale.objects.filter(sale_date__gte=month_start)
        context['total_revenue'] = int(sales_this_month.aggregate(Sum('amount'))['amount__sum'] or 0)
        sales_last_month = Sale.objects.filter(sale_date__gte=last_month_start, sale_date__lt=last_month_end)
        revenue_last_month = int(sales_last_month.aggregate(Sum('amount'))['amount__sum'] or 0)
        context['revenue_change'] = self._calc_change(context['total_revenue'], revenue_last_month)
        
        # Revenue Chart Data (last 6 months)
        revenue_labels = []
        revenue_data = []
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30*i)
            month_start_dt = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start_dt + timedelta(days=32)).replace(day=1)
            
            revenue = Sale.objects.filter(
                sale_date__gte=month_start_dt,
                sale_date__lt=next_month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            revenue_labels.append(month_start_dt.strftime('%b'))
            revenue_data.append(float(revenue))
        
        context['revenue_labels'] = json.dumps(revenue_labels)
        context['revenue_data'] = json.dumps(revenue_data)
        
        # Pipeline Snapshot (by stage)
        pipeline_labels = []
        pipeline_data = []
        
        # Get all opportunity stages
        from opportunities.models import OpportunityStage
        stages = OpportunityStage.objects.filter(is_won=False, is_lost=False).order_by('order')
        
        for stage in stages:
            count = open_opps.filter(stage=stage).count()
            if count > 0:
                pipeline_labels.append(stage.name)
                pipeline_data.append(count)
        
        context['pipeline_labels'] = json.dumps(pipeline_labels)
        context['pipeline_data'] = json.dumps(pipeline_data)
        
        # Activity Feed
        activities = []
        
        # Recent leads
        recent_leads = leads_qs.order_by('-created_at')[:3]
        for lead in recent_leads:
            activities.append({
                'type': 'lead',
                'title': f'New Lead: {lead.full_name}',
                'description': f'{lead.company} - {lead.get_industry_display()}',
                'timestamp': lead.created_at
            })
        
        # Recent opportunities
        recent_opps = opps_qs.order_by('-created_at')[:3]
        for opp in recent_opps:
            activities.append({
                'type': 'opportunity',
                'title': f'Opportunity: {opp.name}',
                'description': f'${opp.amount:,.0f} - {opp.stage.name}',
                'timestamp': opp.created_at
            })
        
        # Recent cases
        recent_cases = cases_qs.order_by('-created_at')[:4]
        for case in recent_cases:
            activities.append({
                'type': 'case',
                'title': f'Case: {case.subject}',
                'description': f'{case.get_priority_display()} priority - {case.get_status_display()}',
                'timestamp': case.created_at
            })
        
        # Sort by timestamp and limit to 10
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        context['recent_activities'] = activities[:10]
        
        return context
    
    def _calc_change(self, current, previous):
        """Calculate percentage change."""
        if previous == 0:
            return 100 if current > 0 else 0
        return int(((current - previous) / previous) * 100)



class CockpitView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/cockpit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # 1. My Day (Tasks)
        context['my_tasks'] = Task.objects.filter(
            assigned_to=user,
            status__in=['todo', 'in_progress'],
            due_date__date__lte=today
        ).order_by('due_date')

        # 2. Hot Leads (Score >= 70)
        context['hot_leads'] = Lead.objects.filter(
            owner=user,
            status__in=['new', 'qualified'],
            lead_score__gte=70
        ).order_by('-lead_score')[:5]

        # 3. At-Risk Accounts (Health < 40)
        context['at_risk_accounts'] = Account.objects.filter(
            owner=user,
            status='active',
            health_score__lt=40
        ).order_by('health_score')[:5]

        # 4. Urgent Cases
        context['urgent_cases'] = Case.objects.filter(
            owner=user,
            priority__in=['high', 'critical'],
            status__in=['new', 'in_progress']
        ).order_by('sla_due')[:5]
        
        # 5. Pipeline Summary (Simple aggregation)
        # Assuming Opportunity model exists and has 'amount' and 'stage'
        # We'll add a try/except block or check if Opportunity exists later.
        # For now, let's assume it does based on previous file lists.
        from opportunities.models import Opportunity
        context['pipeline_value'] = 0
        try:
            pipeline = Opportunity.objects.filter(owner=user).exclude(stage__is_won=True).exclude(stage__is_lost=True)
            context['pipeline_value'] = sum(o.amount for o in pipeline if o.amount)
        except Exception:
            pass

        return context

class ManagerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/manager_dashboard.html'

    def test_func(self):
        # Allow staff users or users with specific manager permissions
        return self.request.user.is_staff or self.request.user.groups.filter(name='Sales Manager').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Assuming manager can see all data for their tenant
        
        # Team Revenue (This Month)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        sales_this_month = Sale.objects.filter(sale_date__gte=month_start)
        context['team_revenue'] = sales_this_month.aggregate(Sum('amount'))['amount__sum'] or 0
        context['deals_closed_count'] = sales_this_month.count()
        
        # Pipeline Value
        context['pipeline_value'] = Opportunity.objects.exclude(stage__is_won=True).exclude(stage__is_lost=True).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # At-Risk Accounts
        context['at_risk_count'] = Account.objects.filter(health_score__lt=40, status='active').count()
        
        # Critical Escalations
        context['critical_cases'] = Case.objects.filter(priority='critical', status__in=['new', 'in_progress']).select_related('account', 'owner')[:5]
        
        # Rep Performance (Mock logic for now, aggregating by user)
        reps = User.objects.filter(is_active=True) # Filter by role if available
        rep_data = []
        for rep in reps:
            revenue = Sale.objects.filter(account__owner=rep, sale_date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0
            deals = Sale.objects.filter(account__owner=rep, sale_date__gte=month_start).count()
            pipeline = Opportunity.objects.filter(owner=rep).exclude(stage__is_won=True).exclude(stage__is_lost=True).aggregate(Sum('amount'))['amount__sum'] or 0
            # Simple activity score mock
            activity_score = min(100, (deals * 10) + (pipeline // 1000)) 
            
            rep_data.append({
                'name': rep.get_full_name() or rep.email,
                'revenue': revenue,
                'deals_closed': deals,
                'pipeline': pipeline,
                'activity_score': int(activity_score)
            })
        
        context['rep_performance'] = sorted(rep_data, key=lambda x: x['revenue'], reverse=True)
        
        return context

class SupportDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/support_dashboard.html'

    def test_func(self):
        # Allow staff users or users in Support group
        return self.request.user.is_staff or self.request.user.groups.filter(name='Support').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # My Open Cases
        my_cases = Case.objects.filter(owner=user, status__in=['new', 'in_progress'])
        context['my_queue'] = my_cases.order_by('sla_due')
        context['my_open_cases_count'] = my_cases.count()
        
        # SLA Breaches (My cases overdue)
        now = timezone.now()
        context['sla_breaches'] = my_cases.filter(sla_due__lt=now).count()
        
        # Avg CSAT (My resolved cases)
        # Assuming CSAT is linked to Case via CsatResponse (reverse relation 'csat_response')
        # We need to aggregate across cases owned by user
        # This is a bit complex with reverse relation, so we'll do a simple query
        # Find cases owned by user that have a csat_response
        resolved_cases_ids = Case.objects.filter(owner=user, status='resolved').values_list('id', flat=True)
        # We need to import CsatResponse to query it directly or use annotation if possible
        # Let's import CsatResponse
        from cases.models import CsatResponse, CsatDetractorAlert
        
        avg_csat = CsatResponse.objects.filter(case__id__in=resolved_cases_ids).aggregate(Avg('score'))['score__avg']
        context['avg_csat'] = avg_csat or 0.0
        
        # Recent Detractors (Open alerts assigned to me or unassigned in my queue)
        context['detractor_alerts'] = CsatDetractorAlert.objects.filter(
            status='open'
        ).select_related('response__case__account')[:5]
        
        return context

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def test_func(self):
        # Only allow staff users
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
            
        # System Stats
        # Assuming TenantModel has a way to count unique tenants, but here we might just count users or accounts as proxy if no Tenant model
        # Actually we have TenantModel mixin, but no explicit Tenant model in core?
        # Let's check core/models.py. Usually tenant_id is a string.
        # We can count unique tenant_ids in User model
        context['active_tenants_count'] = User.objects.values('tenant_id').distinct().count()
        context['total_users_count'] = User.objects.count()
        
        # Recent Users
        context['recent_users'] = User.objects.order_by('-date_joined')[:10]
        
        # Billing (MRR)
        # Import Subscription from billing
        try:
            from billing.models import Subscription
            active_subs = Subscription.objects.filter(status='active')
            # MRR = sum of plan prices
            mrr = 0
            for sub in active_subs:
                mrr += sub.plan.price_monthly
            context['mrr'] = mrr
            
            context['recent_subscriptions'] = Subscription.objects.select_related('plan').order_by('-created_at')[:5]
        except ImportError:
            context['mrr'] = 0
            context['recent_subscriptions'] = []
            
        return context
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Sum
from .models import DashboardConfig, DashboardWidget
from .widgets import get_widget, WIDGET_REGISTRY
import json


class DashboardBuilderView(LoginRequiredMixin, TemplateView):
    """
    Dashboard builder with drag-and-drop widget placement.
    """
    template_name = 'dashboard/builder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available widgets
        available_widgets = DashboardWidget.objects.filter(is_active=True).order_by('name')
        context['available_widgets'] = available_widgets
        
        # Get user's existing dashboards
        user_dashboards = DashboardConfig.objects.filter(
            user=self.request.user
        ).order_by('-is_default', '-updated_at')
        context['user_dashboards'] = user_dashboards
        
        # Load dashboard if ID provided
        dashboard_id = self.request.GET.get('dashboard')
        if dashboard_id:
            try:
                dashboard = DashboardConfig.objects.get(pk=dashboard_id, user=self.request.user)
                context['current_dashboard'] = dashboard
                context['layout_json'] = json.dumps(dashboard.layout)
            except DashboardConfig.DoesNotExist:
                pass
        
        return context


class DashboardRenderView(LoginRequiredMixin, TemplateView):
    """
    Render a configured dashboard.
    """
    template_name = 'dashboard/render.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get dashboard
        dashboard_id = kwargs.get('pk') or self.request.GET.get('dashboard')
        
        if dashboard_id:
            dashboard = get_object_or_404(
                DashboardConfig,
                pk=dashboard_id,
                user=self.request.user
            )
        else:
            # Get default dashboard or create one
            dashboard = DashboardConfig.objects.filter(
                user=self.request.user,
                is_default=True
            ).first()
            
            if not dashboard:
                # Create default dashboard
                dashboard = DashboardConfig.objects.create(
                    user=self.request.user,
                    name="My Dashboard",
                    is_default=True,
                    layout={
                        "rows": [
                            {"cols": [{"widget": "revenue", "span": 6}, {"widget": "pipeline", "span": 6}]},
                            {"cols": [{"widget": "tasks", "span": 6}, {"widget": "leads", "span": 6}]}
                        ]
                    }
                )
        
        context['dashboard'] = dashboard
        
        # Render widgets
        widgets_data = []
        for row in dashboard.layout.get('rows', []):
            row_widgets = []
            for col in row.get('cols', []):
                widget_type = col.get('widget')
                widget_span = col.get('span', 6)
                
                try:
                    widget = get_widget(
                        widget_type,
                        self.request,
                        dashboard.widget_settings.get(widget_type, {})
                    )
                    
                    if widget.has_permission():
                        widget_context = widget.get_context_data()
                        widget_data = {
                            'type': widget_type,
                            'span': widget_span,
                            'template': widget.template_path,
                        }
                        # Flatten widget context into the dict
                        widget_data.update(widget_context)
                        row_widgets.append(widget_data)
                except Exception as e:
                    # Skip broken widgets
                    print(f"Error rendering widget {widget_type}: {e}")
                    continue
            
            if row_widgets:
                widgets_data.append(row_widgets)
        
        context['widgets_data'] = widgets_data
        
        return context


class SaveDashboardView(LoginRequiredMixin, View):
    """
    AJAX endpoint to save dashboard configuration.
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
           
            dashboard_id = data.get('dashboard_id')
            name = data.get('name', 'My Dashboard')
            layout = data.get('layout', {})
            widget_settings = data.get('widget_settings', {})
            is_default = data.get('is_default', False)
            
            if dashboard_id:
                # Update existing
                dashboard = DashboardConfig.objects.get(pk=dashboard_id, user=request.user)
                dashboard.name = name
                dashboard.layout = layout
                dashboard.widget_settings = widget_settings
                if is_default:
                    dashboard.set_as_default()
                dashboard.save()
            else:
                # Create new
                dashboard = DashboardConfig.objects.create(
                    user=request.user,
                    name=name,
                    layout=layout,
                    widget_settings=widget_settings,
                    is_default=is_default
                )
            
            return JsonResponse({
                'success': True,
                'dashboard_id': dashboard.id,
                'message': 'Dashboard saved successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
