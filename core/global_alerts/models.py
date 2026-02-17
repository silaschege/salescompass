from django.db import models
from django.utils import timezone
from core.models import User
from tenants.models import Tenant


class Alert(Tenant):
    """
    Global alert system for broadcasting important messages to users
    """
    SEVERITY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('system', 'System'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('feature', 'Feature'),
        ('announcement', 'Announcement'),
        ('emergency', 'Emergency'),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    
    is_global = models.BooleanField(default=True, help_text="Show alert to all users or specific tenants")
    target_tenant_ids = models.JSONField(default=list, blank=True, help_text="List of tenant IDs if not global")
    
    is_dismissible = models.BooleanField(default=True, help_text="Can users dismiss this alert?")
    show_on_all_pages = models.BooleanField(default=True, help_text="Show on all pages or specific sections")
    alert_is_active = models.BooleanField(default=True)
    
    alert_created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts_created')
    alert_created_at = models.DateTimeField(auto_now_add=True)
    alert_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Global Alert"
        verbose_name_plural = "Global Alerts"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AlertConfiguration(models.Model):
    """Model for configuring system-wide alerts"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the alert configuration")
    description = models.TextField(blank=True, help_text="Description of what this alert monitors")
    is_active = models.BooleanField(default=True, help_text="Whether this alert configuration is active")
    alert_type = models.CharField(max_length=100, choices=[
        ('system_performance', 'System Performance'),
        ('security_incident', 'Security Incident'),
        ('availability', 'Availability'),
        ('capacity', 'Capacity'),
        ('data_integrity', 'Data Integrity'),
        ('compliance', 'Compliance'),
        ('business_metric', 'Business Metric'),
        ('custom', 'Custom Alert'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='warning')
    condition = models.JSONField(default=dict, blank=True, help_text="Condition that triggers the alert")
    evaluation_frequency = models.CharField(max_length=20, choices=[
        ('real_time', 'Real Time'),
        ('minute', 'Every Minute'),
        ('five_minutes', 'Every 5 Minutes'),
        ('fifteen_minutes', 'Every 15 Minutes'),
        ('thirty_minutes', 'Every 30 Minutes'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
    ], default='five_minutes')
    notification_channels = models.JSONField(default=list, blank=True, help_text="Channels to send notifications to")
    escalation_policy = models.JSONField(default=dict, blank=True, help_text="How to escalate the alert")
    alert_recipients = models.JSONField(default=list, blank=True, help_text="List of email addresses to alert")
    tenant_filter = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='alert_configurations')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alert_configs_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_evaluated = models.DateTimeField(null=True, blank=True, help_text="Last time the alert was evaluated")
    last_triggered = models.DateTimeField(null=True, blank=True, help_text="Last time the alert was triggered")
    trigger_count = models.IntegerField(default=0, help_text="Number of times this alert has been triggered")
    cooldown_period_minutes = models.IntegerField(default=15, help_text="Minimum time between alert triggers in minutes")
    suppression_rules = models.JSONField(default=list, blank=True, help_text="Rules to suppress this alert")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing alerts")
    notes = models.TextField(blank=True, help_text="Internal notes about this alert configuration")
    
    class Meta:
        verbose_name = "Alert Configuration"
        verbose_name_plural = "Alert Configurations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.severity.upper()}"


class AlertInstance(models.Model):
    """Model for individual alert instances"""
    id = models.AutoField(primary_key=True)
    alert_config = models.ForeignKey(AlertConfiguration, on_delete=models.CASCADE, related_name='instances')
    title = models.CharField(max_length=255, help_text="Title of the alert instance")
    description = models.TextField(help_text="Detailed description of the alert")
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('triggered', 'Triggered'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('suppressed', 'Suppressed'),
    ], default='triggered')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ], default='medium')
    source = models.CharField(max_length=100, help_text="Source of the alert (e.g., monitoring system, service)")
    resource_type = models.CharField(max_length=100, help_text="Type of resource that triggered the alert")
    resource_id = models.CharField(max_length=100, help_text="ID of the resource that triggered the alert")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts_triggered')
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts_acknowledged')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts_resolved')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    triggered_at = models.DateTimeField(default=timezone.now)
    details = models.JSONField(default=dict, blank=True, help_text="Additional details about the alert")
    related_alerts = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='related_to')
    escalation_level = models.IntegerField(default=1, help_text="Current escalation level")
    escalation_reason = models.TextField(blank=True, help_text="Reason for escalation")
    is_duplicate = models.BooleanField(default=False, help_text="Whether this is a duplicate of another alert")
    duplicate_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')
    suppression_reason = models.TextField(blank=True, help_text="Reason if the alert was suppressed")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing alerts")
    notes = models.TextField(blank=True, help_text="Internal notes about this alert")
    
    class Meta:
        verbose_name = "Alert Instance"
        verbose_name_plural = "Alert Instances"
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.title} - {self.severity.upper()} - {self.status}"


class AlertEscalationPolicy(models.Model):
    """Model for managing alert escalation policies"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the escalation policy")
    description = models.TextField(blank=True, help_text="Description of the escalation policy")
    is_active = models.BooleanField(default=True, help_text="Whether this escalation policy is active")
    steps = models.JSONField(default=list, blank=True, help_text="List of escalation steps")
    time_threshold_minutes = models.IntegerField(default=30, help_text="Time threshold to trigger next escalation step")
    repeat_interval_minutes = models.IntegerField(default=60, help_text="Interval to repeat escalation if unresolved")
    max_escalation_levels = models.IntegerField(default=5, help_text="Maximum number of escalation levels")
    notification_channels = models.JSONField(default=list, blank=True, help_text="Channels to notify during escalation")
    escalation_recipients = models.JSONField(default=list, blank=True, help_text="Recipients for escalation notifications")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalation_policies_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True, help_text="Last time this policy was used")
    usage_count = models.IntegerField(default=0, help_text="Number of times this policy was used")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing escalation policies")
    notes = models.TextField(blank=True, help_text="Internal notes about this policy")
    
    class Meta:
        verbose_name = "Alert Escalation Policy"
        verbose_name_plural = "Alert Escalation Policies"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.max_escalation_levels} levels"


