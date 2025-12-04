from django.urls import path
from . import views

app_name = 'global_alerts'

urlpatterns = [
    path('', views.GlobalAlertsDashboardView.as_view(), name='dashboard'),
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    path('alerts/create/', views.AlertCreateView.as_view(), name='alert_create'),
    path('alerts/<int:pk>/', views.AlertDetailView.as_view(), name='alert_detail'),
    path('alerts/<int:pk>/edit/', views.AlertUpdateView.as_view(), name='alert_update'),
    path('alerts/<int:pk>/delete/', views.AlertDeleteView.as_view(), name='alert_delete'),
    path('alerts/<int:pk>/preview/', views.AlertPreviewView.as_view(), name='alert_preview'),
    path('active/', views.ActiveAlertsView.as_view(), name='active_alerts'),
    path('scheduled/', views.ScheduledAlertsView.as_view(), name='scheduled_alerts'),
    path('type/<str:alert_type>/', views.AlertsByTypeView.as_view(), name='alerts_by_type'),
    path('severity/<str:severity>/', views.AlertsBySeverityView.as_view(), name='alerts_by_severity'),
    path('global/', views.GlobalAlertsOnlyView.as_view(), name='global_alerts'),
    path('tenant-specific/', views.TenantSpecificAlertsView.as_view(), name='tenant_specific'),
    path('analytics/', views.AlertAnalyticsView.as_view(), name='analytics'),
]
