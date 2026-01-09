from django.urls import path
from . import views, lifecycle_views

app_name = 'tenants'

urlpatterns = [
    # Existing URLs
    path('', views.TenantListView.as_view(), name='tenant_list'),
    path('create/', views.TenantCreateView.as_view(), name='create'),
    path('search/', views.TenantSearchView.as_view(), name='search'),
    path('plan-selection/', views.PlanSelectionView.as_view(), name='plan_selection'),
    path('provision/<int:plan_id>/', views.ProvisioningView.as_view(), name='provision'),
    path('provision/new/', views.SuperuserProvisionView.as_view(), name='provision_new'),
    path('provision-tenant/', views.ProvisionTenantView.as_view(), name='provision_tenant'),
    path('subdomain-assignment/', views.SubdomainAssignmentView.as_view(), name='subdomain_assignment'),
    path('database-initialization/', views.DatabaseInitializationView.as_view(), name='database_initialization'),
    path('admin-user-setup/', views.AdminUserSetupView.as_view(), name='admin_user_setup'),
    
    # Onboarding Wizard URLs
    path('signup/wizard/', views.OnboardingSignupView.as_view(), name='onboarding_signup'),
    path('onboarding/', views.OnboardingWelcomeView.as_view(), name='onboarding_welcome'),
    path('onboarding/tenant-info/', views.OnboardingTenantInfoView.as_view(), name='onboarding_tenant_info'),
    path('onboarding/plan-selection/', views.OnboardingPlanSelectionView.as_view(), name='onboarding_plan_selection'),
    path('onboarding/subdomain/', views.OnboardingSubdomainView.as_view(), name='onboarding_subdomain'),
    path('onboarding/data-residency/', views.OnboardingDataResidencyView.as_view(), name='onboarding_data_residency'),
    path('onboarding/branding/', views.OnboardingBrandingView.as_view(), name='onboarding_branding'),
    path('onboarding/admin-setup/', views.OnboardingAdminSetupView.as_view(), name='onboarding_admin_setup'),
    path('onboarding/complete/', views.OnboardingCompleteView.as_view(), name='onboarding_complete'),
    
    # Data Export/Import URLs
    path('export/', views.TenantDataExportView.as_view(), name='data_export'),
    path('import/', views.TenantDataImportView.as_view(), name='data_import'),
    path('export/download/<str:format_type>/', views.TenantDataExportDownloadView.as_view(), name='data_export_download'),
    
    # Tenant Cloning URLs
    path('clone/', views.TenantCloneView.as_view(), name='clone_tenant'),
    path('clone/history/', views.TenantCloneHistoryView.as_view(), name='clone_history'),
    path('clone/status/<int:pk>/', views.TenantCloneStatusView.as_view(), name='clone_status'),
    
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

   
    # White-label Branding URLs
    path('white-label/', views.WhiteLabelSettingsView.as_view(), name='white_label_settings'),
    

    # Usage Metering URLs
    path('usage-metrics/', views.TenantUsageMetricsView.as_view(), name='usage_metrics'),
    path('usage-report/', views.TenantUsageReportView.as_view(), name='usage_report'),
    path('usage-alerts/', views.TenantUsageAlertsView.as_view(), name='usage_alerts'),
    

    # Feature Entitlements URLs
    path('feature-entitlements/', views.TenantFeatureEntitlementView.as_view(), name='feature_entitlements'),
    path('feature-entitlements/create/', views.TenantFeatureEntitlementCreateView.as_view(), name='feature_entitlement_create'),
    path('feature-entitlements/<int:pk>/edit/', views.TenantFeatureEntitlementUpdateView.as_view(), name='feature_entitlement_update'),
    path('feature-entitlements/<int:pk>/delete/', views.TenantFeatureEntitlementDeleteView.as_view(), name='feature_entitlement_delete'),
    path('feature-access-check/', views.TenantFeatureAccessCheckView.as_view(), name='feature_access_check'),
    path('bulk-feature-entitlement/', views.TenantBulkFeatureEntitlementView.as_view(), name='bulk_feature_entitlement'),
    

    # Overage Alerts and Notifications URLs
    path('overage-alerts/', views.OverageAlertListView.as_view(), name='overage_alerts'),
    path('overage-alerts/<int:pk>/resolve/', views.ResolveOverageAlertView.as_view(), name='resolve_alert'),
    path('alert-thresholds/', views.AlertThresholdListView.as_view(), name='alert_thresholds'),
    path('alert-thresholds/create/', views.AlertThresholdCreateView.as_view(), name='alert_threshold_create'),
    path('alert-thresholds/<int:pk>/edit/', views.AlertThresholdUpdateView.as_view(), name='alert_threshold_update'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/mark-read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    
    # Data Isolation Audit URLs
    path('data-isolation-audits/', views.TenantDataIsolationAuditListView.as_view(), name='data_isolation_audits'),
    path('data-isolation-audits/create/', views.TenantDataIsolationAuditCreateView.as_view(), name='data_isolation_audit_create'),
    path('data-isolation-audits/<int:pk>/', views.TenantDataIsolationAuditDetailView.as_view(), name='data_isolation_audit_detail'),
    path('data-isolation-violations/', views.TenantDataIsolationViolationListView.as_view(), name='data_isolation_violations'),
    path('data-isolation-violations/<int:pk>/update/', views.TenantDataIsolationViolationUpdateView.as_view(), name='data_isolation_violation_update'),
    path('run-data-isolation-audit/', views.RunDataIsolationAuditView.as_view(), name='run_data_isolation_audit'),
    
    # Member Management URLs
    path('members/', views.TenantMemberListView.as_view(), name='member_list'),
    path('members/create/', views.TenantMemberCreateView.as_view(), name='member_create'),
    path('members/<int:pk>/edit/', views.TenantMemberUpdateView.as_view(), name='member_update'),
    path('members/<int:pk>/delete/', views.TenantMemberDeleteView.as_view(), name='member_delete'),

]