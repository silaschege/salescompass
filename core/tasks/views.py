from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.http import JsonResponse
from core.permissions import ObjectPermissionRequiredMixin, PermissionRequiredMixin
from .models import Task, TaskComment, TaskAttachment, TaskTemplate
from .forms import TaskForm, TaskCommentForm, TaskAttachmentForm, TaskTemplateForm
from django.utils import timezone


class TaskListView(PermissionRequiredMixin, ListView):
    """List all tasks with filtering and search."""
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25
    required_permission = 'tasks:read'

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'assigned_to', 'created_by', 'account', 'opportunity', 
            'related_lead', 'case'
        )
        
        # Filter by assigned user
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
            
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        # Filter by task type
        task_type = self.request.GET.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
            
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        # Overdue tasks
        overdue = self.request.GET.get('overdue')
        if overdue:
            queryset = queryset.filter(due_date__lt=timezone.now(), status__in=['todo', 'in_progress'])
            
        return queryset.order_by('-due_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_types'] = Task._meta.get_field('task_type').choices
        context['priorities'] = Task._meta.get_field('priority').choices
        context['statuses'] = Task._meta.get_field('status').choices
        
        # Get team members for assignment filter
        from core.models import User
        context['team_members'] = User.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        )
        
        return context


class TaskDetailView(PermissionRequiredMixin, DetailView):
    """Display detailed task information."""
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    required_permission = 'tasks:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = TaskCommentForm()
        context['attachment_form'] = TaskAttachmentForm()
        context['comments'] = self.object.comments.select_related('author').order_by('-created_at')
        context['attachments'] = self.object.attachments.select_related('uploaded_by')
        return context


class TaskCreateView(PermissionRequiredMixin, CreateView):
    """Create a new task."""
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:list')
    required_permission = 'tasks:write'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Pre-populate from related objects
        if 'account_pk' in self.kwargs:
            kwargs['initial'] = {'account': self.kwargs['account_pk']}
        elif 'opportunity_pk' in self.kwargs:
            kwargs['initial'] = {'opportunity': self.kwargs['opportunity_pk']}
        elif 'lead_pk' in self.kwargs:
            kwargs['initial'] = {'related_lead': self.kwargs['lead_pk']}
        elif 'case_pk' in self.kwargs:
            kwargs['initial'] = {'case': self.kwargs['case_pk']}
            
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        messages.success(self.request, f"Task '{form.instance.title}' created successfully!")
        return super().form_valid(form)


class TaskUpdateView(PermissionRequiredMixin, UpdateView):
    """Update an existing task."""
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:list')
    required_permission = 'tasks:write'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Task '{form.instance.title}' updated successfully!")
        return super().form_valid(form)


class TaskDeleteView(PermissionRequiredMixin, DeleteView):
    """Delete a task."""
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:list')
    required_permission = 'tasks:delete'

    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        messages.success(request, f"Task '{task.title}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


class TaskDashboardView(PermissionRequiredMixin, TemplateView):
    """Tasks dashboard with KPIs and charts."""
    template_name = 'tasks/dashboard.html'
    required_permission = 'tasks:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        
        # Get user's tasks
        my_tasks = Task.objects.filter(
            assigned_to=user,
            tenant_id=tenant_id
        )
        
        # KPIs
        context['total_tasks'] = my_tasks.count()
        context['completed_tasks'] = my_tasks.filter(status='completed').count()
        context['overdue_tasks'] = my_tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now()
        ).count()
        context['high_priority_tasks'] = my_tasks.filter(priority='high').count()
        
        # Completion rate
        if context['total_tasks'] > 0:
            context['completion_rate'] = (context['completed_tasks'] / context['total_tasks']) * 100
        else:
            context['completion_rate'] = 0
            
        # Recent tasks
        context['recent_tasks'] = my_tasks.order_by('-created_at')[:10]
        context['upcoming_tasks'] = my_tasks.filter(
            status__in=['todo', 'in_progress']
        ).order_by('due_date')[:10]
        
        return context


class TaskCalendarView(PermissionRequiredMixin, TemplateView):
    """Calendar view for tasks."""
    template_name = 'tasks/calendar.html'
    required_permission = 'tasks:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        
        # Get user's tasks for calendar
        tasks = Task.objects.filter(
            assigned_to=user,
            tenant_id=tenant_id
        ).values('id', 'title', 'due_date', 'status', 'priority')
        
        context['tasks_json'] = list(tasks)
        return context


