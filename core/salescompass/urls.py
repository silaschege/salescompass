"""
URL configuration for salescompass project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('', include('core.urls')),
    path('system/', include('core.system_urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('portal/', include('customer_portal.urls')),
    
    path('sales/',include('sales.urls')),
    path('leads/', include('leads.urls')),
    path('products/', include('products.urls')),
    path('opportunities/', include('opportunities.urls')),
    path('proposals/', include('proposals.urls')),
    path('cases/', include('cases.urls')),
    path('engagement/', include('engagement.urls')),
    path('nps/', include('nps.urls')),
    path('marketing/', include('marketing.urls')),
    path('reports/', include('reports.urls')),
    path('automation/', include('automation.urls')),
    path('settings/', include('settings_app.urls')),
    path('learn/', include('learn.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('tenants/', include('tenants.urls')),
    path('billing/', include('billing.urls')),
    path('tasks/', include('tasks.urls')),
    path('commissions/', include('commissions.urls')),
    path('inventory/', include('inventory.urls')),
    path('pos/', include('pos.urls')),
    path('communication/', include('communication.urls')),
    path('projects/', include('projects.urls')),
    path('manufacturing/', include('manufacturing.urls')),
    path('logistics/', include('logistics.urls')),
    path('quality-control/', include('quality_control.urls')),
    path('developer/', include('developer.urls')),
    
      # Access Control
    path('access-control/', include('access_control.urls')),
    
    # Control Plane Apps
    path('infrastructure/', include('infrastructure.urls')),
    path('audit-logs/', include('audit_logs.urls')),
    path('feature-flags/', include('feature_flags.urls')),
    path('global-alerts/', include('global_alerts.urls')),
    
    # Finance & Commerce
    path('accounting/', include('accounting.urls')),
    path('purchasing/', include('purchasing.urls')),
    path('loyalty/', include('loyalty.urls')),
    path('expenses/', include('expenses.urls')),
    path('hr/', include('hr.urls')),
    path('assets/', include('assets.urls')),
    path('ecommerce/', include('ecommerce.urls')),

    # Telephony Integration
    path('wazo/', include('wazo.urls')),
    
    # Legacy URLs (Compatibility)
    path('legacy/communication/', include('communication.urls_legacy')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns += staticfiles_urlpatterns()