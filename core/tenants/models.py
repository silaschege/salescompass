from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from core.models import User
from django.core.files.storage import default_storage
import os

# Choices for various fields
TIMEZONE_CHOICES = [
    ('UTC', 'UTC'),
    ('US/Eastern', 'US/Eastern'),
    ('US/Central', 'US/Central'),
    ('US/Mountain', 'US/Mountain'),
    ('US/Pacific', 'US/Pacific'),
    ('Europe/London', 'Europe/London'),
    ('Europe/Paris', 'Europe/Paris'),
    ('Asia/Tokyo', 'Asia/Tokyo'),
    ('Asia/Shanghai', 'Asia/Shanghai'),
    ('Asia/Kolkata', 'Asia/Kolkata'),
]

CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('JPY', 'Japanese Yen'),
    ('CAD', 'Canadian Dollar'),
    ('AUD', 'Australian Dollar'),
    ('CHF', 'Swiss Franc'),
    ('CNY', 'Chinese Yuan'),
    ('INR', 'Indian Rupee'),
    ('KES', 'Kenyan Shilling'),
]

DATE_FORMAT_CHOICES = [
    ('%Y-%m-%d', 'YYYY-MM-DD (ISO)'),
    ('%m/%d/%Y', 'MM/DD/YYYY (US)'),
    ('%d/%m/%Y', 'DD/MM/YYYY (EU)'),
    ('%m-%d-%Y', 'MM-DD-YYYY (US)'),
    ('%d-%m-%Y', 'DD-MM-YYYY (EU)'),
]

LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('ja', 'Japanese'),
    ('zh-hans', 'Chinese (Simplified)'),
    ('sw', 'Swahili'),
]

REGION_CHOICES = [
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('EU', 'European Union'),
    ('KE', 'Kenya'),
    ('JP', 'Japan'),
    ('CN', 'China'),
    ('IN', 'India'),
]



class TenantAwareModel(models.Model):
    """Abstract base class for models that belong to a tenant"""
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='%(class)ss')
    
    class Meta:
        abstract = True



class TenantAwareModel(models.Model):
    """Abstract base class for models that belong to a tenant"""
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='%(class)ss')
    
    class Meta:
        abstract = True


