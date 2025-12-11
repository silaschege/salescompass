from django.db import models
from django.utils import timezone
from core.models import User
from tenants.models import Tenant


class APIToken(models.Model):
    """Model for managing API access tokens"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Descriptive name for the token")
    token = models.CharField(max_length=255, unique=True, help_text="The actual API token")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='api_tokens')
    scopes = models.JSONField(default=list, blank=True, help_text="List of permissions this token has")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this token expires")
    last_used_at = models.DateTimeField(null=True, blank=True, help_text="When this token was last used")
    is_active = models.BooleanField(default=True, help_text="Whether this token is currently active")
    description = models.TextField(blank=True, help_text="Description of what this token is used for")
    ip_restrictions = models.JSONField(default=list, blank=True, help_text="IP addresses from which this token can be used")
    rate_limit = models.IntegerField(default=1000, help_text="Number of requests allowed per time period")
    rate_limit_period_seconds = models.IntegerField(default=3600, help_text="Time period for rate limiting in seconds")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tokens_created')
    notes = models.TextField(blank=True, help_text="Internal notes about this token")
    
    class Meta:
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"


class IntegrationHealthCheck(models.Model):
    """Model for tracking integration health"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the integration")
    description = models.TextField(blank=True, help_text="Description of the integration")
    endpoint_url = models.URLField(max_length=500, help_text="URL of the integration endpoint")
    auth_method = models.CharField(max_length=50, choices=[
        ('api_key', 'API Key'),
        ('oauth', 'OAuth'),
        ('basic_auth', 'Basic Authentication'),
        ('bearer_token', 'Bearer Token'),
        ('custom', 'Custom'),
    ])
    auth_config = models.JSONField(default=dict, blank=True, help_text="Authentication configuration")
    health_check_frequency_minutes = models.IntegerField(default=5, help_text="How often to check health in minutes")
    last_checked = models.DateTimeField(null=True, blank=True, help_text="Last time health was checked")
    last_status = models.CharField(max_length=20, choices=[
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='healthy')
    last_response_time_ms = models.FloatField(null=True, blank=True, help_text="Last response time in milliseconds")
    last_error = models.TextField(blank=True, help_text="Last error message if any")
    is_active = models.BooleanField(default=True, help_text="Whether health checks are active for this integration")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='integration_health_checks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='integration_health_checks_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    failure_threshold = models.IntegerField(default=3, help_text="Number of consecutive failures before marking as unhealthy")
    consecutive_failure_count = models.IntegerField(default=0, help_text="Current count of consecutive failures")
    last_successful_check = models.DateTimeField(null=True, blank=True, help_text="Last time the integration was healthy")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing integrations")
    notes = models.TextField(blank=True, help_text="Internal notes about this integration")
    
    class Meta:
        verbose_name = "Integration Health Check"
        verbose_name_plural = "Integration Health Checks"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.last_status.upper()}"


