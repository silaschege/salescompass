"""
API URLs for business metrics
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Business Metrics API
    path('metrics/clv/', views.clv_metrics_api, name='clv_metrics_api'),
    path('metrics/cac/', views.cac_metrics_api, name='cac_metrics_api'),
    path('metrics/sales-velocity/', views.sales_velocity_metrics_api, name='sales_velocity_metrics_api'),
    path('metrics/roi/', views.roi_metrics_api, name='roi_metrics_api'),
    path('metrics/conversion-funnel/', views.conversion_funnel_metrics_api, name='conversion_funnel_metrics_api'),
    path('metrics/trend/', views.metrics_trend_api, name='metrics_trend_api'),
    path('metrics/', views.BusinessMetricsAPIView.as_view(), name='business_metrics_api'),
]
