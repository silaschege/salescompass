from django.db import models
from django.utils import timezone
from core.models import User
from tenants.models import Tenant


class SystemHealthCheck(models.Model):
    """Model for system health checks"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the health check")
    description = models.TextField(blank=True, help_text="Description of what is being checked")
    check_type = models.CharField(max_length=100, choices=[
        ('database', 'Database Connection'),
        ('cache', 'Cache Health'),
        ('storage', 'Storage Space'),
        ('network', 'Network Connectivity'),
        ('api', 'API Response Time'),
        ('memory', 'Memory Usage'),
        ('cpu', 'CPU Usage'),
        ('disk_io', 'Disk I/O'),
        ('process', 'Process Health'),
        ('service', 'Service Availability'),
        ('third_party', 'Third Party Service'),
    ])
    endpoint_url = models.URLField(blank=True, help_text="URL to check for API/service health")
    timeout_seconds = models.IntegerField(default=30, help_text="Timeout for the health check in seconds")
    is_active = models.BooleanField(default=True, help_text="Whether this health check is active")
    interval_seconds = models.IntegerField(default=300, help_text="How often to run the check in seconds")
    expected_response_time_ms = models.IntegerField(default=1000, help_text="Expected maximum response time in milliseconds")
    failure_threshold = models.IntegerField(default=3, help_text="Number of consecutive failures before alerting")
    consecutive_failure_count = models.IntegerField(default=0, help_text="Current count of consecutive failures")
    last_check = models.DateTimeField(null=True, blank=True, help_text="Last time the check was run")
    last_status = models.CharField(max_length=20, choices=[
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='healthy')
    last_response_time_ms = models.FloatField(null=True, blank=True, help_text="Last response time in milliseconds")
    last_error = models.TextField(blank=True, help_text="Last error message if any")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='health_checks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='health_checks_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    alert_recipients = models.JSONField(default=list, blank=True, help_text="List of email addresses to alert on failure")
    recovery_notifications = models.BooleanField(default=True, help_text="Whether to send notifications when recovering from failure")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing health checks")
    notes = models.TextField(blank=True, help_text="Internal notes about this health check")
    
    class Meta:
        verbose_name = "System Health Check"
        verbose_name_plural = "System Health Checks"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.last_status.upper()}"


class LogAggregation(models.Model):
    """Model for log aggregation and analysis"""
    id = models.AutoField(primary_key=True)
    log_source = models.CharField(max_length=255, help_text="Source of the logs (e.g., application, database, system)")
    log_level = models.CharField(max_length=20, choices=[
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ])
    message = models.TextField(help_text="Log message content")
    details = models.JSONField(default=dict, blank=True, help_text="Additional structured details")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address associated with the log")
    user_agent = models.TextField(blank=True, help_text="User agent string")
    session_id = models.CharField(max_length=100, blank=True, help_text="Session ID associated with the log")
    request_url = models.URLField(max_length=500, blank=True, help_text="URL of the request that generated the log")
    response_status = models.IntegerField(null=True, blank=True, help_text="HTTP response status code")
    execution_time_ms = models.FloatField(null=True, blank=True, help_text="Execution time in milliseconds")
    severity_score = models.FloatField(default=0.0, help_text="Calculated severity score (0-10)")
    is_processed = models.BooleanField(default=False, help_text="Whether this log has been processed for analysis")
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When this log was processed")
    is_alert_trigger = models.BooleanField(default=False, help_text="Whether this log triggered an alert")
    correlation_id = models.CharField(max_length=100, blank=True, help_text="Correlation ID for tracing requests")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing logs")
    
    class Meta:
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['log_level']),
            models.Index(fields=['tenant']),
            models.Index(fields=['log_source']),
            models.Index(fields=['timestamp', 'log_level']),
        ]
    
    def __str__(self):
        return f"{self.log_source} - {self.log_level.upper()} - {self.timestamp}"


class SystemConfigurationBackup(models.Model):
    """Model for system configuration backups"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name for this backup")
    description = models.TextField(blank=True, help_text="Description of what is included in this backup")
    backup_type = models.CharField(max_length=100, choices=[
        ('full', 'Full System'),
        ('configuration', 'Configuration Only'),
        ('database', 'Database Only'),
        ('files', 'Files Only'),
        ('custom', 'Custom Selection'),
    ])
    backup_content = models.JSONField(default=dict, blank=True, help_text="Structured backup content")
    file_path = models.CharField(max_length=500, help_text="Path to the backup file")
    file_size_bytes = models.BigIntegerField(help_text="Size of the backup file in bytes")
    is_encrypted = models.BooleanField(default=True, help_text="Whether the backup is encrypted")
    encryption_key_identifier = models.CharField(max_length=255, blank=True, help_text="Identifier for the encryption key used")
    checksum = models.CharField(max_length=255, help_text="Checksum for verifying backup integrity")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='configuration_backups_created')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_by_system = models.BooleanField(default=False, help_text="Whether this was a scheduled system backup")
    restore_instructions = models.TextField(blank=True, help_text="Instructions for restoring this backup")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing backups")
    notes = models.TextField(blank=True, help_text="Internal notes about this backup")
    
    class Meta:
        verbose_name = "System Configuration Backup"
        verbose_name_plural = "System Configuration Backups"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.backup_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class TenantCloneHistory(models.Model):
    """Model for tracking tenant cloning operations"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name for this clone operation")
    description = models.TextField(blank=True, help_text="Description of the cloning operation")
    source_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clones_as_source')
    destination_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='clones_as_destination')
    clone_type = models.CharField(max_length=100, choices=[
        ('full_copy', 'Full Copy'),
        ('template_based', 'Template Based'),
        ('data_migration', 'Data Migration'),
        ('configuration_only', 'Configuration Only'),
        ('users_only', 'Users Only'),
        ('custom', 'Custom Selection'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_clones_started')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_clones_completed')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.FloatField(default=0.0, help_text="Progress percentage of the clone operation")
    total_steps = models.IntegerField(default=0, help_text="Total number of steps in the cloning process")
    completed_steps = models.IntegerField(default=0, help_text="Number of completed steps")
    error_message = models.TextField(blank=True, help_text="Error message if the clone operation failed")
    success_message = models.TextField(blank=True, help_text="Success message if the clone operation succeeded")
    clone_options = models.JSONField(default=dict, blank=True, help_text="Options for the cloning process")
    data_copied = models.JSONField(default=dict, blank=True, help_text="Information about what data was copied")
    tenant_settings = models.JSONField(default=dict, blank=True, help_text="Settings copied during the clone")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing clone operations")
    notes = models.TextField(blank=True, help_text="Internal notes about this clone operation")
    
    class Meta:
        verbose_name = "Tenant Clone History"
        verbose_name_plural = "Tenant Clone Histories"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.name} - {self.source_tenant.name} to {self.destination_tenant.name if self.destination_tenant else 'New Tenant'}"


class SystemUpdateLog(models.Model):
    """Model for tracking system updates and patches"""
    id = models.AutoField(primary_key=True)
    update_type = models.CharField(max_length=100, choices=[
        ('security_patch', 'Security Patch'),
        ('feature_update', 'Feature Update'),
        ('bug_fix', 'Bug Fix'),
        ('performance_improvement', 'Performance Improvement'),
        ('dependency_update', 'Dependency Update'),
        ('configuration_change', 'Configuration Change'),
        ('database_migration', 'Database Migration'),
        ('infrastructure_update', 'Infrastructure Update'),
    ])
    name = models.CharField(max_length=255, help_text="Name of the update")
    description = models.TextField(blank=True, help_text="Description of what the update does")
    version_from = models.CharField(max_length=50, blank=True, help_text="Version before the update")
    version_to = models.CharField(max_length=50, help_text="Version after the update")
    release_notes = models.TextField(blank=True, help_text="Release notes for the update")
    is_security_update = models.BooleanField(default=False, help_text="Whether this is a security-related update")
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="When the update is scheduled to be applied")
    applied_at = models.DateTimeField(null=True, blank=True, help_text="When the update was applied")
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updates_applied')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ], default='pending')
    requires_downtime = models.BooleanField(default=False, help_text="Whether this update requires system downtime")
    estimated_downtime_minutes = models.IntegerField(default=0, help_text="Estimated downtime in minutes")
    rollback_possible = models.BooleanField(default=True, help_text="Whether the update can be rolled back")
    rollback_instructions = models.TextField(blank=True, help_text="Instructions for rolling back the update")
    affected_components = models.JSONField(default=list, blank=True, help_text="List of components affected by the update")
    pre_update_checks = models.JSONField(default=list, blank=True, help_text="Checks to perform before the update")
    post_update_checks = models.JSONField(default=list, blank=True, help_text="Checks to perform after the update")
    backup_before_update = models.BooleanField(default=True, help_text="Whether to create a backup before the update")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing updates")
    notes = models.TextField(blank=True, help_text="Internal notes about this update")
    
    class Meta:
        verbose_name = "System Update Log"
        verbose_name_plural = "System Update Logs"
        ordering = ['-applied_at', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.update_type} - {self.status}"


class KnowledgeBaseArticle(models.Model):
    """Model for system documentation and knowledge base"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, help_text="Title of the article")
    slug = models.SlugField(max_length=255, unique=True, help_text="URL-friendly version of the title")
    content = models.TextField(help_text="Content of the article")
    content_format = models.CharField(max_length=20, choices=[
        ('html', 'HTML'),
        ('markdown', 'Markdown'),
        ('plain_text', 'Plain Text'),
    ], default='markdown')
    category = models.CharField(max_length=100, choices=[
        ('getting_started', 'Getting Started'),
        ('troubleshooting', 'Troubleshooting'),
        ('best_practices', 'Best Practices'),
        ('api_documentation', 'API Documentation'),
        ('security', 'Security'),
        ('compliance', 'Compliance'),
        ('administration', 'Administration'),
        ('integration', 'Integration'),
        ('performance', 'Performance'),
        ('customization', 'Customization'),
    ])
    subcategory = models.CharField(max_length=100, blank=True, help_text="Optional subcategory")
    is_published = models.BooleanField(default=False, help_text="Whether this article is published and visible")
    is_featured = models.BooleanField(default=False, help_text="Whether this article is featured")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='knowledge_base_articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True, help_text="When this article was last reviewed")
    review_frequency_days = models.IntegerField(default=180, help_text="How often this article should be reviewed in days")
    next_review_date = models.DateTimeField(null=True, blank=True, help_text="When this article is next due for review")
    view_count = models.IntegerField(default=0, help_text="Number of times this article has been viewed")
    helpful_count = models.IntegerField(default=0, help_text="Number of times users found this article helpful")
    not_helpful_count = models.IntegerField(default=0, help_text="Number of times users found this article not helpful")
    related_articles = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='related_to')
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing articles")
    search_keywords = models.JSONField(default=list, blank=True, help_text="Keywords for improving searchability")
    is_archived = models.BooleanField(default=False, help_text="Whether this article is archived")
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles_archived')
    
    class Meta:
        verbose_name = "Knowledge Base Article"
        verbose_name_plural = "Knowledge Base Articles"
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class SystemNotification(models.Model):
    """Model for system-wide notifications"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, help_text="Title of the notification")
    message = models.TextField(help_text="Content of the notification")
    notification_type = models.CharField(max_length=50, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('alert', 'Alert'),
        ('maintenance', 'Maintenance Notice'),
        ('update', 'System Update'),
        ('security', 'Security Notice'),
        ('announcement', 'Announcement'),
    ])
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='normal')
    target_audience = models.CharField(max_length=50, choices=[
        ('all_users', 'All Users'),
        ('admin_users', 'Administrators Only'),
        ('specific_tenants', 'Specific Tenants'),
        ('specific_roles', 'Specific Roles'),
    ], default='all_users')
    affected_tenants = models.ManyToManyField(Tenant, blank=True, related_name='system_notifications')
    affected_roles = models.JSONField(default=list, blank=True, help_text="List of roles this notification affects")
    start_publishing = models.DateTimeField(default=timezone.now, help_text="When to start publishing this notification")
    stop_publishing = models.DateTimeField(null=True, blank=True, help_text="When to stop publishing this notification")
    is_active = models.BooleanField(default=True, help_text="Whether this notification is currently active")
    is_dismissible = models.BooleanField(default=True, help_text="Whether users can dismiss this notification")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    dismissed_by_users = models.ManyToManyField(User, blank=True, related_name='dismissed_notifications', help_text="Users who have dismissed this notification")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing notifications")
    notes = models.TextField(blank=True, help_text="Internal notes about this notification")
    
    class Meta:
        verbose_name = "System Notification"
        verbose_name_plural = "System Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.notification_type.upper()}"
