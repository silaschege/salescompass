from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Task, TaskPriority, TaskStatus, TaskType, RecurrencePattern, TaskTemplate, TaskDependency, TaskTimeEntry, TaskComment, TaskActivity, TaskSharing,TaskAttachment
from .forms import TaskForm, TaskPriorityForm, TaskStatusForm, TaskTypeForm, RecurrencePatternForm, TaskDependencyForm, TaskTimeEntryForm
from tenants.models import Tenant as TenantModel
from core.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from core.event_bus import event_bus
import json

class TaskPriorityListView(ListView):
    model = TaskPriority
    template_name = 'tasks/task_priority_list.html'
    context_object_name = 'task_priorities'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class TaskPriorityCreateView(CreateView):
    model = TaskPriority
    form_class = TaskPriorityForm
    template_name = 'tasks/task_priority_form.html'
    success_url = reverse_lazy('tasks:task_priority_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Task priority created successfully.')
        return super().form_valid(form)


class TaskPriorityUpdateView(UpdateView):
    model = TaskPriority
    form_class = TaskPriorityForm
    template_name = 'tasks/task_priority_form.html'
    success_url = reverse_lazy('tasks:task_priority_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Task priority updated successfully.')
        return super().form_valid(form)


class TaskPriorityDeleteView(DeleteView):
    model = TaskPriority
    template_name = 'tasks/task_priority_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_priority_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Task priority deleted successfully.')
        return super().delete(request, *args, **kwargs)


class TaskStatusListView(ListView):
    model = TaskStatus
    template_name = 'tasks/task_status_list.html'
    context_object_name = 'task_statuses'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class TaskStatusCreateView(CreateView):
    model = TaskStatus
    form_class = TaskStatusForm
    template_name = 'tasks/task_status_form.html'
    success_url = reverse_lazy('tasks:task_status_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Task status created successfully.')
        return super().form_valid(form)


class TaskStatusUpdateView(UpdateView):
    model = TaskStatus
    form_class = TaskStatusForm
    template_name = 'tasks/task_status_form.html'
    success_url = reverse_lazy('tasks:task_status_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Task status updated successfully.')
        return super().form_valid(form)


class TaskStatusDeleteView(DeleteView):
    model = TaskStatus
    template_name = 'tasks/task_status_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_status_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Task status deleted successfully.')
        return super().delete(request, *args, **kwargs)


class TaskTypeListView(ListView):
    model = TaskType
    template_name = 'tasks/task_type_list.html'
    context_object_name = 'task_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class TaskTypeCreateView(CreateView):
    model = TaskType
    form_class = TaskTypeForm
    template_name = 'tasks/task_type_form.html'
    success_url = reverse_lazy('tasks:task_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Task type created successfully.')
        return super().form_valid(form)


class TaskTypeUpdateView(UpdateView):
    model = TaskType
    form_class = TaskTypeForm
    template_name = 'tasks/task_type_form.html'
    success_url = reverse_lazy('tasks:task_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Task type updated successfully.')
        return super().form_valid(form)


class TaskTypeDeleteView(DeleteView):
    model = TaskType
    template_name = 'tasks/task_type_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Task type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class RecurrencePatternListView(ListView):
    model = RecurrencePattern
    template_name = 'tasks/recurrence_pattern_list.html'
    context_object_name = 'recurrence_patterns'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class RecurrencePatternCreateView(CreateView):
    model = RecurrencePattern
    form_class = RecurrencePatternForm
    template_name = 'tasks/recurrence_pattern_form.html'
    success_url = reverse_lazy('tasks:recurrence_pattern_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Recurrence pattern created successfully.')
        return super().form_valid(form)


class RecurrencePatternUpdateView(UpdateView):
    model = RecurrencePattern
    form_class = RecurrencePatternForm
    template_name = 'tasks/recurrence_pattern_form.html'
    success_url = reverse_lazy('tasks:recurrence_pattern_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Recurrence pattern updated successfully.')
        return super().form_valid(form)


class RecurrencePatternDeleteView(DeleteView):
    model = RecurrencePattern
    template_name = 'tasks/recurrence_pattern_confirm_delete.html'
    success_url = reverse_lazy('tasks:recurrence_pattern_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Recurrence pattern deleted successfully.')
        return super().delete(request, *args, **kwargs)


