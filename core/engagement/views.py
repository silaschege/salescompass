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
from .models import NextBestAction, EngagementEvent
from .forms import NextBestActionForm, EngagementEventForm
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
from django.db import transaction
from django.db.models import Q
import json
import logging


class EngagementFeedView(PermissionRequiredMixin, ListView):
    model = EngagementEvent
    template_name = 'engagement/feed.html'
    context_object_name = 'events'
    paginate_by = 50
    required_permission = 'engagement:read'

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'account', 'opportunity', 'created_by', 'contact', 'case'
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
        )
        
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
        
        # Chart data (last 7 days)
        chart_labels = []
        chart_data = []
        event_type_data = []
        event_type_labels = []
        
        for i in range(6, -1, -1):
            date = now - timedelta(days=i)
            date_str = date.strftime('%m/%d')
            count = EngagementEvent.objects.filter(
                tenant_id=tenant_id,
                created_at__date=date.date()
            ).count()
            chart_labels.append(date_str)
            chart_data.append(count)
        
        # Event type distribution
        event_types = events.values('event_type').annotate(count=Count('event_type')).order_by('-count')[:7]
        for et in event_types:
            event_type_labels.append(dict(EngagementEvent.EVENT_TYPES)[et['event_type']])
            event_type_data.append(et['count'])
        
        context['chart_labels'] = chart_labels
        context['chart_data'] = chart_data
        context['event_type_labels'] = event_type_labels
        context['event_type_data'] = event_type_data
        context['now'] = now
        
        return context
    
    def calculate_trend(self, current, previous):
        """Calculate percentage trend."""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)



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
            'account', 'opportunity', 'assigned_to', 'contact', 'engagement_event'
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
        ).order_by('name')[:100]  # Limit to 100 accounts
        
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