class Tenant(models.Model):
    """Model for managing tenants in the multi-tenant system"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, help_text="URL-friendly identifier for the tenant")
    description = models.TextField(blank=True)
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True, help_text="Custom domain for the tenant")
    subdomain = models.SlugField(max_length=255, unique=True, null=True, blank=True, help_text="Subdomain for the tenant")
    logo_url = models.URLField(blank=True, help_text="URL to the tenant's logo")
    primary_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#6f42c1',
        help_text="Primary brand color in hex format"
    )
    secondary_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#007bff',
        help_text="Secondary brand color in hex format"
    )
    
    # Plan and billing information
    plan = models.ForeignKey('billing.Plan', on_delete=models.SET_NULL, null=True, blank=True, related_name='tenants')
    subscription_status = models.CharField(max_length=20, choices=[
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
    ], default='trialing')
    trial_end_date = models.DateTimeField(null=True, blank=True, help_text="End date of trial period")
    billing_cycle_anchor = models.DateTimeField(null=True, blank=True, help_text="Date for billing cycle alignment")
    
    # Tenant status and lifecycle
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True, help_text="Reason for suspension")
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Limits and quotas
    user_limit = models.IntegerField(default=10, help_text="Maximum number of users allowed")
    storage_limit_mb = models.IntegerField(default=1000, help_text="Storage limit in MB")
    api_call_limit = models.IntegerField(default=10000, help_text="Monthly API call limit")
    
    # Settings
    tenant_config = models.JSONField(default=dict, blank=True, help_text="Tenant-specific configuration")
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def suspend(self, reason='', triggered_by=None, ip_address=None):
        """Suspend the tenant and log the lifecycle event"""
        old_status = f"active={self.is_active}, suspended={self.is_suspended}"
        
        self.is_suspended = True
        self.is_active = False
        self.suspension_reason = reason
        self.save()
        
        new_status = f"active={self.is_active}, suspended={self.is_suspended}"
        
        # Create lifecycle event
        TenantLifecycleEvent.objects.create(
            tenant=self,
            event_type='suspended',
            old_value=old_status,
            new_value=new_status,
            reason=reason,
            triggered_by=triggered_by,
            ip_address=ip_address
        )
    
    def reactivate(self, triggered_by=None, ip_address=None):
        """Reactivate the tenant and log the lifecycle event"""
        old_status = f"active={self.is_active}, suspended={self.is_suspended}"
        
        self.is_suspended = False
        self.is_active = True
        self.suspension_reason = ''
        self.save()
        
        new_status = f"active={self.is_active}, suspended={self.is_suspended}"
        
        # Create lifecycle event
        TenantLifecycleEvent.objects.create(
            tenant=self,
            event_type='reactivated',
            old_value=old_status,
            new_value=new_status,
            reason='Tenant reactivation',
            triggered_by=triggered_by,
            ip_address=ip_address
        )
    
    def archive(self, triggered_by=None, ip_address=None):
        """Archive the tenant and log the lifecycle event"""
        old_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        self.is_archived = True
        self.is_active = False
        self.archived_at = timezone.now()
        self.save()
        
        new_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        # Create lifecycle event
        TenantLifecycleEvent.objects.create(
            tenant=self,
            event_type='archived',
            old_value=old_status,
            new_value=new_status,
            reason='Tenant archival',
            triggered_by=triggered_by,
            ip_address=ip_address
        )
    
    def restore(self, triggered_by=None, ip_address=None):
        """Restore the tenant from archived state and log the lifecycle event"""
        old_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        self.is_archived = False
        self.is_active = True
        self.archived_at = None
        self.save()
        
        new_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        # Create lifecycle event
        TenantLifecycleEvent.objects.create(
            tenant=self,
            event_type='restored',
            old_value=old_status,
            new_value=new_status,
            reason='Tenant restoration',
            triggered_by=triggered_by,
            ip_address=ip_address
        )
    
    def soft_delete(self, triggered_by=None, ip_address=None):
        """Soft delete the tenant and log the lifecycle event"""
        old_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        self.is_active = False
        self.is_archived = True
        self.archived_at = timezone.now()
        self.save()
        
        new_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        # Create lifecycle event
        TenantLifecycleEvent.objects.create(
            tenant=self,
            event_type='deleted',
            old_value=old_status,
            new_value=new_status,
            reason='Tenant deletion',
            triggered_by=triggered_by,
            ip_address=ip_address
        )
    
    def activate(self, triggered_by=None, ip_address=None):
        """Activate the tenant and log the lifecycle event"""
        old_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        self.is_active = True
        self.is_suspended = False
        self.is_archived = False
        self.archived_at = None
        self.save()
        
        new_status = f"active={self.is_active}, suspended={self.is_suspended}, archived={self.is_archived}"
        
        # Create lifecycle event
        TenantLifecycleEvent.objects.create(
            tenant=self,
            event_type='activated',
            old_value=old_status,
            new_value=new_status,
            reason='Tenant activation',
            triggered_by=triggered_by,
            ip_address=ip_address
        )


class TenantLifecycleEvent(models.Model):
    """Model for tracking tenant lifecycle transitions"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='lifecycle_events')
    event_type = models.CharField(max_length=50, choices=[
        ('created', 'Tenant Created'),
        ('activated', 'Tenant Activated'),
        ('suspended', 'Tenant Suspended'),
        ('reactivated', 'Tenant Reactivated'),
        ('archived', 'Tenant Archived'),
        ('restored', 'Tenant Restored'),
        ('deleted', 'Tenant Deleted'),
        ('plan_changed', 'Plan Changed'),
        ('subscription_renewed', 'Subscription Renewed'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('trial_extended', 'Trial Extended'),
        ('domain_changed', 'Domain Changed'),
        ('billing_info_updated', 'Billing Info Updated'),
    ])
    old_value = models.TextField(blank=True, help_text="Previous value before change")
    new_value = models.TextField(blank=True, help_text="New value after change")
    reason = models.TextField(blank=True, help_text="Reason for the lifecycle event")
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_lifecycle_events')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Tenant Lifecycle Event"
        verbose_name_plural = "Tenant Lifecycle Events"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} for {self.tenant.name} at {self.timestamp}"


class TenantMigrationRecord(models.Model):
    """Model for documenting tenant migration activities"""
    id = models.AutoField(primary_key=True)
    source_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='migration_sources')
    destination_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='migration_destinations')
    migration_type = models.CharField(max_length=50, choices=[
        ('tenant_clone', 'Tenant Clone'),
        ('tenant_merge', 'Tenant Merge'),
        ('tenant_split', 'Tenant Split'),
        ('data_transfer', 'Data Transfer'),
        ('user_transfer', 'User Transfer'),
        ('account_transfer', 'Account Transfer'),
        ('lead_transfer', 'Lead Transfer'),
        ('opportunity_transfer', 'Opportunity Transfer'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='initiated_migrations')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_migrations')
    progress_percentage = models.FloatField(default=0.0)
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True, help_text="Log of any errors encountered during migration")
    migration_notes = models.TextField(blank=True, help_text="Notes about the migration process")
    
    class Meta:
        verbose_name = "Tenant Migration Record"
        verbose_name_plural = "Tenant Migration Records"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.migration_type} from {self.source_tenant.name} to {self.destination_tenant.name}"