class TaskListView(ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('assigned_to', 'created_by', 'account', 
                                       'opportunity', 'lead', 'case', 'priority_ref', 
                                       'status_ref', 'task_type_ref', 'recurrence_pattern_ref')


class UndoneWorkView(ListView):
    """View to show undone work (assigned to user or unassigned)."""
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by current tenant
        if hasattr(user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=user.tenant_id)
            
        # Filter for tasks assigned to user OR unassigned/general tasks
        # AND exclude completed or cancelled tasks
        queryset = queryset.filter(
            Q(assigned_to=user) | Q(assigned_to__isnull=True)
        ).exclude(
            status__in=['completed', 'cancelled']
        )
        
        return queryset.select_related('assigned_to', 'created_by', 'account', 
                                       'opportunity', 'lead', 'case', 'priority_ref', 
                                       'status_ref', 'task_type_ref', 'recurrence_pattern_ref')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Undone Work'
        context['page_subtitle'] = 'Tasks assigned to you or waiting for assignment'
        return context


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        
        # Handle generic relation pre-fill from GET parameters
        if self.request.method == 'GET':
            initial = kwargs.get('initial', {})
            content_type_id = self.request.GET.get('content_type')
            object_id = self.request.GET.get('object_id')
            
            if content_type_id and object_id:
                initial['content_type'] = content_type_id
                initial['object_id'] = object_id
                # Also hide relevant fields if linking to a specific object
                # This logic is handled dynamically in the form/template usually
            kwargs['initial'] = initial
            
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Task created successfully.')
        response = super().form_valid(form)
        
        event_bus.emit('task.created', {
            'task_id': self.object.id,
            'title': self.object.title,
            'priority': self.object.priority,
            'status': self.object.status,
            'assigned_to_id': self.object.assigned_to.id if self.object.assigned_to else None,
            'tenant_id': self.request.user.tenant_id if hasattr(self.request.user, 'tenant_id') else None,
            'user': self.request.user
        })
        
        return response


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Task updated successfully.')
        response = super().form_valid(form)
        
        event_bus.emit('task.updated', {
            'task_id': self.object.id,
            'title': self.object.title,
            'priority': self.object.priority,
            'status': self.object.status,
            'assigned_to_id': self.object.assigned_to.id if self.object.assigned_to else None,
            'tenant_id': self.request.user.tenant_id if hasattr(self.request.user, 'tenant_id') else None,
            'user': self.request.user
        })
        
        return response


class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Task deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_http_methods(["GET"])
def get_task_dynamic_choices(request, model_name):
    """
    API endpoint to fetch dynamic choices for task models
    """
    tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
    
    if not tenant_id:
        return JsonResponse({'error': 'No tenant associated with user'}, status=400)
    
    # Map model names to actual models
    model_map = {
        'taskpriority': TaskPriority,
        'taskstatus': TaskStatus,
        'tasktype': TaskType,
        'recurrencepattern': RecurrencePattern,
    }
    
    model_class = model_map.get(model_name.lower())
    
    if not model_class:
        return JsonResponse({'error': 'Invalid choice model'}, status=400)
    
    try:
        choices = model_class.objects.filter(tenant_id=tenant_id).values('id', 'name', 'label')
        return JsonResponse(list(choices), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# === Additional Views Referenced in urls.py ===

class TaskDetailView(LoginRequiredMixin, DetailView):
    """Task detail view."""
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        return Task.objects.filter(tenant_id=self.request.user.tenant_id).prefetch_related(
            'comments__author', 'comments__replies__author', 'comments__mentioned_users',
            'time_entries', 'attachments', 'activities__user'
        ).select_related(
            'assigned_to', 'created_by', 'account', 'opportunity', 'lead', 'case',
            'priority_ref', 'status_ref', 'task_type_ref', 'recurrence_pattern_ref'
        )


class CompleteTaskView(LoginRequiredMixin, View):
    """Mark a task as complete via API."""
    def post(self, request):
        task_id = request.POST.get('task_id')
        if not task_id:
            return JsonResponse({'error': 'task_id required'}, status=400)
        task = get_object_or_404(Task, pk=task_id, tenant_id=request.user.tenant_id)
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        event_bus.emit('task.completed', {
            'task_id': task.id,
            'title': task.title,
            'tenant_id': request.user.tenant_id if hasattr(request.user, 'tenant_id') else None,
            'user': request.user
        })
        
        return JsonResponse({'success': True, 'message': 'Task completed'})


class AddTaskCommentView(LoginRequiredMixin, View):
    """Add a comment to a task."""
    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id, tenant_id=request.user.tenant_id)
        # For now, just return success - implement comment model later
        messages.success(request, 'Comment added.')
        return redirect('tasks:detail', pk=task_id)


class UploadTaskAttachmentView(LoginRequiredMixin, View):
    """Upload an attachment to a task."""
    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id, tenant_id=request.user.tenant_id)
        # For now, just return success - implement attachment model later
        messages.success(request, 'Attachment uploaded.')
        return redirect('tasks:detail', pk=task_id)



