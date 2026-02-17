from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q, Avg, F
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from datetime import timedelta
from .models import (
    ResourceAllocation, InfrastructureAlert, PerformanceBaseline, 
    CapacityPlanning, InfrastructureAudit, AppModule, TenantModuleProvision, 
    ModuleProvisionWorkflow, ModuleDependency, ResourceMonitoring, 
    ResourceQuota, ResourceAlert, ResourceUsageReport, AlertNotificationPreference
)
from core.models import User
from tenants.models import Tenant


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class ResourceMonitoringDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'infrastructure/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Resource monitoring statistics
        context['total_monitored_resources'] = ResourceMonitoring.objects.count()
        context['critical_resources'] = ResourceMonitoring.objects.filter(status='critical').count()
        context['warning_resources'] = ResourceMonitoring.objects.filter(status='warning').count()
        context['healthy_resources'] = ResourceMonitoring.objects.filter(status='normal').count()
        
        # Resource types distribution
        context['resource_types'] = ResourceMonitoring.objects.values(
            'resource_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent alerts
        context['recent_alerts'] = ResourceAlert.objects.select_related(
            'resource_monitoring'
        ).order_by('-created_at')[:10]
        
        # Resource utilization by tenant
        context['tenant_utilization'] = Tenant.objects.annotate(
            resource_count=Count('resource_monitoring')
        ).order_by('-resource_count')[:10]
        
        return context


class ResourceMonitoringListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = ResourceMonitoring
    template_name = 'infrastructure/api_calls.html'
    context_object_name = 'resources'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('tenant')
        
        # Apply filters
        resource_type = self.request.GET.get('resource_type')
        service_name = self.request.GET.get('service_name')
        tenant_id = self.request.GET.get('tenant_id')
        status = self.request.GET.get('status')
        
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        if service_name:
            queryset = queryset.filter(service_name__icontains=service_name)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-last_updated')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource_types'] = ResourceMonitoring.objects.values_list(
            'resource_type', flat=True
        ).distinct()
        context['tenants'] = Tenant.objects.all()
        context['statuses'] = ['normal', 'warning', 'critical']
        context['search_query'] = self.request.GET.get('service_name', '')
        context['selected_resource_type'] = self.request.GET.get('resource_type', '')
        context['selected_tenant'] = self.request.GET.get('tenant_id', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class ResourceAlertListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = ResourceAlert
    template_name = 'infrastructure/resource_alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'resource_monitoring', 'resource_monitoring__tenant'
        )
        
        # Apply filters
        alert_type = self.request.GET.get('alert_type')
        severity = self.request.GET.get('severity')
        tenant_id = self.request.GET.get('tenant_id')
        status = self.request.GET.get('status')
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        if tenant_id:
            queryset = queryset.filter(resource_monitoring__tenant_id=tenant_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alert_types'] = ['threshold_exceeded', 'quota_exceeded', 'resource_low', 'peak_usage', 'anomaly_detected']
        context['severities'] = ['info', 'warning', 'error', 'critical']
        context['tenants'] = Tenant.objects.all()
        context['statuses'] = ['open', 'acknowledged', 'resolved', 'closed']
        context['selected_alert_type'] = self.request.GET.get('alert_type', '')
        context['selected_severity'] = self.request.GET.get('severity', '')
        context['selected_tenant'] = self.request.GET.get('tenant_id', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class ResourceQuotaListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = ResourceQuota
    template_name = 'infrastructure/resource_quota_list.html'
    context_object_name = 'quotas'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('tenant')
        
        # Apply filters
        resource_type = self.request.GET.get('resource_type')
        tenant_id = self.request.GET.get('tenant_id')
        is_over_quota = self.request.GET.get('is_over_quota')
        
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        if is_over_quota == 'yes':
            queryset = queryset.extra(where=["used_quota > allocated_quota"])
        elif is_over_quota == 'no':
            queryset = queryset.extra(where=["used_quota <= allocated_quota"])
        
        # Annotate with percentage used
        queryset = queryset.extra(select={
            'percentage_used': 'ROUND((used_quota * 100.0 / allocated_quota), 2)'
        })
        
        return queryset.order_by('-percentage_used')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource_types'] = ResourceQuota.objects.values_list(
            'resource_type', flat=True
        ).distinct()
        context['tenants'] = Tenant.objects.all()
        context['selected_resource_type'] = self.request.GET.get('resource_type', '')
        context['selected_tenant'] = self.request.GET.get('tenant_id', '')
        context['selected_over_quota'] = self.request.GET.get('is_over_quota', '')
        return context


class ResourceQuotaUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = ResourceQuota
    template_name = 'infrastructure/resource_quota_form.html'
    fields = [
        'allocated_quota', 'unit', 'reset_cycle', 
        'is_soft_limit', 'grace_period_hours'
    ]
    success_url = reverse_lazy('infrastructure:resource_quota_list')
    pk_url_kwarg = 'quota_id'
    
    def form_valid(self, form):
        messages.success(self.request, f"Resource quota for {form.instance.tenant.name} updated successfully.")
        return super().form_valid(form)


class ResourceUsageReportListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = ResourceUsageReport
    template_name = 'infrastructure/tenant_usage_list.html'
    context_object_name = 'reports'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('tenant', 'generated_by')
        
        # Apply filters
        report_type = self.request.GET.get('report_type')
        tenant_id = self.request.GET.get('tenant_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.order_by('-generated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_types'] = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'custom']
        context['tenants'] = Tenant.objects.all()
        context['selected_report_type'] = self.request.GET.get('report_type', '')
        context['selected_tenant'] = self.request.GET.get('tenant_id', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        return context


class ResourceUsageReportCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = ResourceUsageReport
    template_name = 'infrastructure/resource_usage_report_form.html'
    fields = [
        'report_type', 'title', 'description', 'start_date', 
        'end_date', 'tenant', 'resource_types', 'notes'
    ]
    success_url = reverse_lazy('infrastructure:resource_usage_report_list')
    
    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        messages.success(self.request, f"Resource usage report '{form.instance.title}' created successfully.")
        return super().form_valid(form)


class ResourceAlertAcknowledgeView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, alert_id):
        alert = get_object_or_404(ResourceAlert, id=alert_id)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        messages.success(request, f"Alert '{alert.message[:50]}...' acknowledged successfully.")
        return redirect('infrastructure:resource_alert_list')


class ResourceAlertResolveView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, alert_id):
        alert = get_object_or_404(ResourceAlert, id=alert_id)
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save()
        
        messages.success(request, f"Alert '{alert.message[:50]}...' resolved successfully.")
        return redirect('infrastructure:resource_alert_list')


class RealTimeMonitoringView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'infrastructure/real_time_monitoring.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get real-time resource data
        context['current_cpu_usage'] = ResourceMonitoring.objects.filter(
            resource_type='cpu'
        ).aggregate(avg_value=Avg('current_value'))['avg_value'] or 0
        
        context['current_memory_usage'] = ResourceMonitoring.objects.filter(
            resource_type='memory'
        ).aggregate(avg_value=Avg('current_value'))['avg_value'] or 0
        
        context['current_storage_usage'] = ResourceMonitoring.objects.filter(
            resource_type='storage'
        ).aggregate(avg_value=Avg('current_value'))['avg_value'] or 0
        
        # Get critical alerts
        context['critical_alerts'] = ResourceAlert.objects.filter(
            severity='critical',
            status='open'
        ).select_related('resource_monitoring').order_by('-created_at')[:5]
        
        # Get resources near threshold
        context['near_threshold_resources'] = ResourceMonitoring.objects.filter(
            Q(current_value__gte=F('threshold_warning'))
        ).order_by('-current_value')[:10]
        
        return context


class AlertConfigurationView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'infrastructure/alert_configuration.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get existing alert configurations
        context['alert_rules'] = ResourceAlert.objects.all()
        context['escalation_paths'] = []  # Placeholder for now
        context['suppression_rules'] = []  # Placeholder for now
        
        return context


class NotificationPreferencesView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = AlertNotificationPreference
    template_name = 'infrastructure/notification_preferences.html'
    context_object_name = 'preferences'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        
        # Apply filters
        alert_type = self.request.GET.get('alert_type')
        user_id = self.request.GET.get('user_id')
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('user__email', 'alert_type')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alert_types'] = AlertNotificationPreference.objects.values_list(
            'alert_type', flat=True
        ).distinct()
        context['users'] = User.objects.all()
        context['channels'] = AlertNotificationPreference.objects.values_list(
            'channel', flat=True
        ).distinct()
        context['selected_alert_type'] = self.request.GET.get('alert_type', '')
        context['selected_user'] = self.request.GET.get('user_id', '')
        return context


