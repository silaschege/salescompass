from django.urls import path, include
from . import views
from dashboard import views as dashboard_views

from django.views.generic import TemplateView

from accounts.views import CustomLoginView

from django.contrib.auth.views import LogoutView
from core import dynamic_choices_views
app_name = 'core'


urlpatterns = [
    # Landing Page
    path('', views.home, name='home'),

    # Public Pages
    path('products/', TemplateView.as_view(template_name='public/products.html'), name='product'),
    path('solutions/', TemplateView.as_view(template_name='public/solutions.html'), name='solutions'),
    path('pricing/', TemplateView.as_view(template_name='public/pricing.html'), name='pricing'),
    path('customers/', TemplateView.as_view(template_name='public/customer.html'), name='customers'),
    path('company/', TemplateView.as_view(template_name='public/company.html'), name='company'),
    path('support/', TemplateView.as_view(template_name='public/support.html'), name='support'),
    path('try/', TemplateView.as_view(template_name='public/try.html'), name='try_free'),
    path('integrations/', TemplateView.as_view(template_name='public/integrations.html'), name='integrations'),
    path('api-docs/', TemplateView.as_view(template_name='public/api.html'), name='api_docs'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('apps/', views.AppSelectionView.as_view(), name='app_selection'),
    path('apps/settings/', views.AppSettingsView.as_view(), name='app_settings'),

    # Admin URLs
    path('', include('core.admin_urls')),
    path('', include('core.security_urls')),

    # CLV Dashboard
    path('clv-dashboard/', views.clv_dashboard, name='clv_dashboard'),
    
    # Add other existing URLs for core
    # (Note: The actual existing URLs would need to be added based on the original file)

    # Module Label URLs
    path('labels/', views.ModuleLabelListView.as_view(), name='module_label_list'),
    path('labels/create/', views.ModuleLabelCreateView.as_view(), name='module_label_create'),
    path('labels/<int:pk>/edit/', views.ModuleLabelUpdateView.as_view(), name='module_label_edit'),
    path('labels/<int:pk>/delete/', views.ModuleLabelDeleteView.as_view(), name='module_label_delete'),

    # Module Choice URLs
    path('module-choices/', views.ModuleChoiceListView.as_view(), name='module_choice_list'),
    path('module-choices/create/', views.ModuleChoiceCreateView.as_view(), name='module_choice_create'),
    path('module-choices/<int:pk>/edit/', views.ModuleChoiceUpdateView.as_view(), name='module_choice_edit'),
    path('module-choices/<int:pk>/delete/', views.ModuleChoiceDeleteView.as_view(), name='module_choice_delete'),

    # Model Choice URLs
    path('model-choices/', views.ModelChoiceListView.as_view(), name='model_choice_list'),
    path('model-choices/create/', views.ModelChoiceCreateView.as_view(), name='model_choice_create'),
    path('model-choices/<int:pk>/edit/', views.ModelChoiceUpdateView.as_view(), name='model_choice_edit'),
    path('model-choices/<int:pk>/delete/', views.ModelChoiceDeleteView.as_view(), name='model_choice_delete'),

    # Field Type URLs
    path('field-types/', views.FieldTypeListView.as_view(), name='field_type_list'),
    path('field-types/create/', views.FieldTypeCreateView.as_view(), name='field_type_create'),
    path('field-types/<int:pk>/edit/', views.FieldTypeUpdateView.as_view(), name='field_type_edit'),
    path('field-types/<int:pk>/delete/', views.FieldTypeDeleteView.as_view(), name='field_type_delete'),

    # Assignment Rule Type URLs
    path('assignment-rule-types/', views.AssignmentRuleTypeListView.as_view(), name='assignment_rule_type_list'),
    path('assignment-rule-types/create/', views.AssignmentRuleTypeCreateView.as_view(), name='assignment_rule_type_create'),
    path('assignment-rule-types/<int:pk>/edit/', views.AssignmentRuleTypeUpdateView.as_view(), name='assignment_rule_type_edit'),
    path('assignment-rule-types/<int:pk>/delete/', views.AssignmentRuleTypeDeleteView.as_view(), name='assignment_rule_type_delete'),

]



urlpatterns += [
    # Dynamic Choices Dashboard
    path('dynamic-choices/', dynamic_choices_views.DynamicChoicesDashboardView.as_view(), name='dynamic_choices_dashboard'),

    # System Config Types
    path('system-config-types/', dynamic_choices_views.SystemConfigTypeListView.as_view(), name='system_config_type_list'),
    path('system-config-types/create/', dynamic_choices_views.SystemConfigTypeCreateView.as_view(), name='system_config_type_create'),
    path('system-config-types/<int:pk>/edit/', dynamic_choices_views.SystemConfigTypeUpdateView.as_view(), name='system_config_type_edit'),
    path('system-config-types/<int:pk>/delete/', dynamic_choices_views.SystemConfigTypeDeleteView.as_view(), name='system_config_type_delete'),

    # System Config Categories
    path('system-config-categories/', dynamic_choices_views.SystemConfigCategoryListView.as_view(), name='system_config_category_list'),
    path('system-config-categories/create/', dynamic_choices_views.SystemConfigCategoryCreateView.as_view(), name='system_config_category_create'),
    path('system-config-categories/<int:pk>/edit/', dynamic_choices_views.SystemConfigCategoryUpdateView.as_view(), name='system_config_category_edit'),
    path('system-config-categories/<int:pk>/delete/', dynamic_choices_views.SystemConfigCategoryDeleteView.as_view(), name='system_config_category_delete'),

    # System Event Types
    path('system-event-types/', dynamic_choices_views.SystemEventTypeListView.as_view(), name='system_event_type_list'),
    path('system-event-types/create/', dynamic_choices_views.SystemEventTypeCreateView.as_view(), name='system_event_type_create'),
    path('system-event-types/<int:pk>/edit/', dynamic_choices_views.SystemEventTypeUpdateView.as_view(), name='system_event_type_edit'),
    path('system-event-types/<int:pk>/delete/', dynamic_choices_views.SystemEventTypeDeleteView.as_view(), name='system_event_type_delete'),

    # System Event Severities
    path('system-event-severities/', dynamic_choices_views.SystemEventSeverityListView.as_view(), name='system_event_severity_list'),
    path('system-event-severities/create/', dynamic_choices_views.SystemEventSeverityCreateView.as_view(), name='system_event_severity_create'),
    path('system-event-severities/<int:pk>/edit/', dynamic_choices_views.SystemEventSeverityUpdateView.as_view(), name='system_event_severity_edit'),
    path('system-event-severities/<int:pk>/delete/', dynamic_choices_views.SystemEventSeverityDeleteView.as_view(), name='system_event_severity_delete'),

    # Health Check Types
    path('health-check-types/', dynamic_choices_views.HealthCheckTypeListView.as_view(), name='health_check_type_list'),
    path('health-check-types/create/', dynamic_choices_views.HealthCheckTypeCreateView.as_view(), name='health_check_type_create'),
    path('health-check-types/<int:pk>/edit/', dynamic_choices_views.HealthCheckTypeUpdateView.as_view(), name='health_check_type_edit'),
    path('health-check-types/<int:pk>/delete/', dynamic_choices_views.HealthCheckTypeDeleteView.as_view(), name='health_check_type_delete'),

    # Health Check Statuses
    path('health-check-statuses/', dynamic_choices_views.HealthCheckStatusListView.as_view(), name='health_check_status_list'),
    path('health-check-statuses/create/', dynamic_choices_views.HealthCheckStatusCreateView.as_view(), name='health_check_status_create'),
    path('health-check-statuses/<int:pk>/edit/', dynamic_choices_views.HealthCheckStatusUpdateView.as_view(), name='health_check_status_edit'),
    path('health-check-statuses/<int:pk>/delete/', dynamic_choices_views.HealthCheckStatusDeleteView.as_view(), name='health_check_status_delete'),

    # Maintenance Statuses
    path('maintenance-statuses/', dynamic_choices_views.MaintenanceStatusListView.as_view(), name='maintenance_status_list'),
    path('maintenance-statuses/create/', dynamic_choices_views.MaintenanceStatusCreateView.as_view(), name='maintenance_status_create'),
    path('maintenance-statuses/<int:pk>/edit/', dynamic_choices_views.MaintenanceStatusUpdateView.as_view(), name='maintenance_status_edit'),
    path('maintenance-statuses/<int:pk>/delete/', dynamic_choices_views.MaintenanceStatusDeleteView.as_view(), name='maintenance_status_delete'),

    # Maintenance Types
    path('maintenance-types/', dynamic_choices_views.MaintenanceTypeListView.as_view(), name='maintenance_type_list'),
    path('maintenance-types/create/', dynamic_choices_views.MaintenanceTypeCreateView.as_view(), name='maintenance_type_create'),
    path('maintenance-types/<int:pk>/edit/', dynamic_choices_views.MaintenanceTypeUpdateView.as_view(), name='maintenance_type_edit'),
    path('maintenance-types/<int:pk>/delete/', dynamic_choices_views.MaintenanceTypeDeleteView.as_view(), name='maintenance_type_delete'),

    # Performance Metric Types
    path('performance-metric-types/', dynamic_choices_views.PerformanceMetricTypeListView.as_view(), name='performance_metric_type_list'),
    path('performance-metric-types/create/', dynamic_choices_views.PerformanceMetricTypeCreateView.as_view(), name='performance_metric_type_create'),
    path('performance-metric-types/<int:pk>/edit/', dynamic_choices_views.PerformanceMetricTypeUpdateView.as_view(), name='performance_metric_type_edit'),
    path('performance-metric-types/<int:pk>/delete/', dynamic_choices_views.PerformanceMetricTypeDeleteView.as_view(), name='performance_metric_type_delete'),

    # Performance Environments
    path('performance-environments/', dynamic_choices_views.PerformanceEnvironmentListView.as_view(), name='performance_environment_list'),
    path('performance-environments/create/', dynamic_choices_views.PerformanceEnvironmentCreateView.as_view(), name='performance_environment_create'),
    path('performance-environments/<int:pk>/edit/', dynamic_choices_views.PerformanceEnvironmentUpdateView.as_view(), name='performance_environment_edit'),
    path('performance-environments/<int:pk>/delete/', dynamic_choices_views.PerformanceEnvironmentDeleteView.as_view(), name='performance_environment_delete'),

    # Notification Types
    path('notification-types/', dynamic_choices_views.NotificationTypeListView.as_view(), name='notification_type_list'),
    path('notification-types/create/', dynamic_choices_views.NotificationTypeCreateView.as_view(), name='notification_type_create'),
    path('notification-types/<int:pk>/edit/', dynamic_choices_views.NotificationTypeUpdateView.as_view(), name='notification_type_edit'),
    path('notification-types/<int:pk>/delete/', dynamic_choices_views.NotificationTypeDeleteView.as_view(), name='notification_type_delete'),

    # Notification Priorities
    path('notification-priorities/', dynamic_choices_views.NotificationPriorityListView.as_view(), name='notification_priority_list'),
    path('notification-priorities/create/', dynamic_choices_views.NotificationPriorityCreateView.as_view(), name='notification_priority_create'),
    path('notification-priorities/<int:pk>/edit/', dynamic_choices_views.NotificationPriorityUpdateView.as_view(), name='notification_priority_edit'),
    path('notification-priorities/<int:pk>/delete/', dynamic_choices_views.NotificationPriorityDeleteView.as_view(), name='notification_priority_delete'),

]