class TaskDashboardView(LoginRequiredMixin, TemplateView):
    """Tasks dashboard view."""
    template_name = 'tasks/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = user.tenant_id
        
        # Get task statistics
        all_tasks = Task.objects.filter(tenant_id=tenant_id)
        user_tasks = Task.objects.filter(assigned_to=user, tenant_id=tenant_id)
        
        # Calculate stats for all tasks in the tenant
        context['total_tasks'] = all_tasks.count()
        context['completed_tasks'] = all_tasks.filter(status='completed').count()
        context['overdue_tasks'] = all_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress']
        ).count()
        context['completion_rate'] = round(
            (context['completed_tasks'] / context['total_tasks'] * 100) if context['total_tasks'] > 0 else 0, 
            1
        )
        
        # Recent tasks for the current user
        context['recent_tasks'] = user_tasks.select_related(
            'assigned_to', 'created_by', 'priority_ref', 'status_ref'
        ).order_by('-created_at')[:5]
        
        # Upcoming tasks for the current user (due in next 7 days)
        seven_days_ahead = timezone.now() + timezone.timedelta(days=7)
        context['upcoming_tasks'] = user_tasks.filter(
            due_date__lte=seven_days_ahead,
            status__in=['todo', 'in_progress']
        ).select_related(
            'assigned_to', 'created_by', 'priority_ref', 'status_ref'
        ).order_by('due_date')[:5]
        
        # Stats for the current user
        context['user_total_tasks'] = user_tasks.count()
        context['user_completed_tasks'] = user_tasks.filter(status='completed').count()
        context['user_pending_tasks'] = user_tasks.filter(status='todo').count()
        context['user_inprogress_tasks'] = user_tasks.filter(status='in_progress').count()
        
        # Get tasks by priority for chart (with fallback for empty values)
        low_tasks = user_tasks.filter(priority='low').count()
        medium_tasks = user_tasks.filter(priority='medium').count()
        high_tasks = user_tasks.filter(priority='high').count()
        critical_tasks = user_tasks.filter(priority='critical').count()
        
        context['tasks_by_priority'] = {
            'low': low_tasks,
            'medium': medium_tasks,
            'high': high_tasks,
            'critical': critical_tasks,
        }
        
        # Get tasks by status for chart (with fallback for empty values)
        todo_tasks = user_tasks.filter(status='todo').count()
        in_progress_tasks = user_tasks.filter(status='in_progress').count()
        completed_tasks = user_tasks.filter(status='completed').count()
        cancelled_tasks = user_tasks.filter(status='cancelled').count()
        
        context['tasks_by_status'] = {
            'todo': todo_tasks,
            'in_progress': in_progress_tasks,
            'completed': completed_tasks,
            'cancelled': cancelled_tasks,
        }
        
        # Get weekly task completion trend
        week_ago = timezone.now() - timezone.timedelta(days=7)
        context['weekly_completion_trend'] = []
        for i in range(7):
            day = week_ago + timezone.timedelta(days=i)
            day_end = day.replace(hour=23, minute=59, second=59)
            completed_count = user_tasks.filter(
                status='completed',
                completed_at__date=day.date()
            ).count()
            context['weekly_completion_trend'].append({
                'date': day.strftime('%b %d'),
                'completed': completed_count
            })
        
        # Get task distribution by type
        task_types = user_tasks.values('task_type').annotate(count=Count('id'))
        context['task_types'] = {item['task_type']: item['count'] for item in task_types}
        
        # Get overdue tasks for alert section
        context['overdue_user_tasks'] = user_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress']
        ).select_related('priority_ref', 'status_ref').order_by('due_date')
        
        return context