class ConnectorConfiguration(models.Model):
    """Model for storing connector configurations"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the connector")
    description = models.TextField(blank=True, help_text="Description of what the connector does")
    connector_type = models.CharField(max_length=100, choices=[
        ('webhook', 'Webhook'),
        ('api', 'API'),
        ('database', 'Database'),
        ('email', 'Email'),
        ('ftp', 'FTP/SFTP'),
        ('file', 'File System'),
        ('queue', 'Message Queue'),
        ('streaming', 'Streaming'),
        ('custom', 'Custom'),
    ])
    configuration_schema = models.JSONField(default=dict, blank=True, help_text="Schema for connector configuration")
    configuration_values = models.JSONField(default=dict, blank=True, help_text="Actual configuration values")
    is_active = models.BooleanField(default=True, help_text="Whether this connector is active")
    is_encrypted = models.BooleanField(default=True, help_text="Whether sensitive configuration values are encrypted")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='connector_configurations')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='connectors_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_tested = models.DateTimeField(null=True, blank=True, help_text="Last time the connector was tested")
    last_test_result = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('pending', 'Pending'),
    ], default='pending')
    last_test_error = models.TextField(blank=True, help_text="Error message from last test")
    rate_limit_config = models.JSONField(default=dict, blank=True, help_text="Rate limiting configuration")
    retry_policy = models.JSONField(default=dict, blank=True, help_text="Retry policy configuration")
    transformation_rules = models.JSONField(default=dict, blank=True, help_text="Data transformation rules")
    error_handling_config = models.JSONField(default=dict, blank=True, help_text="Error handling configuration")
    monitoring_config = models.JSONField(default=dict, blank=True, help_text="Monitoring configuration")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing connectors")
    notes = models.TextField(blank=True, help_text="Internal notes about this connector")
    
    class Meta:
        verbose_name = "Connector Configuration"
        verbose_name_plural = "Connector Configurations"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.connector_type}"


class IntegrationAuditLog(models.Model):
    """Model for auditing integration activities"""
    id = models.AutoField(primary_key=True)
    integration_name = models.CharField(max_length=255, help_text="Name of the integration involved")
    action = models.CharField(max_length=100, choices=[
        ('connect', 'Connect'),
        ('disconnect', 'Disconnect'),
        ('configure', 'Configure'),
        ('test', 'Test'),
        ('sync', 'Sync'),
        ('data_transfer', 'Data Transfer'),
        ('error', 'Error'),
        ('health_check', 'Health Check'),
        ('rate_limit', 'Rate Limited'),
        ('retry', 'Retry'),
        ('transform', 'Transform'),
        ('validate', 'Validate'),
        ('cleanup', 'Cleanup'),
        ('maintenance', 'Maintenance'),
    ])
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='integration_audit_logs')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='integration_audit_logs')
    resource_type = models.CharField(max_length=100, help_text="Type of resource involved in the integration")
    resource_id = models.CharField(max_length=100, help_text="ID of the resource involved", blank=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('partial_success', 'Partial Success'),
        ('failure', 'Failure'),
        ('timeout', 'Timeout'),
        ('cancelled', 'Cancelled'),
    ], default='success')
    request_payload = models.TextField(blank=True, help_text="Request payload sent to the integration")
    response_payload = models.TextField(blank=True, help_text="Response received from the integration")
    response_status_code = models.IntegerField(null=True, blank=True, help_text="HTTP status code from the response")
    execution_time_ms = models.FloatField(null=True, blank=True, help_text="Time taken to execute the action in milliseconds")
    error_message = models.TextField(blank=True, help_text="Error message if the action failed")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the requesting client")
    user_agent = models.TextField(blank=True, help_text="User agent string of the requesting client")
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the action")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing audit logs")
    
    class Meta:
        verbose_name = "Integration Audit Log"
        verbose_name_plural = "Integration Audit Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.integration_name} - {self.action} - {self.status}"


class MarketplaceApp(models.Model):
    """Model for managing marketplace applications"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the marketplace app")
    description = models.TextField(blank=True, help_text="Description of what the app does")
    version = models.CharField(max_length=50, default='1.0.0', help_text="Version of the app")
    publisher = models.CharField(max_length=255, help_text="Publisher of the app")
    publisher_website = models.URLField(blank=True, help_text="Publisher's website")
    icon_url = models.URLField(blank=True, help_text="URL to the app's icon")
    screenshots = models.JSONField(default=list, blank=True, help_text="List of screenshot URLs")
    categories = models.JSONField(default=list, blank=True, help_text="Categories this app belongs to")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for the app")
    pricing_model = models.CharField(max_length=50, choices=[
        ('free', 'Free'),
        ('freemium', 'Freemium'),
        ('paid', 'Paid'),
        ('subscription', 'Subscription'),
        ('one_time', 'One-time Purchase'),
        ('usage_based', 'Usage-based'),
    ], default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price of the app")
    currency = models.CharField(max_length=3, default='USD', help_text="Currency for the price")
    rating = models.FloatField(default=0.0, help_text="Average rating of the app")
    rating_count = models.IntegerField(default=0, help_text="Number of ratings received")
    download_count = models.IntegerField(default=0, help_text="Number of times the app has been downloaded")
    installation_count = models.IntegerField(default=0, help_text="Number of active installations")
    is_featured = models.BooleanField(default=False, help_text="Whether this app is featured")
    is_verified = models.BooleanField(default=False, help_text="Whether this app is verified by us")
    is_active = models.BooleanField(default=True, help_text="Whether this app is available in the marketplace")
    approval_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ], default='pending')
    approval_notes = models.TextField(blank=True, help_text="Notes from the approval process")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='apps_approved')
    approved_at = models.DateTimeField(null=True, blank=True, help_text="When the app was approved")
    published_at = models.DateTimeField(null=True, blank=True, help_text="When the app was published")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='apps_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    installation_config = models.JSONField(default=dict, blank=True, help_text="Configuration required for installation")
    compatibility = models.JSONField(default=dict, blank=True, help_text="Compatibility information")
    changelog = models.JSONField(default=list, blank=True, help_text="List of changes in each version")
    support_url = models.URLField(blank=True, help_text="URL for support")
    documentation_url = models.URLField(blank=True, help_text="URL for documentation")
    privacy_policy_url = models.URLField(blank=True, help_text="URL for privacy policy")
    terms_of_service_url = models.URLField(blank=True, help_text="URL for terms of service")
    
    class Meta:
        verbose_name = "Marketplace App"
        verbose_name_plural = "Marketplace Apps"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version} by {self.publisher}"
