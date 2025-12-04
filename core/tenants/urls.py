from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Core tenant management
    path('list/', views.TenantListView.as_view(), name='list'),
    path('create/', views.TenantCreateView.as_view(), name='create'),
    path('search/', views.TenantSearchView.as_view(), name='search'),
    path('plan-selection/', views.PlanSelectionView.as_view(), name='plan_selection'),
    path('provision/<int:plan_id>/', views.ProvisioningView.as_view(), name='provision'),
    
    # Provisioning & Onboarding
    path('provision-tenant/', views.ProvisionTenantView.as_view(), name='provision_tenant'),
    path('subdomain-assignment/', views.SubdomainAssignmentView.as_view(), name='subdomain_assignment'),
    path('database-initialization/', views.DatabaseInitializationView.as_view(), name='database_initialization'),
    path('admin-user-setup/', views.AdminUserSetupView.as_view(), name='admin_user_setup'),
    
    # Lifecycle Management
    path('<uuid:tenant_id>/suspend/', views.SuspendTenantView.as_view(), name='suspend_tenant'),
    path('<uuid:tenant_id>/archive/', views.ArchiveTenantView.as_view(), name='archive_tenant'),
    path('<uuid:tenant_id>/reactivate/', views.ReactivateTenantView.as_view(), name='reactivate_tenant'),
    path('<uuid:tenant_id>/delete/', views.DeleteTenantView.as_view(), name='delete_tenant'),
    
    # Module Entitlements
    path('feature-toggles/', views.FeatureTogglesView.as_view(), name='feature_toggles'),
    path('usage-limits/', views.UsageLimitsView.as_view(), name='usage_limits'),
    path('entitlement-templates/', views.EntitlementTemplatesView.as_view(), name='entitlement_templates'),
    
    # Domain & Branding
    path('domain-management/', views.DomainManagementListView.as_view(), name='domain_management'),
    path('<uuid:tenant_id>/domain/', views.DomainManagementView.as_view(), name='domain_management_detail'),
    path('ssl-certificates/', views.SSLCertificatesView.as_view(), name='ssl_certificates'),
    path('branding-config/', views.BrandingConfigListView.as_view(), name='branding_config'),
    path('<uuid:tenant_id>/branding/', views.BrandingConfigView.as_view(), name='branding_config_detail'),
    path('logo-management/', views.LogoManagementView.as_view(), name='logo_management'),
    
    # Billing Oversight
    path('subscription-overview/', views.SubscriptionOverviewView.as_view(), name='subscription_overview'),
    path('revenue-analytics/', views.RevenueAnalyticsView.as_view(), name='revenue_analytics'),
]

