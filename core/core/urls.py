from django.urls import path, include
from . import views
from dashboard import views as dashboard_views

from django.views.generic import TemplateView

from accounts.views import CustomLoginView


from core import dynamic_choices_views
app_name = 'core'

 
urlpatterns = [
    # Landing Page
    path('', views.home, name='home'),

    # Public Pages
    path('product-tour/', TemplateView.as_view(template_name='public/products.html'), name='product_public'),

    path('solutions/', TemplateView.as_view(template_name='public/solutions.html'), name='solutions'),
    path('pricing/', TemplateView.as_view(template_name='public/pricing.html'), name='pricing'),
    path('customers/', TemplateView.as_view(template_name='public/customer.html'), name='customers'),
    path('company/', TemplateView.as_view(template_name='public/company.html'), name='company'),
    path('support/', TemplateView.as_view(template_name='public/support.html'), name='support'),
    path('try/', TemplateView.as_view(template_name='public/try.html'), name='try_free'),
    path('integrations/', TemplateView.as_view(template_name='public/integrations.html'), name='integrations'),
    path('api-docs/', TemplateView.as_view(template_name='public/api.html'), name='api_docs'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('apps/', views.AppSelectionView.as_view(), name='app_selection'),
    path('apps/settings/', views.AppSettingsView.as_view(), name='app_settings'),

    # Admin URLs
    path('', include('core.admin_urls')),
    path('', include('core.security_urls')),

    # CLV Dashboard
    path('clv-dashboard/', views.clv_dashboard, name='clv_dashboard'),
    
    # Add other existing URLs for core
    # (Note: The actual existing URLs would need to be added based on the original file)

    # Add other existing URLs for core
    # (Note: The actual existing URLs would need to be added based on the original file)
]