class TaskCalendarView(LoginRequiredMixin, TemplateView):
    """Tasks calendar view."""
    template_name = 'tasks/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = user.tenant_id
        
        # Get tasks for the current user
        tasks = Task.objects.filter(
            tenant_id=tenant_id,
            assigned_to=user
        ).select_related('priority_ref', 'status_ref')
        
        # Prepare tasks data for FullCalendar
        tasks_data = []
        for task in tasks:
            task_data = {
                'id': task.id,
                'title': task.title,
                'start': task.due_date.isoformat() if task.due_date else None,
                'status': task.status,
                'priority': task.priority,
                'priority_color': task.priority_ref.color if task.priority_ref else '#6c757d',
                'status_label': task.status_ref.label if task.status_ref else task.get_status_display(),
                'priority_label': task.priority_ref.label if task.priority_ref else task.get_priority_display(),
            }
            tasks_data.append(task_data)
        
        import json
        context['tasks_json'] = json.dumps(tasks_data)
        
        return context


class MyTasksView(LoginRequiredMixin, ListView):
    """Current user's tasks view."""
    model = Task
    template_name = 'tasks/my_tasks.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        return Task.objects.filter(
            assigned_to=self.request.user,
            tenant_id=self.request.user.tenant_id
        ).select_related(
            'assigned_to', 'created_by', 'account', 'opportunity', 'lead', 'case',
            'priority_ref', 'status_ref', 'task_type_ref'
        )


class TaskKanbanView(LoginRequiredMixin, TemplateView):
    """Tasks kanban board view."""
    template_name = 'tasks/task_kanban.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group tasks by status for kanban view
        statuses = TaskStatus.objects.filter(tenant_id=self.request.user.tenant_id).order_by('order')
        tasks_by_status = {}
        
        for status in statuses:
            tasks_by_status[status] = Task.objects.filter(
                assigned_to=self.request.user,
                status_ref=status,
                tenant_id=self.request.user.tenant_id
            ).select_related('priority_ref', 'task_type_ref', 'created_by', 'assigned_to').order_by('-created_at')
        
        context['tasks_by_status'] = tasks_by_status
        context['statuses'] = statuses
        
        # Add user stats for the header
        user_tasks = Task.objects.filter(
            assigned_to=self.request.user,
            tenant_id=self.request.user.tenant_id
        )
        
        context['user_total_tasks'] = user_tasks.count()
        context['user_completed_tasks'] = user_tasks.filter(status='completed').count()
        context['user_pending_tasks'] = user_tasks.filter(status='todo').count()
        context['user_inprogress_tasks'] = user_tasks.filter(status='in_progress').count()
        
        return context






