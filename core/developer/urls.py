from django.urls import path
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView,SpectacularRedocView

app_name = 'developer'

urlpatterns = [
    # Regular views
    path('', views.dashboard, name='dashboard'),
    path('portal/', views.portal, name='portal'),
    path('api-keys/', views.api_keys, name='api_keys'),
    path('webhooks/', views.webhooks, name='webhooks'),
    path('analytics/', views.usage_analytics, name='analytics'),
    path('generate-key/', views.generate_api_key, name='generate_key'),
    path('test-webhook/', views.test_webhook, name='test_webhook'),
    
    # API documentation specific to Developer Module
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='developer:schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='developer:schema'), name='redoc'),
    
    
    # API Explorer
    path('api/explorer/', views.api_explorer, name='api_explorer'),
    path('documentation/', views.documentation, name='documentation'),
        # Monitoring URLs

        # Monitoring URLs
    path('monitoring/', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('api/usage-chart/', views.api_usage_chart, name='api_usage_chart'),
    path('api/webhook-stats-chart/', views.webhook_stats_chart, name='webhook_stats_chart'),
    path('quota-alerts/', views.quota_alerts, name='quota_alerts'),
]
