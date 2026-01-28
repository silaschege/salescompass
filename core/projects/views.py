from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from django.contrib import messages
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView,
    TenantAwareViewMixin
)
from .models import Project, ProjectMilestone, ResourceAllocation

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