class AlertNotification(models.Model):
    """Model for tracking alert notifications"""
    id = models.AutoField(primary_key=True)
    alert_instance = models.ForeignKey(AlertInstance, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('microsoft_teams', 'Microsoft Teams'),
        ('pagerduty', 'PagerDuty'),
        ('custom', 'Custom Channel'),
    ])
    recipient = models.CharField(max_length=255, help_text="Recipient of the notification (email, phone number, etc.)")
    recipient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alert_notifications_received')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
    ], default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text="Error message if notification failed")
    response_code = models.IntegerField(null=True, blank=True, help_text="Response code from the notification service")
    response_message = models.TextField(blank=True, help_text="Response message from the notification service")
    retry_count = models.IntegerField(default=0, help_text="Number of retry attempts")
    escalation_level = models.IntegerField(default=1, help_text="Escalation level of this notification")
    is_escalated = models.BooleanField(default=False, help_text="Whether this notification was escalated")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='alert_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notification_content = models.TextField(help_text="Content of the notification sent")
    notification_metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the notification")
    
    class Meta:
        verbose_name = "Alert Notification"
        verbose_name_plural = "Alert Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.alert_instance.title} - {self.status}"


class AlertCorrelationRule(models.Model):
    """Model for defining rules to correlate related alerts"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the correlation rule")
    description = models.TextField(blank=True, help_text="Description of the correlation rule")
    is_active = models.BooleanField(default=True, help_text="Whether this correlation rule is active")
    rule_type = models.CharField(max_length=50, choices=[
        ('time_proximity', 'Time Proximity'),
        ('resource_similarity', 'Resource Similarity'),
        ('pattern_matching', 'Pattern Matching'),
        ('dependency_based', 'Dependency Based'),
        ('custom_logic', 'Custom Logic'),
    ])
    conditions = models.JSONField(default=dict, blank=True, help_text="Conditions for correlating alerts")
    correlation_window_minutes = models.IntegerField(default=60, help_text="Time window for correlation in minutes")
    max_correlated_alerts = models.IntegerField(default=10, help_text="Maximum number of alerts to correlate")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='correlation_rules_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_evaluation = models.DateTimeField(null=True, blank=True, help_text="Last time this rule was evaluated")
    correlation_count = models.IntegerField(default=0, help_text="Number of correlations made by this rule")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing correlation rules")
    notes = models.TextField(blank=True, help_text="Internal notes about this rule")
    
    class Meta:
        verbose_name = "Alert Correlation Rule"
        verbose_name_plural = "Alert Correlation Rules"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.rule_type}"