class MyTasksView(PermissionRequiredMixin, ListView):
    """List tasks assigned to the current user."""
    model = Task
    template_name = 'tasks/my_tasks.html'
    context_object_name = 'tasks'
    paginate_by = 20
    required_permission = 'tasks:read'

    def get_queryset(self):
        return Task.objects.filter(
            assigned_to=self.request.user,
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).select_related(
            'created_by', 'account', 'opportunity', 'related_lead', 'case'
        ).order_by('-due_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_types'] = Task._meta.get_field('task_type').choices
        context['priorities'] = Task._meta.get_field('priority').choices
        context['statuses'] = Task._meta.get_field('status').choices
        return context


class TaskKanbanView(PermissionRequiredMixin, TemplateView):
    """Kanban board view for tasks."""
    template_name = 'tasks/task_kanban.html'
    required_permission = 'tasks:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        
        # Get tasks by status for kanban columns
        tasks = Task.objects.filter(
            assigned_to=user,
            tenant_id=tenant_id
        ).select_related(
            'created_by', 'account', 'opportunity', 'related_lead', 'case'
        )
        
        context['todo_tasks'] = tasks.filter(status='todo')
        context['in_progress_tasks'] = tasks.filter(status='in_progress')
        context['completed_tasks'] = tasks.filter(status='completed')
        context['cancelled_tasks'] = tasks.filter(status='cancelled')
        
        return context


class CompleteTaskView(PermissionRequiredMixin, View):
    """AJAX endpoint to complete a task."""
    required_permission = 'tasks:write'

    def post(self, request):
        if not request.user.is_authenticated:
            messages.error(request, 'Authentication required')
            return redirect('tasks:list')
            # return JsonResponse({'error': 'Authentication required'}, status=403)
            
        try:
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id, tenant_id=getattr(request.user, 'tenant_id', None))
            
            # Permission check
            if task.assigned_to != request.user and not request.user.has_perm('tasks:write'):
                messages.error(request, 'Permission denied')
                return redirect('tasks:list')
                # return JsonResponse({'error': 'Permission denied'}, status=403)
                
            task.mark_completed(request.user)
            messages.success(request, 'Task completed successfully!')
            return redirect('tasks:detail', pk=task_id)
            # return JsonResponse({'success': True, 'message': 'Task completed successfully!'})
            
        except Exception as e:
            messages.error(request, f'Error completing task: {str(e)}')
            return redirect('tasks:list')
            # return JsonResponse({'error': str(e)}, status=400)


class AddTaskCommentView(PermissionRequiredMixin, View):
    """AJAX endpoint to add a comment to a task."""
    required_permission = 'tasks:write'

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id, tenant_id=getattr(request.user, 'tenant_id', None))
        
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.tenant_id = getattr(request.user, 'tenant_id', None)
            comment.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': form.errors}, status=400)


class UploadTaskAttachmentView(PermissionRequiredMixin, View):
    """AJAX endpoint to upload a task attachment."""
    required_permission = 'tasks:write'

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id, tenant_id=getattr(request.user, 'tenant_id', None))
        
        form = TaskAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = task
            attachment.uploaded_by = request.user
            attachment.tenant_id = getattr(request.user, 'tenant_id', None)
            attachment.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': form.errors}, status=400)


# Task Template Views
class TaskTemplateListView(PermissionRequiredMixin, ListView):
    model = TaskTemplate
    template_name = 'tasks/task_template_list.html'
    context_object_name = 'templates'
    required_permission = 'tasks:write'


class TaskTemplateCreateView(PermissionRequiredMixin, CreateView):
    model = TaskTemplate
    form_class = TaskTemplateForm
    template_name = 'tasks/task_template_form.html'
    success_url = reverse_lazy('tasks:template_list')
    required_permission = 'tasks:write'


class TaskTemplateUpdateView(PermissionRequiredMixin, UpdateView):
    model = TaskTemplate
    form_class = TaskTemplateForm
    template_name = 'tasks/task_template_form.html'
    success_url = reverse_lazy('tasks:template_list')
    required_permission = 'tasks:write'


class TaskTemplateDeleteView(PermissionRequiredMixin, DeleteView):
    model = TaskTemplate
    template_name = 'tasks/task_template_confirm_delete.html'
    success_url = reverse_lazy('tasks:template_list')
    required_permission = 'tasks:write'