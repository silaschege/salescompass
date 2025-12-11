from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from .models import AlertConfiguration, AlertInstance, AlertEscalationPolicy, AlertNotification, AlertCorrelationRule
from core.models import User
from tenants.models import Tenant


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class GlobalAlertsDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'global_alerts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Alert statistics
        context['total_alerts'] = AlertInstance.objects.count()
        context['active_alerts'] = AlertInstance.objects.filter(
            status__in=['triggered', 'acknowledged', 'investigating']
        ).count()
        context['critical_alerts'] = AlertInstance.objects.filter(
            severity='critical'
        ).count()
        context['resolved_alerts'] = AlertInstance.objects.filter(
            status='resolved'
        ).count()
        
        # Configuration stats
        context['active_configs'] = AlertConfiguration.objects.filter(is_active=True).count()
        context['total_configs'] = AlertConfiguration.objects.count()
        
        # Recent alerts
        context['recent_alerts'] = AlertInstance.objects.select_related(
            'alert_config', 'tenant', 'triggered_by'
        ).order_by('-triggered_at')[:10]
        
        # Alert types distribution
        context['alert_types'] = AlertConfiguration.objects.values(
            'alert_type'
        ).annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        return context


class AlertConfigurationListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = AlertConfiguration
    template_name = 'global_alerts/alert_configuration_list.html'
    context_object_name = 'alert_configs'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('created_by', 'tenant_filter')
        
        # Apply filters
        search = self.request.GET.get('search')
        alert_type = self.request.GET.get('alert_type')
        severity = self.request.GET.get('severity')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        if is_active is not None:
            if is_active == 'active':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alert_types'] = [
            ('system_performance', 'System Performance'),
            ('security_incident', 'Security Incident'),
            ('availability', 'Availability'),
            ('capacity', 'Capacity'),
            ('data_integrity', 'Data Integrity'),
            ('compliance', 'Compliance'),
            ('business_metric', 'Business Metric'),
            ('custom', 'Custom Alert'),
        ]
        context['severities'] = [
            ('info', 'Information'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ]
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_alert_type'] = self.request.GET.get('alert_type', '')
        context['selected_severity'] = self.request.GET.get('severity', '')
        context['selected_status'] = self.request.GET.get('is_active', '')
        return context


class AlertConfigurationCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = AlertConfiguration
    template_name = 'global_alerts/alert_configuration_form.html'
    fields = [
        'name', 'description', 'is_active', 'alert_type', 'severity', 
        'condition', 'evaluation_frequency', 'notification_channels',
        'escalation_policy', 'alert_recipients', 'tenant_filter'
    ]
    success_url = reverse_lazy('global_alerts:alert_config_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Alert configuration '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class AlertConfigurationUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = AlertConfiguration
    template_name = 'global_alerts/alert_configuration_form.html'
    fields = [
        'name', 'description', 'is_active', 'alert_type', 'severity', 
        'condition', 'evaluation_frequency', 'notification_channels',
        'escalation_policy', 'alert_recipients', 'tenant_filter'
    ]
    success_url = reverse_lazy('global_alerts:alert_config_list')
    pk_url_kwarg = 'config_id'
    
    def form_valid(self, form):
        messages.success(self.request, f"Alert configuration '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class AlertConfigurationDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = AlertConfiguration
    template_name = 'global_alerts/alert_configuration_confirm_delete.html'
    success_url = reverse_lazy('global_alerts:alert_config_list')
    pk_url_kwarg = 'config_id'
    
    def delete(self, request, *args, **kwargs):
        alert_config = self.get_object()
        messages.success(request, f"Alert configuration '{alert_config.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


class AlertInstanceListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = AlertInstance
    template_name = 'global_alerts/alert_instance_list.html'
    context_object_name = 'alerts'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'alert_config', 'tenant', 'triggered_by', 'acknowledged_by', 'resolved_by'
        )
        
        # Apply filters
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        severity = self.request.GET.get('severity')
        alert_type = self.request.GET.get('alert_type')
        tenant_id = self.request.GET.get('tenant_id')
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        if alert_type:
            queryset = queryset.filter(alert_config__alert_type=alert_type)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        return queryset.order_by('-triggered_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = [
            ('triggered', 'Triggered'),
            ('acknowledged', 'Acknowledged'),
            ('investigating', 'Investigating'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('suppressed', 'Suppressed'),
        ]
        context['severities'] = [
            ('info', 'Information'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ]
        context['alert_types'] = [
            ('system_performance', 'System Performance'),
            ('security_incident', 'Security Incident'),
            ('availability', 'Availability'),
            ('capacity', 'Capacity'),
            ('data_integrity', 'Data Integrity'),
            ('compliance', 'Compliance'),
            ('business_metric', 'Business Metric'),
            ('custom', 'Custom Alert'),
        ]
        context['tenants'] = Tenant.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_severity'] = self.request.GET.get('severity', '')
        context['selected_alert_type'] = self.request.GET.get('alert_type', '')
        context['selected_tenant'] = self.request.GET.get('tenant_id', '')
        return context


class AlertInstanceDetailView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'global_alerts/alert_instance_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alert = get_object_or_404(AlertInstance, id=kwargs['alert_id'])
        context['alert'] = alert
        context['related_alerts'] = alert.related_alerts.all()
        context['notifications'] = alert.notifications.all()
        return context


class AcknowledgeAlertView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, alert_id):
        alert = get_object_or_404(AlertInstance, id=alert_id)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        messages.success(request, f"Alert '{alert.title}' acknowledged successfully.")
        return redirect('global_alerts:alert_detail', alert_id=alert.id)


class ResolveAlertView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def post(self, request, alert_id):
        alert = get_object_or_404(AlertInstance, id=alert_id)
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save()
        
        messages.success(request, f"Alert '{alert.title}' resolved successfully.")
        return redirect('global_alerts:alert_detail', alert_id=alert.id)


class AlertEscalationPolicyListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = AlertEscalationPolicy
    template_name = 'global_alerts/escalation_policy_list.html'
    context_object_name = 'policies'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        search = self.request.GET.get('search')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        if is_active is not None:
            if is_active == 'active':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('is_active', '')
        return context


class AlertEscalationPolicyCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = AlertEscalationPolicy
    template_name = 'global_alerts/escalation_policy_form.html'
    fields = [
        'name', 'description', 'is_active', 'steps', 'time_threshold_minutes',
        'repeat_interval_minutes', 'max_escalation_levels', 'notification_channels',
        'escalation_recipients'
    ]
    success_url = reverse_lazy('global_alerts:escalation_policy_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Escalation policy '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class AlertEscalationPolicyUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = AlertEscalationPolicy
    template_name = 'global_alerts/escalation_policy_form.html'
    fields = [
        'name', 'description', 'is_active', 'steps', 'time_threshold_minutes',
        'repeat_interval_minutes', 'max_escalation_levels', 'notification_channels',
        'escalation_recipients'
    ]
    success_url = reverse_lazy('global_alerts:escalation_policy_list')
    pk_url_kwarg = 'policy_id'
    
    def form_valid(self, form):
        messages.success(self.request, f"Escalation policy '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class AlertNotificationListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = AlertNotification
    template_name = 'global_alerts/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'alert_instance', 'alert_instance__alert_config', 'recipient_user', 'tenant'
        )
        
        # Apply filters
        status = self.request.GET.get('status')
        notification_type = self.request.GET.get('notification_type')
        tenant_id = self.request.GET.get('tenant_id')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = [
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('delivered', 'Delivered'),
            ('failed', 'Failed'),
            ('bounced', 'Bounced'),
            ('opened', 'Opened'),
        ]
        context['notification_types'] = [
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('push', 'Push Notification'),
            ('webhook', 'Webhook'),
            ('slack', 'Slack'),
            ('microsoft_teams', 'Microsoft Teams'),
            ('pagerduty', 'PagerDuty'),
            ('custom', 'Custom Channel'),
        ]
        context['tenants'] = Tenant.objects.all()
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_type'] = self.request.GET.get('notification_type', '')
        context['selected_tenant'] = self.request.GET.get('tenant_id', '')
        return context


class AlertCorrelationRuleListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = AlertCorrelationRule
    template_name = 'global_alerts/correlation_rule_list.html'
    context_object_name = 'rules'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        search = self.request.GET.get('search')
        rule_type = self.request.GET.get('rule_type')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        
        if is_active is not None:
            if is_active == 'active':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rule_types'] = [
            ('time_proximity', 'Time Proximity'),
            ('resource_similarity', 'Resource Similarity'),
            ('pattern_matching', 'Pattern Matching'),
            ('dependency_based', 'Dependency Based'),
            ('custom_logic', 'Custom Logic'),
        ]
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_type'] = self.request.GET.get('rule_type', '')
        context['selected_status'] = self.request.GET.get('is_active', '')
        return context


class AlertCorrelationRuleCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = AlertCorrelationRule
    template_name = 'global_alerts/correlation_rule_form.html'
    fields = [
        'name', 'description', 'is_active', 'rule_type', 'conditions',
        'correlation_window_minutes', 'max_correlated_alerts'
    ]
    success_url = reverse_lazy('global_alerts:correlation_rule_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Correlation rule '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class AlertCorrelationRuleUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = AlertCorrelationRule
    template_name = 'global_alerts/correlation_rule_form.html'
    fields = [
        'name', 'description', 'is_active', 'rule_type', 'conditions',
        'correlation_window_minutes', 'max_correlated_alerts'
    ]
    success_url = reverse_lazy('global_alerts:correlation_rule_list')
    pk_url_kwarg = 'rule_id'
    
    def form_valid(self, form):
        messages.success(self.request, f"Correlation rule '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class AlertAnalyticsView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'global_alerts/alert_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Alert analytics
        context['alert_stats'] = {
            'total_alerts': AlertInstance.objects.count(),
            'critical_alerts': AlertInstance.objects.filter(severity='critical').count(),
            'resolved_alerts': AlertInstance.objects.filter(status='resolved').count(),
            'avg_resolution_time_hours': self.get_avg_resolution_time(),
        }
        
        # Alert trends (last 30 days)
        context['alert_trends'] = self.get_alert_trends()
        
        # Top alert sources
        context['top_sources'] = AlertInstance.objects.values(
            'source'
        ).annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        # Alert severities distribution
        context['severity_distribution'] = AlertInstance.objects.values(
            'severity'
        ).annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        return context
    
    def get_avg_resolution_time(self):
        """Calculate average resolution time for resolved alerts"""
        from django.db.models import Avg, F
        resolved_alerts = AlertInstance.objects.filter(
            status='resolved',
            resolved_at__isnull=False
        ).annotate(
            resolution_time=F('resolved_at') - F('triggered_at')
        )
        
        # Calculate average resolution time in hours
        # This is a simplified calculation - in practice you'd need to convert timedelta to hours
        return resolved_alerts.count()  # Placeholder - actual implementation would be more complex
        
    def get_alert_trends(self):
        """Get alert trends over the last 30 days"""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_counts = AlertInstance.objects.filter(
            triggered_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(triggered_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return list(daily_counts)
