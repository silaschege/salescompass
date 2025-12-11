from django.urls import path
from . import security_views

app_name = 'core'

urlpatterns = [
    # Security Views
    path('admin/security-dashboard/', security_views.SecurityDashboardView.as_view(), name='security_dashboard'),
    path('admin/ip-whitelist/', security_views.IPWhitelistManagementView.as_view(), name='ip_whitelist_management'),
    path('admin/security-events/', security_views.SecurityEventMonitoringView.as_view(), name='security_event_monitoring'),
    path('admin/intrusion-detection/', security_views.IntrusionDetectionView.as_view(), name='intrusion_detection'),
    path('admin/secure-credentials/', security_views.SecureCredentialManagementView.as_view(), name='secure_credential_management'),
    path('admin/compliance-dashboard/', security_views.ComplianceDashboardView.as_view(), name='compliance_dashboard'),
    path('admin/data-privacy/', security_views.DataPrivacyManagementView.as_view(), name='data_privacy_management'),
    path('admin/security-policies/', security_views.SecurityPolicyManagementView.as_view(), name='security_policy_management'),
    path('admin/vulnerability-management/', security_views.VulnerabilityManagementView.as_view(), name='vulnerability_management'),
]
