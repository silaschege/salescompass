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
    # Setting URLs
    path('settings/', views.SettingListView.as_view(), name='setting_list'),
    path('settings/create/', views.SettingCreateView.as_view(), name='setting_create'),
    path('settings/<int:pk>/edit/', views.SettingUpdateView.as_view(), name='setting_edit'),
    path('settings/<int:pk>/delete/', views.SettingDeleteView.as_view(), name='setting_delete'),

    # Setting Group URLs
    path('setting-groups/', views.SettingGroupListView.as_view(), name='setting_group_list'),
    path('setting-groups/create/', views.SettingGroupCreateView.as_view(), name='setting_group_create'),
    path('setting-groups/<int:pk>/edit/', views.SettingGroupUpdateView.as_view(), name='setting_group_edit'),
    path('setting-groups/<int:pk>/delete/', views.SettingGroupDeleteView.as_view(), name='setting_group_delete'),

    # Setting Type URLs
    path('setting-types/', views.SettingTypeListView.as_view(), name='setting_type_list'),
    path('setting-types/create/', views.SettingTypeCreateView.as_view(), name='setting_type_create'),
    path('setting-types/<int:pk>/edit/', views.SettingTypeUpdateView.as_view(), name='setting_type_edit'),
    path('setting-types/<int:pk>/delete/', views.SettingTypeDeleteView.as_view(), name='setting_type_delete'),

]

