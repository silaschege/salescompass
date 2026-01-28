from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'global_alerts'

urlpatterns = [
    # Dashboard
    path('', RedirectView.as_view(pattern_name='global_alerts:dashboard', permanent=False), name='index'),
    path('admin/dashboard/', views.GlobalAlertsDashboardView.as_view(), name='dashboard'),
    
    # Alert Configuration Management
    path('admin/configurations/', views.AlertConfigurationListView.as_view(), name='alert_config_list'),
    path('admin/configurations/create/', views.AlertConfigurationCreateView.as_view(), name='alert_config_create'),
    path('admin/configurations/<int:config_id>/update/', views.AlertConfigurationUpdateView.as_view(), name='alert_config_update'),
    path('admin/configurations/<int:config_id>/delete/', views.AlertConfigurationDeleteView.as_view(), name='alert_config_delete'),
    
    # Alert Instance Management
    path('admin/instances/', views.AlertInstanceListView.as_view(), name='alert_instance_list'),
    path('admin/instances/<int:alert_id>/', views.AlertInstanceDetailView.as_view(), name='alert_instance_detail'),
    path('admin/instances/<int:alert_id>/acknowledge/', views.AcknowledgeAlertView.as_view(), name='acknowledge_alert'),
    path('admin/instances/<int:alert_id>/resolve/', views.ResolveAlertView.as_view(), name='resolve_alert'),
    
    # Escalation Policy Management
    path('admin/policies/escalation/', views.AlertEscalationPolicyListView.as_view(), name='escalation_policy_list'),
    path('admin/policies/escalation/create/', views.AlertEscalationPolicyCreateView.as_view(), name='escalation_policy_create'),
    path('admin/policies/escalation/<int:policy_id>/update/', views.AlertEscalationPolicyUpdateView.as_view(), name='escalation_policy_update'),
    
    # Notification Management
    path('admin/notifications/', views.AlertNotificationListView.as_view(), name='notification_list'),
    
    # Correlation Rule Management
    path('admin/rules/correlation/', views.AlertCorrelationRuleListView.as_view(), name='correlation_rule_list'),
    path('admin/rules/correlation/create/', views.AlertCorrelationRuleCreateView.as_view(), name='correlation_rule_create'),
    path('admin/rules/correlation/<int:rule_id>/update/', views.AlertCorrelationRuleUpdateView.as_view(), name='correlation_rule_update'),
    
    # Analytics
    path('admin/analytics/', views.AlertAnalyticsView.as_view(), name='alert_analytics'),
]
