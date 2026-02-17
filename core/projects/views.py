from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from django.contrib import messages
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView,
    TenantAwareViewMixin
)
from .models import Project, ProjectMilestone, ResourceAllocation, Timesheet, TimesheetEntry
from tasks.models import Task
from . import reports
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views import View

class ProjectDashboardView(TenantAwareViewMixin, TemplateView):
    template_name = 'projects/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        projects = Project.objects.filter(tenant=tenant)
        
        context['total_projects'] = projects.count()
        context['active_projects'] = projects.filter(status='active').count()
        context['total_budget'] = projects.aggregate(Sum('budget'))['budget__sum'] or 0
        context['total_cost'] = projects.aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
        
        # Recent Milestones
        context['upcoming_milestones'] = ProjectMilestone.objects.filter(
            tenant=tenant,
            is_completed=False
        ).select_related('project').order_by('due_date')[:5]
        
        return context

class ProjectListView(SalesCompassListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

class ProjectCreateView(SalesCompassCreateView):
    model = Project
    fields = ['name', 'description', 'customer', 'status', 'project_type', 'budget', 'start_date', 'end_date', 'project_manager']
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project_list')
    success_message = "Project created successfully."

class ProjectUpdateView(SalesCompassUpdateView):
    model = Project
    fields = ['name', 'description', 'customer', 'status', 'project_type', 'budget', 'start_date', 'end_date', 'project_manager']
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project_list')
    success_message = "Project updated successfully."

class ProjectDetailView(SalesCompassDetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['milestones'] = self.object.milestones.all().order_by('due_date')
        context['allocations'] = self.object.allocations.all().select_related('user')
        return context

class ProjectGanttView(SalesCompassDetailView):
    model = Project
    template_name = 'projects/gantt.html'
    context_object_name = 'project'

class ProjectGanttDataView(TenantAwareViewMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk, tenant=request.user.tenant)
        tasks = Task.objects.filter(project=project).order_by('due_date')
        
        data = []
        for task in tasks:
            # Map task status to gantt progress
            progress = 0
            if task.status == 'completed':
                progress = 100
            elif task.status == 'in_progress':
                progress = 50
                
            data.append({
                'id': str(task.id),
                'name': task.title,
                'start': (task.due_date - timedelta(days=2)).strftime('%Y-%m-%d'), # Dummy start date
                'end': task.due_date.strftime('%Y-%m-%d'),
                'progress': progress,
                'dependencies': '', # Could map to successor_dependencies later
            })
            
        return JsonResponse(data, safe=False)

class ResourceCapacityView(TenantAwareViewMixin, TemplateView):
    template_name = 'projects/resource_capacity.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource_data'] = reports.get_resource_capacity(self.request.user.tenant)
        return context

class RevenueRecognitionView(TenantAwareViewMixin, TemplateView):
    template_name = 'projects/revenue_recognition.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['revenue_data'] = reports.get_revenue_recognition(self.request.user.tenant)
        return context

class ProjectProfitabilityView(TenantAwareViewMixin, TemplateView):
    template_name = 'projects/profitability_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_data'] = reports.get_tenant_projects_profitability(self.request.user.tenant)
        return context

class TimesheetListView(SalesCompassListView):
    model = Timesheet
    template_name = 'projects/timesheet_list.html'
    context_object_name = 'timesheets'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class TimesheetDetailView(SalesCompassDetailView):
    model = Timesheet
    template_name = 'projects/timesheet_detail.html'
    context_object_name = 'timesheet'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = self.object.entries.all().select_related('project', 'task')
        return context

class TimesheetSubmitView(TenantAwareViewMixin, View):
    def post(self, request, pk):
        timesheet = get_object_or_404(Timesheet, pk=pk, tenant=request.user.tenant, user=request.user)
        if timesheet.status == 'draft':
            timesheet.status = 'submitted'
            timesheet.save()
            messages.success(request, "Timesheet submitted for approval.")
        else:
            messages.warning(request, "Timesheet cannot be submitted in its current status.")
        return redirect('projects:timesheet_detail', pk=pk)

class TimesheetApprovalListView(SalesCompassListView):
    model = Timesheet
    template_name = 'projects/timesheet_approval_list.html'
    context_object_name = 'timesheets'

    def get_queryset(self):
        # In a real scenario, we'd filter by projects managed by the user
        # or where the user is a designated approver.
        # For now, show all submitted/approved/rejected for the tenant.
        return super().get_queryset().exclude(status='draft')

class TimesheetApproveRejectView(TenantAwareViewMixin, View):
    def post(self, request, pk):
        timesheet = get_object_or_404(Timesheet, pk=pk, tenant=request.user.tenant)
        action = request.POST.get('action')
        
        if action == 'approve':
            timesheet.status = 'approved'
            timesheet.approved_by = request.user
            timesheet.approved_at = timezone.now()
            messages.success(request, "Timesheet approved.")
        elif action == 'reject':
            timesheet.status = 'rejected'
            timesheet.rejection_reason = request.POST.get('reason', '')
            messages.info(request, "Timesheet rejected.")
        
        timesheet.save()
        return redirect('projects:timesheet_approval_list')
