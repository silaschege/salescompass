from django.urls import path
from . import views

app_name = 'developer'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('portal/', views.portal, name='portal'),
    path('api-keys/', views.api_keys, name='api_keys'),
    path('webhooks/', views.webhooks, name='webhooks'),
    path('analytics/', views.usage_analytics, name='analytics'),
    path('generate-key/', views.generate_api_key, name='generate_key'),
    path('test-webhook/', views.test_webhook, name='test_webhook'),
]
