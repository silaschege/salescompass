from django.db import models
from django.utils import timezone
from core.models import User
from tenants.models import Tenant


class AuditLog(models.Model):
    """Model for tracking audit logs for all system activities"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_change', 'Permission Change'),
        ('configuration_change', 'Configuration Change'),
        ('data_export', 'Data Export'),
        ('data_import', 'Data Import'),
        ('file_upload', 'File Upload'),
        ('file_download', 'File Download'),
        ('api_call', 'API Call'),
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
        ('security_event', 'Security Event'),
    ]
    
    RESOURCE_TYPE_CHOICES = [
        ('user', 'User'),
        ('account', 'Account'),
        ('lead', 'Lead'),
        ('opportunity', 'Opportunity'),
        ('case', 'Case'),
        ('deal', 'Deal'),
        ('document', 'Document'),
        ('setting', 'Setting'),
        ('permission', 'Permission'),
        ('role', 'Role'),
        ('tenant', 'Tenant'),
        ('automation', 'Automation'),
        ('workflow', 'Workflow'),
        ('api_key', 'API Key'),
        ('webhook', 'Webhook'),
        ('integration', 'Integration'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='tenant_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, help_text="Type of action performed")
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES, help_text="Type of resource accessed/modified")
    resource_id = models.CharField(max_length=100, help_text="ID of the resource accessed/modified")
    resource_name = models.CharField(max_length=255, help_text="Name of the resource accessed/modified")
    old_values = models.JSONField(default=dict, blank=True, help_text="Old values before the change (for update/delete actions)")
    new_values = models.JSONField(default=dict, blank=True, help_text="New values after the change (for create/update actions)")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the user")
    user_agent = models.TextField(blank=True, help_text="User agent string of the client")
    is_successful = models.BooleanField(default=True, help_text="Whether the action was successful")
    error_message = models.TextField(blank=True, help_text="Error message if the action failed")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the action")
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='info', help_text="Severity level of the audit log")
    audit_log_created_at = models.DateTimeField(auto_now_add=True)
    audit_log_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-audit_log_created_at']
        indexes = [
            models.Index(fields=['user', 'audit_log_created_at']),
            models.Index(fields=['action', 'audit_log_created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['tenant_id', 'audit_log_created_at']),
        ]
    
    def __str__(self):
        user_email = self.user.email if self.user else 'System'
        return f"{self.action.upper()} {self.resource_type} '{self.resource_name}' by {user_email}"

    @property
    def created_at(self):
        return self.audit_log_created_at

    @created_at.setter
    def created_at(self, value):
        self.audit_log_created_at = value

    @property
    def action_type(self):
        return self.action

    @action_type.setter
    def action_type(self, value):
        self.action = value


class ComplianceAuditTrail(models.Model):
    """Model for specific compliance-related audit events"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_audits')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='compliance_audits')
    compliance_standard = models.CharField(max_length=100, choices=[
        ('gdpr', 'GDPR'),
        ('hipaa', 'HIPAA'),
        ('soc2', 'SOC2'),
        ('iso27001', 'ISO 27001'),
        ('pci_dss', 'PCI DSS'),
        ('sox', 'SOX'),
        ('ccpa', 'CCPA'),
        ('ferpa', 'FERPA'),
        ('coppa', 'COPPA'),
    ])
    audit_type = models.CharField(max_length=100, choices=[
        ('access_audit', 'Access Audit'),
        ('data_processing_audit', 'Data Processing Audit'),
        ('consent_audit', 'Consent Audit'),
        ('data_retention_audit', 'Data Retention Audit'),
        ('data_deletion_audit', 'Data Deletion Audit'),
        ('privacy_policy_audit', 'Privacy Policy Audit'),
        ('security_control_audit', 'Security Control Audit'),
        ('incident_response_audit', 'Incident Response Audit'),
    ])
    resource_type = models.CharField(max_length=100, help_text="Type of resource audited")
    resource_id = models.CharField(max_length=100, help_text="ID of the resource audited")
    action = models.CharField(max_length=100, help_text="Action performed during audit")
    details = models.JSONField(default=dict, blank=True, help_text="Additional audit details")
    status = models.CharField(max_length=20, choices=[
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
        ('not_applicable', 'Not Applicable'),
    ])
    finding_description = models.TextField(blank=True, help_text="Description of any findings")
    remediation_required = models.BooleanField(default=False, help_text="Whether remediation is required")
    remediation_deadline = models.DateTimeField(null=True, blank=True, help_text="Deadline for remediation")
    evidence = models.TextField(blank=True, help_text="Evidence supporting the audit finding")
    timestamp = models.DateTimeField(default=timezone.now)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_audits_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Compliance Audit Trail"
        verbose_name_plural = "Compliance Audit Trails"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.compliance_standard} - {self.audit_type} for {self.resource_type} - {self.status}"