# === Application Module Management Views ===

class AppModuleListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    """List all application modules."""
    model = AppModule
    template_name = 'infrastructure/app_module_list.html'
    context_object_name = 'modules'


class AppModuleCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    """Create a new application module."""
    model = AppModule
    template_name = 'infrastructure/app_module_form.html'
    fields = ['module_name', 'module_code', 'description', 'version', 'is_core', 'is_active']
    success_url = reverse_lazy('infrastructure:app_module_list')


class AppModuleUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    """Update an application module."""
    model = AppModule
    template_name = 'infrastructure/app_module_form.html'
    fields = ['module_name', 'module_code', 'description', 'version', 'is_core', 'is_active']
    pk_url_kwarg = 'module_id'
    success_url = reverse_lazy('infrastructure:app_module_list')


class AppModuleDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    """Delete an application module."""
    model = AppModule
    template_name = 'infrastructure/app_module_confirm_delete.html'
    pk_url_kwarg = 'module_id'
    success_url = reverse_lazy('infrastructure:app_module_list')


class AppModuleManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """Application module management dashboard."""
    template_name = 'infrastructure/app_module_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = AppModule.objects.all()
        context['active_modules'] = AppModule.objects.filter(is_active=True).count()
        context['core_modules'] = AppModule.objects.filter(is_core=True).count()
        return context


