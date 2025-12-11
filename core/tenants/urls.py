from django.urls import path
from . import views, lifecycle_views

app_name = 'tenants'

urlpatterns = [
    # Existing URLs
    path('', views.TenantListView.as_view(), name='list'),
    path('create/', views.TenantCreateView.as_view(), name='create'),
    path('search/', views.TenantSearchView.as_view(), name='search'),
    path('plan-selection/', views.PlanSelectionView.as_view(), name='plan_selection'),
    path('provision/<int:plan_id>/', views.ProvisioningView.as_view(), name='provision'),
    path('provision-tenant/', views.ProvisionTenantView.as_view(), name='provision_tenant'),
    path('subdomain-assignment/', views.SubdomainAssignmentView.as_view(), name='subdomain_assignment'),
    path('database-initialization/', views.DatabaseInitializationView.as_view(), name='database_initialization'),
    path('admin-user-setup/', views.AdminUserSetupView.as_view(), name='admin_user_setup'),
    
    # Lifecycle Management URLs
    path('lifecycle/dashboard/', lifecycle_views.TenantLifecycleDashboardView.as_view(), name='lifecycle-dashboard'),
    path('lifecycle/status/', lifecycle_views.TenantStatusManagementView.as_view(), name='status-management'),
    path('lifecycle/suspend/', lifecycle_views.TenantSuspensionWorkflowView.as_view(), name='initiate-suspension'),
    path('lifecycle/suspension-workflows/', lifecycle_views.TenantSuspensionWorkflowView.as_view(), name='suspension-workflows'),
    path('lifecycle/terminate/', lifecycle_views.TenantTerminationWorkflowView.as_view(), name='initiate-termination'),
    path('lifecycle/termination-workflows/', lifecycle_views.TenantTerminationWorkflowView.as_view(), name='termination-workflows'),
    path('lifecycle/automated-rules/', lifecycle_views.AutomatedLifecycleRulesView.as_view(), name='automated-lifecycle-rules'),
    path('lifecycle/automated-rules/create/', lifecycle_views.CreateAutomatedLifecycleRuleView.as_view(), name='create-automated-rule'),
    path('lifecycle/automated-rules/execute/<int:rule_id>/', lifecycle_views.ExecuteLifecycleRuleView.as_view(), name='execute-automated-rule'),
    path('lifecycle/data-preservation/', lifecycle_views.TenantDataPreservationView.as_view(), name='data-preservation'),
    path('lifecycle/data-restoration/', lifecycle_views.TenantDataRestorationView.as_view(), name='data-restoration'),
    path('lifecycle/data-restoration/initiate/<int:preservation_id>/', lifecycle_views.TenantRestorationView.as_view(), name='initiate-restoration'),
    path('lifecycle/workflows/', lifecycle_views.TenantLifecycleWorkflowsView.as_view(), name='lifecycle-workflows'),
    path('lifecycle/workflows/approve-suspension/<int:workflow_id>/', lifecycle_views.ApproveSuspensionWorkflowView.as_view(), name='approve-suspension'),
    path('lifecycle/workflows/approve-termination/<int:workflow_id>/', lifecycle_views.ApproveTerminationWorkflowView.as_view(), name='approve-termination'),
    path('lifecycle/event-log/', lifecycle_views.TenantLifecycleEventLogView.as_view(), name='lifecycle-event-log'),
    
    # Existing lifecycle URLs
    path('suspend/<int:tenant_id>/', views.SuspendTenantView.as_view(), name='suspend'),
    path('archive/<int:tenant_id>/', views.ArchiveTenantView.as_view(), name='archive'),
    path('reactivate/<int:tenant_id>/', views.ReactivateTenantView.as_view(), name='reactivate'),
    path('delete/<int:tenant_id>/', views.DeleteTenantView.as_view(), name='delete'),
    
    # Module Entitlements URLs
    path('feature-toggles/', views.FeatureTogglesView.as_view(), name='feature_toggles'),
    path('usage-limits/', views.UsageLimitsView.as_view(), name='usage_limits'),
    path('entitlement-templates/', views.EntitlementTemplatesView.as_view(), name='entitlement_templates'),
    
    # Domain & Branding URLs
    path('domain-management/', views.DomainManagementListView.as_view(), name='domain_management_list'),
    path('domain-management/<int:tenant_id>/', views.DomainManagementView.as_view(), name='domain_management'),
    path('ssl-certificates/', views.SSLCertificatesView.as_view(), name='ssl_certificates'),
    path('branding-config/', views.BrandingConfigListView.as_view(), name='branding_config_list'),
    path('branding-config/<int:tenant_id>/', views.BrandingConfigView.as_view(), name='branding_config'),
    path('logo-management/', views.LogoManagementView.as_view(), name='logo_management'),
    
    # Billing Oversight URLs
    path('subscription-overview/', views.SubscriptionOverviewView.as_view(), name='subscription_overview'),
    path('revenue-analytics/', views.RevenueAnalyticsView.as_view(), name='revenue_analytics'),
]
