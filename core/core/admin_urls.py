from django.urls import path
from . import admin_views



urlpatterns = [
    # System Configuration
    path('admin/system-config/', admin_views.SystemConfigurationView.as_view(), name='system_configuration'),
    path('admin/env-vars/', admin_views.EnvironmentVariablesView.as_view(), name='environment_variables'),
    path('admin/feature-toggles/', admin_views.FeatureToggleManagementView.as_view(), name='feature_toggle_management'),
    path('admin/config-audit/', admin_views.ConfigurationAuditView.as_view(), name='configuration_audit'),
    path('admin/maintenance/', admin_views.SystemMaintenanceView.as_view(), name='system_maintenance'),
    path('admin/data-management/', admin_views.DataManagementView.as_view(), name='data_management'),
    path('admin/backup-management/', admin_views.BackupManagementView.as_view(), name='backup_management'),
]