# === Tenant Module Provisioning Views ===

class TenantModuleProvisionListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    """List tenant module provisions."""
    model = TenantModuleProvision
    template_name = 'infrastructure/tenant_module_provision_list.html'
    context_object_name = 'provisions'


class TenantModuleProvisionCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    """Create a tenant module provision."""
    model = TenantModuleProvision
    template_name = 'infrastructure/tenant_module_provision_form.html'
    fields = ['tenant', 'module', 'provision_status', 'configuration']
    success_url = reverse_lazy('infrastructure:tenant_module_provision_list')


class TenantModuleProvisionUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    """Update a tenant module provision."""
    model = TenantModuleProvision
    template_name = 'infrastructure/tenant_module_provision_form.html'
    fields = ['provision_status', 'configuration']
    pk_url_kwarg = 'provision_id'
    success_url = reverse_lazy('infrastructure:tenant_module_provision_list')


# === Module Provision Workflows ===

class ModuleProvisionWorkflowListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    """List module provision workflows."""
    model = ModuleProvisionWorkflow
    template_name = 'infrastructure/module_provision_workflow_list.html'
    context_object_name = 'workflows'


# === Module Dependencies ===

class ModuleDependencyListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    """List module dependencies."""
    model = ModuleDependency
    template_name = 'infrastructure/module_dependency_list.html'
    context_object_name = 'dependencies'


class ModuleDependencyCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    """Create a module dependency."""
    model = ModuleDependency
    template_name = 'infrastructure/module_dependency_form.html'
    fields = ['module', 'depends_on', 'dependency_type', 'is_optional']
    success_url = reverse_lazy('infrastructure:module_dependency_list')


class ModuleDependencyUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    """Update a module dependency."""
    model = ModuleDependency
    template_name = 'infrastructure/module_dependency_form.html'
    fields = ['dependency_type', 'is_optional']
    pk_url_kwarg = 'dependency_id'
    success_url = reverse_lazy('infrastructure:module_dependency_list')


# === Module Provision Dashboard ===

class ModuleProvisionDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """Module provision dashboard."""
    template_name = 'infrastructure/module_provision_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provisions'] = TenantModuleProvision.objects.select_related('tenant', 'module')[:20]
        context['workflows'] = ModuleProvisionWorkflow.objects.order_by('-created_at')[:10]
        return context


# === Module Health Check ===

class ModuleHealthCheckView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """Module health check view."""
    template_name = 'infrastructure/module_health_check.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = AppModule.objects.filter(is_active=True)
        return context


# === Module Configuration ===

class ModuleConfigurationView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    """Configure a specific module provision."""
    model = TenantModuleProvision
    template_name = 'infrastructure/module_configuration.html'
    fields = ['configuration']
    pk_url_kwarg = 'provision_id'
    success_url = reverse_lazy('infrastructure:tenant_module_provision_list')
