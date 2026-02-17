from django.urls import path
from . import views

app_name = 'audit_logs'

urlpatterns = [
    path('', views.AuditLogsDashboardView.as_view(), name='dashboard'),
    path('logs/', views.AuditLogListView.as_view(), name='log_list'),
    path('logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='log_detail'),
    path('recent-actions/', views.RecentActionsView.as_view(), name='recent_actions'),
    path('critical-events/', views.CriticalEventsView.as_view(), name='critical_events'),
    path('state-changes/', views.StateChangesView.as_view(), name='state_changes'),
    path('data-modifications/', views.DataModificationsView.as_view(), name='data_modifications'),
    path('security-events/', views.SecurityEventsView.as_view(), name='security_events'),
    path('soc2-report/', views.SOC2ReportView.as_view(), name='soc2_report'),
    path('hipaa-audit/', views.HIPAAAuditView.as_view(), name='hipaa_audit'),
    path('export/', views.ExportLogsView.as_view(), name='export_logs'),
]
