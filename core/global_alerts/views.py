from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Alert
from .utils import (
    get_active_alerts, get_scheduled_alerts, get_alerts_by_type,
    get_alerts_by_severity, get_alert_statistics, get_global_alerts,
    get_tenant_specific_alerts
)


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class GlobalAlertsDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'global_alerts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = get_alert_statistics()
        context.update(stats)
        context['recent_alerts'] = Alert.objects.all()[:10]
        return context


class AlertListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Alert
    template_name = 'global_alerts/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        alert_type = self.request.GET.get('type')
        severity = self.request.GET.get('severity')
        is_global = self.request.GET.get('is_global')
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if is_global is not None:
            queryset = queryset.filter(is_global=is_global == 'true')
        
        return queryset


class AlertCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Alert
    template_name = 'global_alerts/alert_form.html'
    fields = ['title', 'message', 'alert_type', 'severity', 'start_time', 'end_time',
              'is_global', 'target_tenant_ids', 'is_dismissible', 'show_on_all_pages']
    success_url = reverse_lazy('global_alerts:alert_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user.username
        messages.success(self.request, f"Alert '{form.instance.title}' created successfully.")
        return super().form_valid(form)


class AlertUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Alert
    template_name = 'global_alerts/alert_form.html'
    fields = ['title', 'message', 'alert_type', 'severity', 'start_time', 'end_time',
              'is_global', 'target_tenant_ids', 'is_dismissible', 'show_on_all_pages', 'is_active']
    success_url = reverse_lazy('global_alerts:alert_list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Alert '{form.instance.title}' updated successfully.")
        return super().form_valid(form)


class AlertDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = Alert
    template_name = 'global_alerts/alert_confirm_delete.html'
    success_url = reverse_lazy('global_alerts:alert_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Alert deleted successfully.")
        return super().delete(request, *args, **kwargs)


class AlertDetailView(LoginRequiredMixin, SuperuserRequiredMixin, DetailView):
    model = Alert
    template_name = 'global_alerts/alert_detail.html'
    context_object_name = 'alert'


class ActiveAlertsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Alert
    template_name = 'global_alerts/active_alerts.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        return get_active_alerts()


class ScheduledAlertsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Alert
    template_name = 'global_alerts/scheduled_alerts.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        return get_scheduled_alerts()


class AlertsByTypeView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Alert
    template_name = 'global_alerts/alerts_by_type.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        alert_type = self.kwargs.get('alert_type')
        return get_alerts_by_type(alert_type)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alert_type'] = self.kwargs.get('alert_type')
        return context


class AlertsBySeverityView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Alert
    template_name = 'global_alerts/alerts_by_severity.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        severity = self.kwargs.get('severity')
        return get_alerts_by_severity(severity)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['severity'] = self.kwargs.get('severity')
        return context


class GlobalAlertsOnlyView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Alert
    template_name = 'global_alerts/global_alerts.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        return get_global_alerts()


class TenantSpecificAlertsView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Alert
    template_name = 'global_alerts/tenant_specific.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        return get_tenant_specific_alerts()


class AlertPreviewView(LoginRequiredMixin, SuperuserRequiredMixin, DetailView):
    model = Alert
    template_name = 'global_alerts/alert_preview.html'
    context_object_name = 'alert'


class AlertAnalyticsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'global_alerts/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = get_alert_statistics()
        context.update(stats)
        
        # Additional analytics
        context['active_alerts_list'] = get_active_alerts()[:5]
        context['scheduled_alerts_list'] = get_scheduled_alerts()[:5]
        
        return context
