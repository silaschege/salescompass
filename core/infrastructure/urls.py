from django.urls import path
from . import views

app_name = 'infrastructure'

urlpatterns = [
    path('', views.InfrastructureDashboardView.as_view(), name='dashboard'),
    path('tenant-usage/', views.TenantUsageListView.as_view(), name='tenant_usage'),
    path('api-calls/', views.APICallsView.as_view(), name='api_calls'),
    path('storage-usage/', views.StorageUsageView.as_view(), name='storage_usage'),
    path('db-connections/', views.DBConnectionsView.as_view(), name='db_connections'),
    path('throttled-tenants/', views.ThrottledTenantsView.as_view(), name='throttled_tenants'),
    path('resource-limit/<int:pk>/update/', views.ResourceLimitUpdateView.as_view(), name='resource_limit_update'),
    path('system-health/', views.SystemHealthView.as_view(), name='system_health'),
    path('performance-metrics/', views.PerformanceMetricsView.as_view(), name='performance_metrics'),
    path('resource-alerts/', views.ResourceAlertsView.as_view(), name='resource_alerts'),
]