class TenantUsageMetric(models.Model):
    """Model for capturing tenant-specific usage data"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='usage_metrics')
    metric_type = models.CharField(max_length=100, choices=[
        ('users_active', 'Active Users'),
        ('users_total', 'Total Users'),
        ('storage_used_mb', 'Storage Used (MB)'),
        ('api_calls', 'API Calls'),
        ('records_created', 'Records Created'),
        ('records_updated', 'Records Updated'),
        ('records_deleted', 'Records Deleted'),
        ('logins', 'Login Count'),
        ('sessions', 'Active Sessions'),
        ('emails_sent', 'Emails Sent'),
        ('files_uploaded', 'Files Uploaded'),
        ('data_exported', 'Data Exported'),
        ('reports_generated', 'Reports Generated'),
        ('integrations_active', 'Active Integrations'),
    ])
    value = models.FloatField()
    unit = models.CharField(max_length=20, default='', blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    class Meta:
        verbose_name = "Tenant Usage Metric"
        verbose_name_plural = "Tenant Usage Metrics"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'metric_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric_type} for {self.tenant.name}: {self.value}{self.unit}"


class TenantCloneHistory(models.Model):
    """Model for tracking tenant cloning operations"""
    id = models.AutoField(primary_key=True)
    original_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clones_created')
    cloned_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cloned_from')
    clone_type = models.CharField(max_length=50, choices=[
        ('full_copy', 'Full Copy'),
        ('template_based', 'Template Based'),
        ('minimal_setup', 'Minimal Setup'),
        ('data_migration', 'Data Migration'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_clones_initiated')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_clones_completed')
    clone_options = models.JSONField(default=dict, blank=True, help_text="Options for the cloning process")
    progress_percentage = models.FloatField(default=0.0)
    total_steps = models.IntegerField(default=0)
    completed_steps = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    success_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Tenant Clone History"
        verbose_name_plural = "Tenant Clone Histories"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Clone of {self.original_tenant.name} to {self.cloned_tenant.name}"


class TenantFeatureEntitlement(models.Model):
    """Model for managing feature access per tenant"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='feature_entitlements')
    feature_key = models.CharField(max_length=255, help_text="Unique identifier for the feature")
    feature_name = models.CharField(max_length=255, help_text="Display name for the feature")
    is_enabled = models.BooleanField(default=True, help_text="Whether the feature is enabled for this tenant")
    entitlement_type = models.CharField(max_length=50, choices=[
        ('always_enabled', 'Always Enabled'),
        ('plan_based', 'Plan Based'),
        ('trial', 'Trial'),
        ('premium', 'Premium'),
        ('custom', 'Custom'),
    ], default='plan_based')
    trial_start_date = models.DateTimeField(null=True, blank=True, help_text="Start date for trial period")
    trial_end_date = models.DateTimeField(null=True, blank=True, help_text="End date for trial period")
    notes = models.TextField(blank=True, help_text="Additional notes about the feature entitlement")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Feature Entitlement"
        verbose_name_plural = "Tenant Feature Entitlements"
        unique_together = ['tenant', 'feature_key']
        ordering = ['feature_name']
    
    def __str__(self):
        return f"{self.feature_name} for {self.tenant.name} - {'Enabled' if self.is_enabled else 'Disabled'}"


class TenantSettings(models.Model):
    """Model for storing tenant-specific settings and configurations"""
    id = models.AutoField(primary_key=True)
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='tenant_settings')
    
    # Branding settings
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True, help_text="Upload tenant logo")
    primary_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#6f42c1',
        help_text="Primary brand color in hex format"
    )
    secondary_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#007bff',
        help_text="Secondary brand color in hex format"
    )
    
    # Localization settings
    time_zone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='UTC', help_text="Default time zone for the tenant")
    date_format = models.CharField(max_length=20, choices=DATE_FORMAT_CHOICES, default='%Y-%m-%d', help_text="Default date format")
    language_preference = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en', help_text="Default language for the tenant")
    region = models.CharField(max_length=10, choices=REGION_CHOICES, default='US', help_text="Default region for regional settings")
    default_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD', help_text="Default currency for financial values")
    
    # Business hours and working days
    business_hours = models.JSONField(default=dict, blank=True, help_text="""
        Business hours configuration example:
        {
            "monday": {"start": "09:00", "end": "17:00"},
            "tuesday": {"start": "09:00", "end": "17:00"},
            ...
            "friday": {"start": "09:00", "end": "17:00"}
        }
    """)
    working_days = models.JSONField(default=list, blank=True, help_text="List of working days (e.g., ['monday', 'tuesday', ...])")
    
    # Session and security settings
    session_timeout_minutes = models.PositiveIntegerField(default=120, help_text="Session timeout in minutes")
    max_login_attempts = models.PositiveIntegerField(default=5, help_text="Maximum number of failed login attempts before lockout")
    lockout_duration_minutes = models.PositiveIntegerField(default=30, help_text="Duration of account lockout in minutes")
    
    # Feature toggles
    is_active = models.BooleanField(default=True, help_text="Whether this tenant's settings are active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Setting"
        verbose_name_plural = "Tenant Settings"
        ordering = ['tenant__name']
    
    def __str__(self):
        return f"Settings for {self.tenant.name}"
