from django.shortcuts import render
from django.views.generic import TemplateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import TenantUsage, ResourceLimit


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class InfrastructureDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'infrastructure/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add summary data
        context['total_api_calls'] = sum(t.api_calls_count for t in TenantUsage.objects.all())
        context['total_storage_used'] = sum(t.storage_used_gb for t in TenantUsage.objects.all())
        context['total_db_connections'] = sum(t.active_db_connections for t in TenantUsage.objects.all())
        return context


class TenantUsageListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = TenantUsage
    template_name = 'infrastructure/tenant_usage_list.html'
    context_object_name = 'tenant_usages'
    paginate_by = 20


class APICallsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = TenantUsage
    template_name = 'infrastructure/api_calls.html'
    context_object_name = 'tenant_usages'
    ordering = ['-api_calls_count']
    paginate_by = 20


class StorageUsageView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = TenantUsage
    template_name = 'infrastructure/storage_usage.html'
    context_object_name = 'tenant_usages'
    ordering = ['-storage_used_gb']
    paginate_by = 20


class DBConnectionsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = TenantUsage
    template_name = 'infrastructure/db_connections.html'
    context_object_name = 'tenant_usages'
    ordering = ['-active_db_connections']
    paginate_by = 20


class ThrottledTenantsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = ResourceLimit
    template_name = 'infrastructure/throttled_tenants.html'
    context_object_name = 'resource_limits'
    
    def get_queryset(self):
        return ResourceLimit.objects.filter(is_throttled=True)


class ResourceLimitUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = ResourceLimit
    fields = ['is_throttled', 'throttle_reason', 'custom_api_limit', 'custom_storage_limit_gb', 'custom_db_connections']
    template_name = 'infrastructure/resource_limit_form.html'
    success_url = reverse_lazy('infrastructure:throttled_tenants')
    
    def form_valid(self, form):
        messages.success(self.request, "Resource limits updated successfully.")
        return super().form_valid(form)


class SystemHealthView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'infrastructure/system_health.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mock health data for now
        context['cpu_usage'] = 45
        context['memory_usage'] = 60
        context['disk_usage'] = 30
        return context


class PerformanceMetricsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'infrastructure/performance_metrics.html'


class ResourceAlertsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = TenantUsage
    template_name = 'infrastructure/resource_alerts.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        # Return tenants that are over their limits
        return [t for t in TenantUsage.objects.all() if t.is_over_api_limit or t.is_over_storage_limit]