class UpdateTaskStatusView(LoginRequiredMixin, View):
    """API endpoint to update task status via drag and drop."""
    def post(self, request):
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            status_id = data.get('status_id')
            
            if not task_id or not status_id:
                return JsonResponse({'success': False, 'error': 'Task ID and Status ID are required'}, status=400)
            
            # Get the task and ensure it belongs to the user's tenant
            task = get_object_or_404(Task, id=task_id, tenant_id=request.user.tenant_id)
            
            # Get the new status and ensure it belongs to the user's tenant
            new_status = get_object_or_404(TaskStatus, id=status_id, tenant_id=request.user.tenant_id)
            
            # Update the task status
            task.status_ref = new_status
            task.status = new_status.status_name  # Update the status field as well
            task.save(update_fields=['status_ref', 'status'])
            
            return JsonResponse({
                'success': True,
                'message': 'Task status updated successfully',
                'task_id': task_id,
                'new_status_id': status_id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
# Task Template Views
class TaskTemplateListView(LoginRequiredMixin, ListView):
    """Task templates list."""
    model = TaskTemplate
    template_name = 'tasks/task_template_list.html'  # Fixed the template name to match actual file
    context_object_name = 'templates'
    
    def get_queryset(self):
        return TaskTemplate.objects.filter(tenant_id=self.request.user.tenant_id)


class TaskTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create task template."""
    model = TaskTemplate
    template_name = 'tasks/task_template_form.html'  # Fixed the template name to match actual file
    fields = ['template_name', 'template_description', 'title_template', 'description_template', 
              'priority', 'priority_ref', 'task_type', 'task_type_ref', 'due_date_offset_days']
    success_url = reverse_lazy('tasks:template_list')
    
    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Task template created successfully.')
        return super().form_valid(form)


class TaskTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Update task template."""
    model = TaskTemplate
    template_name = 'tasks/task_template_form.html'  # Fixed the template name to match actual file
    fields = ['template_name', 'template_description', 'title_template', 'description_template', 
              'priority', 'priority_ref', 'task_type', 'task_type_ref', 'due_date_offset_days']
    success_url = reverse_lazy('tasks:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Task template updated successfully.')
        return super().form_valid(form)


class TaskTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete task template."""
    model = TaskTemplate
    template_name = 'tasks/task_template_confirm_delete.html'  # Fixed the template name to match actual file
    success_url = reverse_lazy('tasks:template_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Task template deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Task Dependency Views
class TaskDependencyCreateView(LoginRequiredMixin, CreateView):
    model = TaskDependency
    form_class = TaskDependencyForm
    template_name = 'tasks/task_dependency_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        # Ensure tenant isolation
        if form.instance.predecessor.tenant_id != self.request.user.tenant_id or \
           form.instance.successor.tenant_id != self.request.user.tenant_id:
            return self.form_invalid(form)
        
        # Validate dependency to prevent circular dependencies
        from .utils import validate_task_dependency
        is_valid, error_msg = validate_task_dependency(form.instance.predecessor, form.instance.successor)
        
        if not is_valid:
            messages.error(self.request, error_msg)
            return self.form_invalid(form)
        
        messages.success(self.request, 'Task dependency created successfully.')
        return super().form_valid(form)


class TaskDependencyDeleteView(LoginRequiredMixin, DeleteView):
    model = TaskDependency
    template_name = 'tasks/task_dependency_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def delete(self, request, *args, **kwargs):
        # Ensure tenant isolation
        obj = self.get_object()
        if obj.tenant_id != request.user.tenant_id:
            return HttpResponseForbidden()
        
        messages.success(request, 'Task dependency deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Task Comment Views
class TaskCommentsView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_comments.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        return Task.objects.filter(tenant_id=self.request.user.tenant_id).prefetch_related('comments__author')


class AddTaskCommentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, tenant_id=request.user.tenant_id)
        content = request.POST.get('content', '')
        
        if content.strip():
            comment = TaskComment.objects.create(
                task=task,
                author=request.user,
                content=content,
                tenant_id=request.user.tenant_id
            )
            
            # Process mentions
            self.process_mentions(comment, content)
            
            messages.success(request, 'Comment added successfully.')
        
        return redirect('tasks:detail', pk=pk)
    
    def process_mentions(self, comment, content):
        # Simple mention processing - could be enhanced
        import re
        mentioned_emails = re.findall(r'@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content)
        
        for email in mentioned_emails:
            try:
                user = User.objects.get(email=email, tenant_id=comment.tenant_id)
                comment.mentioned_users.add(user)
                # Send notification to mentioned user
                self.send_mention_notification(user, comment)
            except User.DoesNotExist:
                continue
    
    def send_mention_notification(self, user, comment):
        # Send notification to mentioned user
        pass  # Implementation depends on notification system


# Task Attachment Views
class UploadTaskAttachmentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, tenant_id=request.user.tenant_id)
        uploaded_file = request.FILES.get('file')
        
        if uploaded_file:
            # Validate file size (e.g., max 10MB)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
                messages.error(request, 'File size exceeds 10MB limit.')
                return redirect('tasks:detail', pk=pk)
            
            # Create attachment record
            attachment = TaskAttachment.objects.create(
                task=task,
                file=uploaded_file,
                filename=uploaded_file.name,
                uploaded_by=request.user,
                file_size=uploaded_file.size,
                mime_type=uploaded_file.content_type or '',
                tenant_id=request.user.tenant_id
            )
            
            messages.success(request, f'File "{uploaded_file.name}" uploaded successfully.')
        
        return redirect('tasks:detail', pk=pk)


class DownloadTaskAttachmentView(LoginRequiredMixin, View):
    def get(self, request, pk, attachment_pk):
        from django.http import Http404
        
        attachment = get_object_or_404(
            TaskAttachment, 
            pk=attachment_pk, 
            task_id=pk,
            tenant_id=request.user.tenant_id
        )
        
        if not attachment.file:
            raise Http404("File not found")
        
        response = FileResponse(
            attachment.file.open('rb'),
            content_type='application/octet-stream',
            as_attachment=True,
            filename=attachment.filename
        )
        return response


# Task Time Entry Views
class AddTaskTimeEntryView(LoginRequiredMixin, CreateView):
    """Add time entry for a task."""
    model = TaskTimeEntry
    fields = ['date_logged', 'hours_spent', 'description', 'is_billable']
    template_name = 'tasks/time_entry_form.html'
    
    def form_valid(self, form):
        task_id = self.kwargs['pk']
        task = get_object_or_404(Task, pk=task_id, tenant_id=self.request.user.tenant_id)
        
        form.instance.task = task
        form.instance.user = self.request.user
        form.instance.tenant_id = self.request.user.tenant_id
        
        messages.success(self.request, 'Time entry added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('tasks:detail', kwargs={'pk': self.kwargs['pk']})


class UpdateTaskTimeEntryView(LoginRequiredMixin, UpdateView):
    """Update time entry for a task."""
    model = TaskTimeEntry
    fields = ['date_logged', 'hours_spent', 'description', 'is_billable']
    template_name = 'tasks/time_entry_form.html'
    
    def get_queryset(self):
        return TaskTimeEntry.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def form_valid(self, form):
        messages.success(self.request, 'Time entry updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('tasks:detail', kwargs={'pk': self.object.task.pk})


class DeleteTaskTimeEntryView(LoginRequiredMixin, DeleteView):
    """Delete time entry for a task."""
    model = TaskTimeEntry
    template_name = 'tasks/time_entry_confirm_delete.html'
    
    def get_queryset(self):
        return TaskTimeEntry.objects.filter(tenant_id=self.request.user.tenant_id)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Time entry deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Task Sharing Views
class ShareTaskView(LoginRequiredMixin, View):
    """Share a task with other users or teams."""
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, tenant_id=request.user.tenant_id)
        shared_with_user_id = request.POST.get('shared_with_user')
        shared_with_team_id = request.POST.get('shared_with_team')
        share_level = request.POST.get('share_level', 'view')
        expires_at = request.POST.get('expires_at')
        can_reassign = request.POST.get('can_reassign', False)
        
        if shared_with_user_id:
            try:
                shared_with_user = User.objects.get(id=shared_with_user_id, tenant_id=request.user.tenant_id)
                from .utils import share_task_with_user
                share_task_with_user(task, shared_with_user, request.user, share_level, expires_at, can_reassign)
                messages.success(request, f'Task shared with {shared_with_user.email}.')
            except User.DoesNotExist:
                messages.error(request, 'Selected user does not exist.')
        elif shared_with_team_id:
            # Assuming there's a Team model
            from accounts.models import Team
            try:
                shared_with_team = Team.objects.get(id=shared_with_team_id, tenant_id=request.user.tenant_id)
                from .utils import share_task_with_team
                share_task_with_team(task, shared_with_team, request.user, share_level, expires_at, can_reassign)
                messages.success(request, f'Task shared with {shared_with_team.name}.')
            except Team.DoesNotExist:
                messages.error(request, 'Selected team does not exist.')
        
        return redirect('tasks:detail', pk=pk)


class UnshareTaskView(LoginRequiredMixin, View):
    """Remove sharing of a task with a user or team."""
    def post(self, request, pk, sharing_id):
        task = get_object_or_404(Task, pk=pk, tenant_id=request.user.tenant_id)
        sharing = get_object_or_404(TaskSharing, id=sharing_id, task=task, tenant_id=request.user.tenant_id)
        
        sharing.delete()
        messages.success(request, 'Task sharing removed.')
        
        return redirect('tasks:detail', pk=pk)


# Subtask Views
class CreateSubtaskView(LoginRequiredMixin, CreateView):
    """Create a subtask for a parent task."""
    model = Task
    fields = ['title', 'task_description', 'assigned_to', 'priority', 'priority_ref', 'status', 'status_ref', 'task_type', 'task_type_ref', 'due_date']
    template_name = 'tasks/subtask_form.html'
    
    def form_valid(self, form):
        parent_task = get_object_or_404(Task, pk=self.kwargs['pk'], tenant_id=self.request.user.tenant_id)
        
        form.instance.parent_task = parent_task
        form.instance.created_by = self.request.user
        form.instance.tenant_id = self.request.user.tenant_id
        
        # Set default values from parent if not provided
        if not form.instance.assigned_to:
            form.instance.assigned_to = parent_task.assigned_to
        if not form.instance.due_date:
            form.instance.due_date = parent_task.due_date
        
        messages.success(self.request, 'Subtask created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('tasks:detail', kwargs={'pk': self.kwargs['pk']})


class TaskActivitiesView(LoginRequiredMixin, DetailView):
    """View task activities."""
    model = Task
    template_name = 'tasks/task_activities.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        return Task.objects.filter(tenant_id=self.request.user.tenant_id).prefetch_related('activities__user')


class BulkUpdateTasksView(LoginRequiredMixin, View):
    """Bulk update multiple tasks."""
    def post(self, request):
        task_ids = request.POST.getlist('task_ids')
        update_field = request.POST.get('update_field')
        update_value = request.POST.get('update_value')
        
        if task_ids and update_field and update_value:
            # Validate that all tasks belong to the same tenant
            tasks = Task.objects.filter(
                id__in=task_ids,
                tenant_id=request.user.tenant_id
            )
            
            if tasks.count() != len(task_ids):
                messages.error(request, 'Some tasks do not exist or belong to your tenant.')
                return redirect('tasks:task_list')
            
            # Update the specified field
            update_data = {update_field: update_value}
            from .utils import bulk_update_tasks
            updated_count = bulk_update_tasks(task_ids, update_data, request.user)
            
            messages.success(request, f'{updated_count} tasks updated successfully.')
        else:
            messages.error(request, 'Please select tasks and specify update values.')
        
        return redirect('tasks:task_list')


class BulkDeleteTasksView(LoginRequiredMixin, View):
    """Bulk delete multiple tasks."""
    def post(self, request):
        task_ids = request.POST.getlist('task_ids')
        
        if task_ids:
            from .utils import bulk_delete_tasks
            deleted_count = bulk_delete_tasks(task_ids, request.user)
            messages.success(request, f'{deleted_count} tasks deleted successfully.')
        else:
            messages.error(request, 'Please select tasks to delete.')
        
        return redirect('tasks:task_list')


class BulkAssignTasksView(LoginRequiredMixin, View):
    """Bulk assign multiple tasks to a user."""
    def post(self, request):
        task_ids = request.POST.getlist('task_ids')
        assigned_to_user_id = request.POST.get('assigned_to_user')
        
        if task_ids and assigned_to_user_id:
            try:
                assigned_to_user = User.objects.get(id=assigned_to_user_id, tenant_id=request.user.tenant_id)
                from .utils import bulk_assign_tasks
                assigned_count = bulk_assign_tasks(task_ids, assigned_to_user, request.user)
                messages.success(request, f'{assigned_count} tasks assigned successfully.')
            except User.DoesNotExist:
                messages.error(request, 'Selected user does not exist.')
        else:
            messages.error(request, 'Please select tasks and a user to assign to.')
        
        return redirect('tasks:task_list')