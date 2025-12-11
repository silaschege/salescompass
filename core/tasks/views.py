from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Task, TaskPriority, TaskStatus, TaskType, RecurrencePattern, TaskTemplate
from .forms import TaskForm, TaskPriorityForm, TaskStatusForm, TaskTypeForm, RecurrencePatternForm
from tenants.models import Tenant as TenantModel


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
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Task created successfully.')
        return super().form_valid(form)


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
        return super().form_valid(form)


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


class CompleteTaskView(LoginRequiredMixin, View):
    """Mark a task as complete via API."""
    def post(self, request):
        task_id = request.POST.get('task_id')
        if not task_id:
            return JsonResponse({'error': 'task_id required'}, status=400)
        task = get_object_or_404(Task, pk=task_id)
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        return JsonResponse({'success': True, 'message': 'Task completed'})


class AddTaskCommentView(LoginRequiredMixin, View):
    """Add a comment to a task."""
    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        # For now, just return success - implement comment model later
        messages.success(request, 'Comment added.')
        return redirect('tasks:detail', pk=task_id)


class UploadTaskAttachmentView(LoginRequiredMixin, View):
    """Upload an attachment to a task."""
    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        # For now, just return success - implement attachment model later
        messages.success(request, 'Attachment uploaded.')
        return redirect('tasks:detail', pk=task_id)


class TaskDashboardView(LoginRequiredMixin, TemplateView):
    """Tasks dashboard view."""
    template_name = 'tasks/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['pending_tasks'] = Task.objects.filter(assigned_to=user, status='todo')[:5]
        context['overdue_tasks'] = Task.objects.filter(assigned_to=user, due_date__lt=timezone.now())[:5]
        return context


class TaskCalendarView(LoginRequiredMixin, TemplateView):
    """Tasks calendar view."""
    template_name = 'tasks/calendar.html'


class MyTasksView(LoginRequiredMixin, ListView):
    """Current user's tasks view."""
    model = Task
    template_name = 'tasks/my_tasks.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user)


class TaskKanbanView(LoginRequiredMixin, TemplateView):
    """Tasks kanban board view."""
    template_name = 'tasks/kanban.html'


# Task Template Views
class TaskTemplateListView(LoginRequiredMixin, ListView):
    """Task templates list."""
    model = TaskTemplate
    template_name = 'tasks/template_list.html'
    context_object_name = 'templates'


class TaskTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create task template."""
    model = TaskTemplate
    template_name = 'tasks/template_form.html'
    fields = ['template_name', 'template_description', 'default_title', 'default_description', 
              'default_priority', 'default_task_type', 'estimated_hours_default']
    success_url = reverse_lazy('tasks:template_list')


class TaskTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Update task template."""
    model = TaskTemplate
    template_name = 'tasks/template_form.html'
    fields = ['template_name', 'template_description', 'default_title', 'default_description', 
              'default_priority', 'default_task_type', 'estimated_hours_default']
    success_url = reverse_lazy('tasks:template_list')


class TaskTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete task template."""
    model = TaskTemplate
    template_name = 'tasks/template_confirm_delete.html'
    success_url = reverse_lazy('tasks:template_list')