class SecurityIncident(models.Model):
    """Model for tracking security-related incidents"""
    id = models.AutoField(primary_key=True)
    incident_type = models.CharField(max_length=100, choices=[
        ('unauthorized_access', 'Unauthorized Access'),
        ('data_breach', 'Data Breach'),
        ('malware_detected', 'Malware Detected'),
        ('phishing_attempt', 'Phishing Attempt'),
        ('denial_of_service', 'Denial of Service'),
        ('credential_compromise', 'Credential Compromise'),
        ('privilege_escalation', 'Privilege Escalation'),
        ('sql_injection', 'SQL Injection'),
        ('cross_site_scripting', 'Cross-Site Scripting'),
        ('man_in_the_middle', 'Man-in-the-Middle Attack'),
        ('social_engineering', 'Social Engineering'),
        ('physical_security_breach', 'Physical Security Breach'),
        ('network_intrusion', 'Network Intrusion'),
        ('vulnerability_exploitation', 'Vulnerability Exploitation'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    title = models.CharField(max_length=255)
    description = models.TextField()
    affected_users = models.ManyToManyField(User, blank=True, related_name='security_incidents_affected')
    affected_tenants = models.ManyToManyField(Tenant, blank=True, related_name='security_incidents_affected')
    impacted_resources = models.TextField(help_text="List of impacted system resources")
    detection_timestamp = models.DateTimeField(default=timezone.now)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents_reported')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents_assigned')
    status = models.CharField(max_length=20, choices=[
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('containment', 'Containment'),
        ('eradication', 'Eradication'),
        ('recovery', 'Recovery'),
        ('closed', 'Closed'),
        ('false_positive', 'False Positive'),
    ], default='reported')
    classification = models.CharField(max_length=50, choices=[
        ('confirmed', 'Confirmed'),
        ('potential', 'Potential'),
        ('benign', 'Benign'),
        ('false_positive', 'False Positive'),
    ], default='potential')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    escalation_level = models.IntegerField(default=1)
    resolution_notes = models.TextField(blank=True)
    resolution_timestamp = models.DateTimeField(null=True, blank=True)
    remediation_steps = models.TextField(blank=True, help_text="Steps taken to remediate the incident")
    lessons_learned = models.TextField(blank=True, help_text="Lessons learned from the incident")
    is_public_disclosure_required = models.BooleanField(default=False, help_text="Whether public disclosure is required")
    disclosure_timestamp = models.DateTimeField(null=True, blank=True)
    disclosure_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Security Incident"
        verbose_name_plural = "Security Incidents"
        ordering = ['-detection_timestamp']
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.title} - {self.status}"


class AccessPatternAnalysis(models.Model):
    """Model for storing access pattern analytics"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_patterns')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='access_patterns')
    pattern_type = models.CharField(max_length=100, choices=[
        ('normal_access', 'Normal Access'),
        ('anomalous_access', 'Anomalous Access'),
        ('off_hours_access', 'Off-Hours Access'),
        ('multiple_failures', 'Multiple Failures'),
        ('privilege_escalation', 'Privilege Escalation'),
        ('data_extraction', 'Data Extraction'),
        ('location_anomaly', 'Location Anomaly'),
        ('device_anomaly', 'Device Anomaly'),
        ('resource_anomaly', 'Resource Anomaly'),
    ])
    risk_score = models.FloatField(default=0.0, help_text="Risk score calculated for this pattern")
    confidence_level = models.FloatField(default=0.0, help_text="Confidence level in the analysis")
    analysis_details = models.JSONField(default=dict, blank=True, help_text="Detailed analysis results")
    detected_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='access_patterns_reviewed')
    status = models.CharField(max_length=20, choices=[
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('confirmed', 'Confirmed'),
        ('false_positive', 'False Positive'),
        ('resolved', 'Resolved'),
    ], default='new')
    action_taken = models.TextField(blank=True, help_text="Action taken in response to the pattern")
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Access Pattern Analysis"
        verbose_name_plural = "Access Pattern Analyses"
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"{self.pattern_type} for {self.user.email} - Risk: {self.risk_score}"


class AnomalyDetectionResult(models.Model):
    """Model for recording anomaly detection findings"""
    id = models.AutoField(primary_key=True)
    detection_algorithm = models.CharField(max_length=100, help_text="Algorithm used for anomaly detection")
    resource_type = models.CharField(max_length=100, choices=[
        ('user', 'User'),
        ('account', 'Account'),
        ('api_call', 'API Call'),
        ('data_access', 'Data Access'),
        ('login', 'Login'),
        ('file_operation', 'File Operation'),
        ('permission_change', 'Permission Change'),
        ('configuration_change', 'Configuration Change'),
    ])
    resource_id = models.CharField(max_length=100, help_text="ID of the resource being monitored")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='anomaly_detections')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='anomaly_detections')
    anomaly_type = models.CharField(max_length=100, choices=[
        ('behavioral', 'Behavioral'),
        ('temporal', 'Temporal'),
        ('spatial', 'Spatial'),
        ('volume', 'Volume'),
        ('frequency', 'Frequency'),
        ('pattern', 'Pattern'),
        ('correlation', 'Correlation'),
    ])
    anomaly_score = models.FloatField(help_text="Score indicating the degree of anomaly")
    threshold = models.FloatField(help_text="Threshold for determining anomaly")
    confidence = models.FloatField(default=0.0, help_text="Confidence level in the detection")
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    description = models.TextField(help_text="Description of the detected anomaly")
    detected_at = models.DateTimeField(default=timezone.now)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    analyzed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='anomaly_analysis_performed')
    is_true_anomaly = models.BooleanField(null=True, blank=True, help_text="Whether this is confirmed as a true anomaly")
    verification_notes = models.TextField(blank=True, help_text="Notes about verification process")
    action_required = models.TextField(blank=True, help_text="Recommended action for the anomaly")
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ], default='pending')
    related_events = models.JSONField(default=list, blank=True, help_text="Related events that may be connected")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata for the detection")
    
    class Meta:
        verbose_name = "Anomaly Detection Result"
        verbose_name_plural = "Anomaly Detection Results"
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"{self.anomaly_type} detected in {self.resource_type} {self.resource_id} - Score: {self.anomaly_score}"


class AuditReport(models.Model):
    """Model for managing audit reports and findings"""
    id = models.AutoField(primary_key=True)
    report_type = models.CharField(max_length=100, choices=[
        ('compliance', 'Compliance Report'),
        ('security', 'Security Report'),
        ('access', 'Access Report'),
        ('data_privacy', 'Data Privacy Report'),
        ('system_integrity', 'System Integrity Report'),
        ('user_activity', 'User Activity Report'),
        ('configuration', 'Configuration Report'),
        ('performance', 'Performance Report'),
    ])
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_reports_generated')
    generated_at = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_reports')
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('published', 'Published'),
    ], default='draft')
    findings_count = models.IntegerField(default=0, help_text="Number of findings in the report")
    high_risk_findings = models.IntegerField(default=0, help_text="Number of high-risk findings")
    medium_risk_findings = models.IntegerField(default=0, help_text="Number of medium-risk findings")
    low_risk_findings = models.IntegerField(default=0, help_text="Number of low-risk findings")
    recommendations_count = models.IntegerField(default=0, help_text="Number of recommendations in the report")
    executive_summary = models.TextField(blank=True, help_text="Executive summary of the report")
    detailed_findings = models.TextField(blank=True, help_text="Detailed findings section")
    recommendations = models.TextField(blank=True, help_text="Recommendations section")
    conclusion = models.TextField(blank=True, help_text="Conclusion of the report")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    report_file_path = models.TextField(blank=True, help_text="Path to the generated report file")
    report_metadata = models.JSONField(default=dict, blank=True, help_text="Metadata about the report")
    distribution_list = models.TextField(blank=True, help_text="List of people the report was distributed to")
    retention_period_days = models.IntegerField(default=365, help_text="How long to retain the report")
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Audit Report"
        verbose_name_plural = "Audit Reports"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_type} - {self.title} ({self.start_date.date()} to {self.end_date.date()})"
