
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
    tenant_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_tenants',
        help_text="The primary administrator for this tenant"
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
        
        # Track tenant creation/update if this is a new tenant
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Track tenant creation
            self.track_usage('records_created', value=1, unit='tenants')

    
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

    def get_current_usage(self, metric_type, period_start=None, period_end=None):
        """
        Get current usage for this tenant and a specific metric type
        """
        from django.utils import timezone
        from .utils import get_current_usage
        
        if period_start is None:
            period_start = timezone.now() - timezone.timedelta(days=1)
        if period_end is None:
            period_end = timezone.now()
        
        return get_current_usage(self, metric_type, period_start, period_end)
    
    def track_usage(self, metric_type, value=1, unit='', period_start=None, period_end=None):
        """
        Track usage for this tenant
        """
        from .utils import track_usage
        return track_usage(self, metric_type, value, unit, period_start, period_end)
    

    
    def check_usage_limits(self):
        """
        Check if this tenant is approaching or exceeding usage limits
        """
        from .utils import check_usage_limits
        return check_usage_limits(self)

    def has_feature_access(self, feature_key):
        """
        Check if this tenant has access to a specific feature
        """
        try:
            feature_entitlement = TenantFeatureEntitlement.objects.get(
                tenant=self,
                feature_key=feature_key
            )
            return feature_entitlement.is_enabled
        except TenantFeatureEntitlement.DoesNotExist:
            return False


    
    def enforce_feature_access(self, feature_key):
        """
        Enforce feature access - raise exception if tenant doesn't have access
        """
        if not self.has_feature_access(feature_key):
            raise PermissionError(f"Feature '{feature_key}' is not available for your tenant plan.")
        
        # Check if it's a trial feature and if the trial has expired
        try:
            feature_entitlement = TenantFeatureEntitlement.objects.get(
                tenant=self,
                feature_key=feature_key
            )
            
            if (feature_entitlement.entitlement_type == 'trial' and 
                feature_entitlement.trial_end_date and 
                timezone.now() > feature_entitlement.trial_end_date):
                raise PermissionError(f"Trial for feature '{feature_key}' has expired.")
        except TenantFeatureEntitlement.DoesNotExist:
            pass


    


def get_accessible_features(user):
    """
    Get all features that are accessible to the user's tenant
    """
    if not hasattr(user, 'tenant') or not user.tenant:
        return []
    
    from .models import TenantFeatureEntitlement
    accessible_features = TenantFeatureEntitlement.objects.filter(
        tenant=user.tenant,
        is_enabled=True
    )
    
    # Check trial expiration
    active_features = []
    for feature in accessible_features:
        if feature.entitlement_type != 'trial' or not feature.trial_end_date or feature.trial_end_date > timezone.now():
            active_features.append(feature)
    
    return active_features

    def now(self):
        """
        Get current time respecting tenant's timezone
        """
        from django.utils import timezone
        if hasattr(self, 'tenant_settings') and self.tenant_settings.time_zone:
            import pytz
            tz = pytz.timezone(self.tenant_settings.time_zone)
            return timezone.now().astimezone(tz)
        return timezone.now()

    @property
    def has_data_residency_settings(self):
        """
        Check if this tenant has data residency settings configured
        """
        try:
            return hasattr(self, 'data_residency_settings')
        except:
            return False

    def get_data_residency_settings(self):
        """
        Get data residency settings for this tenant, creating default if needed
        """
        from .models import DataResidencySettings
        settings, created = DataResidencySettings.objects.get_or_create(
            tenant=self,
            defaults={
                'primary_region': 'GLOBAL',
                'encryption_enabled': True,
                'data_retention_period_months': 36,
            }
        )
        return settings




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
    
    def is_trial_active(self):
        """Check if the trial period is currently active"""
        from django.utils import timezone
        if self.entitlement_type != 'trial':
            return False
        if not self.trial_start_date or not self.trial_end_date:
            return False
        now = timezone.now()
        return self.trial_start_date <= now <= self.trial_end_date
    
    def is_access_valid(self):
        """Check if the feature access is currently valid"""
        if not self.is_enabled:
            return False
        if self.entitlement_type == 'trial':
            return self.is_trial_active()
        return True

    def save(self, *args, **kwargs):
        # Track feature entitlement changes
        is_new = self.pk is None
        old_entitlement = None
        
        if not is_new:
            try:
                old_entitlement = TenantFeatureEntitlement.objects.get(pk=self.pk)
            except TenantFeatureEntitlement.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Track changes in usage metrics
        if is_new or old_entitlement and old_entitlement.is_enabled != self.is_enabled:
            # Track feature enable/disable
            action = 'feature_enabled' if self.is_enabled else 'feature_disabled'
            self.tenant.track_usage(action, value=1, unit='features')
        
        # If it's a trial feature, track trial start/end
        if self.entitlement_type == 'trial':
            if self.trial_start_date and (is_new or old_entitlement and old_entitlement.trial_start_date != self.trial_start_date):
                self.tenant.track_usage('trial_started', value=1, unit='trials')
        

   
    def has_feature_access(self, feature_key):
        """
        Check if this tenant has access to a specific feature
        """
        try:
            feature_entitlement = TenantFeatureEntitlement.objects.get(
                tenant=self,
                feature_key=feature_key
            )
            return feature_entitlement.is_enabled
        except TenantFeatureEntitlement.DoesNotExist:
            # Check if feature is available through plan
            if self.plan:
                from billing.models import PlanFeatureAccess
                try:
                    plan_feature = PlanFeatureAccess.objects.get(
                        plan=self.plan,
                        feature_key=feature_key
                    )
                    return plan_feature.is_available
                except PlanFeatureAccess.DoesNotExist:
                    pass
            return False

    def get_accessible_features(self):
        """
        Get all features that are accessible to this tenant
        """
        from .models import TenantFeatureEntitlement
        from billing.models import PlanFeatureAccess
        
        # Get features from explicit entitlements
        explicit_features = TenantFeatureEntitlement.objects.filter(
            tenant=self,
            is_enabled=True
        )
        
        # Get features from plan
        plan_features = []
        if self.plan:
            plan_features = PlanFeatureAccess.objects.filter(
                plan=self.plan,
                is_available=True
            )
        
        # Combine both sources
        accessible_features = list(explicit_features)
        for plan_feature in plan_features:
            # Check if this feature is overridden by explicit entitlement
            if not any(f.feature_key == plan_feature.feature_key for f in explicit_features):
                # Create a temporary object with similar interface to TenantFeatureEntitlement
                class PlanFeatureWrapper:
                    def __init__(self, plan_feature):
                        self.feature_key = plan_feature.feature_key
                        self.feature_name = plan_feature.feature_name
                        self.is_enabled = plan_feature.is_available
                        self.entitlement_type = 'plan_based'
                        self.notes = plan_feature.notes
                        
                accessible_features.append(PlanFeatureWrapper(plan_feature))
        
        return accessible_features

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


class SettingType(models.Model):
    """
    Dynamic setting type values - allows tenant-specific setting type tracking.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='dynamic_setting_types')
    setting_type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'text', 'number'")
    label = models.CharField(max_length=50) # e.g., 'Text', 'Number'
    order = models.IntegerField(default=0)
    setting_type_is_active = models.BooleanField(default=True, help_text="Whether this setting type is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'setting_type_name']
        unique_together = [('tenant', 'setting_type_name')]
        verbose_name_plural = 'Setting Types'
    
    def __str__(self):
        return self.label


class SettingGroup(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='dynamic_setting_groups')
    setting_group_name = models.CharField(max_length=200, help_text="Name of the setting group")
    setting_group_description = models.TextField(blank=True, help_text="Description of the setting group")
    setting_group_is_active = models.BooleanField(default=True, help_text="Whether this setting group is active")

    class Meta:
        unique_together = [('tenant', 'setting_group_name')]

    def __str__(self):
        return self.setting_group_name



class Setting(models.Model):
    SETTING_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='dynamic_settings')
    group = models.ForeignKey(SettingGroup, on_delete=models.CASCADE, related_name='settings')
    setting_name = models.CharField(max_length=200)
    setting_label = models.CharField(max_length=200)
    setting_description = models.TextField(blank=True, help_text="Description of the setting")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='text')
    # New dynamic field
    setting_type_ref = models.ForeignKey(
        SettingType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='settings',
        help_text="Dynamic setting type (replaces setting_type field)"
    )
    value_text = models.TextField(null=True, blank=True)
    value_number = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)
    is_required = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = [('tenant', 'setting_name')]

    def __str__(self):
        return self.setting_label


class WhiteLabelSettings(models.Model):
    """Model for storing white-label branding settings per tenant"""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='white_label_settings')
    
    # Logo and branding assets
    logo = models.ImageField(upload_to='white_label_logos/', null=True, blank=True, help_text="Main logo for the tenant")
    logo_small = models.ImageField(upload_to='white_label_logos/', null=True, blank=True, help_text="Small version of the logo for header")
    favicon = models.ImageField(upload_to='white_label_logos/', null=True, blank=True, help_text="Favicon for the tenant")
    brand_image = models.ImageField(upload_to='white_label_logos/', null=True, blank=True, help_text="Full brand image for login pages")
    
    # Brand colors
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
    accent_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#28a745',
        help_text="Accent color in hex format"
    )
    background_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#ffffff',
        help_text="Background color in hex format"
    )
    
    # Brand text
    brand_name = models.CharField(max_length=255, blank=True, help_text="Custom brand name to display instead of tenant name")
    tagline = models.CharField(max_length=500, blank=True, help_text="Tagline or slogan for the brand")
    copyright_text = models.CharField(max_length=500, blank=True, help_text="Copyright text to display in footer")
    
    # Domain settings
    custom_domain = models.CharField(max_length=255, blank=True, help_text="Custom domain for the tenant")
    subdomain = models.SlugField(max_length=255, blank=True, help_text="Subdomain for the tenant")
    
    # Branding options
    show_brand_name = models.BooleanField(default=True, help_text="Whether to show the brand name in the header")
    show_logo = models.BooleanField(default=True, help_text="Whether to show the logo in the header")
    show_tagline = models.BooleanField(default=False, help_text="Whether to show the tagline")
    
    # Legal links
    privacy_policy_url = models.URLField(blank=True, help_text="URL to privacy policy")
    terms_of_service_url = models.URLField(blank=True, help_text="URL to terms of service")
    support_url = models.URLField(blank=True, help_text="URL to support page")
    
    # Additional branding settings
    login_background_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#f8f9fa',
        help_text="Background color for login pages"
    )
    login_text_color = models.CharField(
        max_length=7, 
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='Enter a valid hex color code')],
        default='#212529',
        help_text="Text color for login pages"
    )
    
    is_active = models.BooleanField(default=True, help_text="Whether white-label branding is active for this tenant")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "White-Label Setting"
        verbose_name_plural = "White-Label Settings"
        ordering = ['tenant__name']
    
    def __str__(self):
        return f"White-Label Settings for {self.tenant.name}"
    
    def save(self, *args, **kwargs):
        # If brand name is empty, use the tenant name
        if not self.brand_name:
            self.brand_name = self.tenant.name
        super().save(*args, **kwargs)



class TenantUsageMetric(models.Model):
    """Model for capturing tenant-specific usage data"""
    # Define the metric types as a class attribute so it can be accessed in templates
    METRIC_TYPES = [
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
        ('response_time', 'Response Time'),
    ]
    
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='usage_metrics')
    metric_type = models.CharField(max_length=100, choices=METRIC_TYPES)
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
    
    @classmethod
    def record_usage(cls, tenant, metric_type, value, unit='', period_start=None, period_end=None):
        """
        Class method to record usage for a tenant
        """
        from django.utils import timezone
        
        if period_start is None:
            period_start = timezone.now() - timezone.timedelta(days=1)
        if period_end is None:
            period_end = timezone.now()
        
        metric = cls.objects.create(
            tenant=tenant,
            metric_type=metric_type,
            value=value,
            unit=unit,
            period_start=period_start,
            period_end=period_end
        )
        return metric
    
    @classmethod
    def get_current_usage(cls, tenant, metric_type, period_start=None, period_end=None):
        """
        Class method to get current usage for a tenant and metric type
        """
        from django.utils import timezone
        
        if period_start is None:
            period_start = timezone.now() - timezone.timedelta(days=1)
        if period_end is None:
            period_end = timezone.now()
        
        metrics = cls.objects.filter(
            tenant=tenant,
            metric_type=metric_type,
            timestamp__gte=period_start,
            timestamp__lte=period_end
        )
        
        return sum([m.value for m in metrics])
    
    @classmethod
    def get_usage_trend(cls, tenant, metric_type, days=30):
        """
        Get usage trend for the specified number of days
        """
        from django.utils import timezone
        from django.db.models import Sum
        import datetime
        
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        
        # Group by date and sum the values
        daily_usage = cls.objects.filter(
            tenant=tenant,
            metric_type=metric_type,
            timestamp__date__gte=start_date.date(),
            timestamp__date__lte=end_date.date()
        ).values('timestamp__date').annotate(total=Sum('value')).order_by('timestamp__date')
        
        dates = []
        values = []
        
        for entry in daily_usage:
            dates.append(entry['timestamp__date'].strftime('%Y-%m-%d'))
            values.append(float(entry['total']))
        
        return {'dates': dates, 'values': values}




class OverageAlert(models.Model):
    """Model for tracking overage alerts"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='overage_alerts')
    metric_type = models.CharField(max_length=100, choices=TenantUsageMetric.METRIC_TYPES)
    threshold_value = models.FloatField(help_text="The value at which the alert was triggered")
    current_value = models.FloatField(help_text="The current value that triggered the alert")
    threshold_percentage = models.FloatField(help_text="The percentage of the limit that was reached")
    alert_level = models.CharField(max_length=20, choices=[
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('limit_reached', 'Limit Reached'),
    ], help_text="Severity level of the alert")
    is_resolved = models.BooleanField(default=False, help_text="Whether the alert has been resolved")
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_overage_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Overage Alert"
        verbose_name_plural = "Overage Alerts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_level.title()} Alert: {self.metric_type} for {self.tenant.name}"


class NotificationTemplate(models.Model):
    """Model for notification templates"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the template")
    subject = models.CharField(max_length=500, help_text="Subject line for email notifications")
    message_body = models.TextField(help_text="Body of the notification message")
    notification_type = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
    ], default='email')
    is_active = models.BooleanField(default=True, help_text="Whether this template is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Notification(models.Model):
    """Model for storing notifications"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=255, help_text="Title of the notification")
    message = models.TextField(help_text="Content of the notification")
    notification_type = models.CharField(max_length=50, choices=[
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('overage', 'Overage Alert'),
    ], default='info')
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    is_read = models.BooleanField(default=False, help_text="Whether the notification has been read")
    is_sent = models.BooleanField(default=False, help_text="Whether the notification has been sent")
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_method = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
    ], default='in_app')
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} for {self.tenant.name}"



class AlertThreshold(models.Model):
    """Model for defining alert thresholds"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='alert_thresholds')
    metric_type = models.CharField(max_length=100, choices=TenantUsageMetric.METRIC_TYPES)
    threshold_percentage = models.FloatField(help_text="Percentage of limit that triggers the alert")
    alert_level = models.CharField(max_length=20, choices=[
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], default='warning')
    is_active = models.BooleanField(default=True, help_text="Whether this threshold is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Alert Threshold"
        verbose_name_plural = "Alert Thresholds"
        unique_together = ['tenant', 'metric_type']
        ordering = ['metric_type']
    
    def __str__(self):
        return f"{self.metric_type} - {self.threshold_percentage}% threshold for {self.tenant.name}"


class TenantDataIsolationAudit(models.Model):
    """Model for tracking tenant data isolation audits"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='data_isolation_audits')
    audit_date = models.DateTimeField(auto_now_add=True)
    auditor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='data_isolation_audits_performed')
    audit_type = models.CharField(max_length=50, choices=[
        ('automated', 'Automated'),
        ('manual', 'Manual'),
        ('compliance', 'Compliance'),
        ('security', 'Security'),
    ], default='automated')
    status = models.CharField(max_length=20, choices=[
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
        ('in_progress', 'In Progress'),
    ], default='in_progress')
    total_records_checked = models.IntegerField(default=0)
    violations_found = models.IntegerField(default=0)
    details = models.JSONField(default=dict, blank=True, help_text="Detailed results of the audit")
    notes = models.TextField(blank=True, help_text="Additional notes about the audit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Data Isolation Audit"
        verbose_name_plural = "Tenant Data Isolation Audits"
        ordering = ['-audit_date']
    
    def __str__(self):
        return f"Data Isolation Audit for {self.tenant.name} on {self.audit_date.strftime('%Y-%m-%d %H:%M')}"


class TenantDataIsolationViolation(models.Model):
    """Model for tracking specific data isolation violations"""
    id = models.AutoField(primary_key=True)
    audit = models.ForeignKey(TenantDataIsolationAudit, on_delete=models.CASCADE, related_name='violations')
    model_name = models.CharField(max_length=100, help_text="Name of the model where violation occurred")
    record_id = models.PositiveIntegerField(help_text="ID of the record that had the violation")
    field_name = models.CharField(max_length=100, help_text="Name of the field that had the violation")
    expected_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='expected_violations')
    actual_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='actual_violations', null=True, blank=True)
    violation_type = models.CharField(max_length=50, choices=[
        ('cross_tenant_access', 'Cross-Tenant Access'),
        ('missing_tenant_filter', 'Missing Tenant Filter'),
        ('incorrect_tenant_assignment', 'Incorrect Tenant Assignment'),
        ('unauthorized_access', 'Unauthorized Access'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    description = models.TextField(help_text="Description of the violation")
    resolution_status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ], default='open')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='violations_resolved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Data Isolation Violation"
        verbose_name_plural = "Tenant Data Isolation Violations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Violation: {self.model_name}:{self.record_id} - {self.violation_type}"







class DataResidencySettings(models.Model):
    """Model for storing data residency preferences per tenant"""
    # Data residency options
    DATA_REGIONS = [
        ('US', 'United States'),
        ('EU', 'European Union'),
        ('GB', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('DE', 'Germany'),
        ('JP', 'Japan'),
        ('SG', 'Singapore'),
        ('IN', 'India'),
        ('BR', 'Brazil'),
        ('GLOBAL', 'Global (No Specific Region)'),
    ]
    
    ENCRYPTION_KEY_LOCATIONS = [
        ('tenant_region', 'Same region as tenant data'),
        ('primary_region', 'Primary region only'),
        ('specific_region', 'Specific region'),
    ]
    
    EXPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xml', 'XML'),
        ('excel', 'Excel'),
    ]
    
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='data_residency_settings')
    
    primary_region = models.CharField(
        max_length=10,
        choices=DATA_REGIONS,
        default='GLOBAL',
        help_text="Primary region where tenant data should be stored"
    )
    
    allowed_regions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of regions where data is allowed to be stored/processed. Empty means only primary region."
    )
    
    # Data encryption settings
    encryption_enabled = models.BooleanField(
        default=True,
        help_text="Whether data encryption is enabled for this tenant"
    )
    
    encryption_key_location = models.CharField(
        max_length=100,
        choices=ENCRYPTION_KEY_LOCATIONS,
        default='tenant_region',
        help_text="Where encryption keys should be stored"
    )
    
    encryption_key_region = models.CharField(
        max_length=10,
        choices=DATA_REGIONS,  # Use the full tuple format
        null=True,
        blank=True,
        help_text="Specific region for encryption key storage if encryption_key_location is 'specific_region'"
    )
    
    # Data retention settings
    data_retention_period_months = models.PositiveIntegerField(
        default=36,
        help_text="Number of months to retain data before automatic deletion"
    )
    
    # Compliance settings
    gdpr_compliant = models.BooleanField(
        default=False,
        help_text="Whether this tenant requires GDPR compliance"
    )
    
    hipaa_compliant = models.BooleanField(
        default=False,
        help_text="Whether this tenant requires HIPAA compliance"
    )
    
    # Backup settings
    backup_regions = models.JSONField(
        default=list,
        blank=True,
        help_text="Regions where backups should be stored. Empty means same as primary region."
    )
    
    # Data transfer settings
    allow_cross_region_transfer = models.BooleanField(
        default=False,
        help_text="Whether cross-region data transfers are allowed for this tenant"
    )
    
    # Data export settings
    export_format = models.CharField(
        max_length=20,
        choices=EXPORT_FORMATS,
        default='json',
        help_text="Preferred format for data exports"
    )
    
    # Legal requirements
    legal_requirements = models.TextField(
        blank=True,
        help_text="Additional legal requirements for data residency"
    )
    
    # Status and enforcement
    is_active = models.BooleanField(
        default=True,
        help_text="Whether data residency controls are active for this tenant"
    )
    
    last_audit_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of last data residency compliance audit"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Data Residency Setting"
        verbose_name_plural = "Data Residency Settings"
        ordering = ['tenant__name']
    
    def __str__(self):
        return f"Data Residency Settings for {self.tenant.name}"
    
    def save(self, *args, **kwargs):
        # Validate that encryption key region is specified if needed
        if (self.encryption_key_location == 'specific_region' and 
            not self.encryption_key_region):
            raise ValueError("Encryption key region must be specified when encryption_key_location is 'specific_region'")
        
        # Ensure primary region is in allowed regions if allowed_regions is specified
        if (self.allowed_regions and 
            self.primary_region not in self.allowed_regions and 
            'GLOBAL' not in self.allowed_regions):
            self.allowed_regions.append(self.primary_region)
        
        super().save(*args, **kwargs)
    
    def is_region_allowed(self, region):
        """Check if a region is allowed for this tenant's data"""
        if not self.allowed_regions:
            return region == self.primary_region
        if 'GLOBAL' in self.allowed_regions:
            return True
        return region in self.allowed_regions
    
    def is_compliant_region(self, region):
        """Check if data placement in a region would be compliant"""
        return self.is_region_allowed(region)
    
    def requires_encryption_in_region(self, region):
        """Check if encryption is required for a specific region"""
        return self.encryption_enabled






# Data Preservation Models (moved from data_preservation.py)
class TenantDataPreservation(models.Model):
    """Model for managing tenant data preservation strategies"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='data_preservation_records')
    preservation_type = models.CharField(max_length=50, choices=[
        ('full_backup', 'Full Backup'),
        ('partial_backup', 'Partial Backup'),
        ('configuration_backup', 'Configuration Backup'),
        ('data_export', 'Data Export'),
        ('snapshot', 'System Snapshot'),
        ('migration_prep', 'Migration Preparation'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    description = models.TextField(blank=True, help_text="Description of the preservation operation")
    backup_location = models.TextField(blank=True, help_text="Location where data is preserved")
    file_size_mb = models.FloatField(default=0.0, help_text="Size of preserved data in MB")
    preservation_date = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this preservation expires")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='data_preservation_created')
    retention_period_days = models.IntegerField(default=30, help_text="Number of days to retain the preservation")
    modules_included = models.JSONField(default=list, blank=True, help_text="List of modules included in preservation")
    notes = models.TextField(blank=True, help_text="Additional notes about the preservation")
    
    class Meta:
        verbose_name = "Tenant Data Preservation"
        verbose_name_plural = "Tenant Data Preservations"
        ordering = ['-preservation_date']
    
    def __str__(self):
        return f"{self.preservation_type} for {self.tenant.name} at {self.preservation_date}"


class TenantDataRestoration(models.Model):
    """Model for tracking tenant data restoration operations"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='data_restoration_records')
    preservation_record = models.ForeignKey(TenantDataPreservation, on_delete=models.SET_NULL, null=True, blank=True, related_name='restorations')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    description = models.TextField(blank=True, help_text="Description of the restoration operation")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='data_restorations_initiated')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='data_restorations_completed')
    modules_restored = models.JSONField(default=list, blank=True, help_text="List of modules restored")
    total_records = models.IntegerField(default=0, help_text="Total number of records to restore")
    restored_records = models.IntegerField(default=0, help_text="Number of records successfully restored")
    failed_records = models.IntegerField(default=0, help_text="Number of records that failed to restore")
    error_log = models.TextField(blank=True, help_text="Log of any errors encountered during restoration")
    progress_percentage = models.FloatField(default=0.0, help_text="Progress percentage of the restoration")
    notes = models.TextField(blank=True, help_text="Additional notes about the restoration")
    
    class Meta:
        verbose_name = "Tenant Data Restoration"
        verbose_name_plural = "Tenant Data Restorations"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Restoration for {self.tenant.name} at {self.started_at}"
    
    def update_progress(self, restored_count, total_count):
        """Update the progress of the restoration"""
        self.restored_records = restored_count
        self.total_records = total_count
        if total_count > 0:
            self.progress_percentage = (restored_count / total_count) * 100
        else:
            self.progress_percentage = 0
        self.save()


class TenantDataPreservationStrategy(models.Model):
    """Model for defining data preservation strategies"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the preservation strategy")
    description = models.TextField(blank=True, help_text="Description of the preservation strategy")
    is_active = models.BooleanField(default=True, help_text="Whether this strategy is active")
    preservation_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('on_demand', 'On Demand'),
    ], default='weekly')
    retention_period_days = models.IntegerField(default=30, help_text="Number of days to retain backups")
    modules_to_preserve = models.JSONField(default=list, blank=True, help_text="List of modules to include in preservation")
    storage_location = models.CharField(max_length=255, default='default', help_text="Storage location for preserved data")
    compression_enabled = models.BooleanField(default=True, help_text="Whether to compress preserved data")
    encryption_enabled = models.BooleanField(default=True, help_text="Whether to encrypt preserved data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='preservation_strategies_created')
    
    class Meta:
        verbose_name = "Tenant Data Preservation Strategy"
        verbose_name_plural = "Tenant Data Preservation Strategies"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.preservation_frequency}"


class TenantDataPreservationSchedule(models.Model):
    """Model for scheduling automated data preservation"""
    id = models.AutoField(primary_key=True)
    strategy = models.ForeignKey(TenantDataPreservationStrategy, on_delete=models.CASCADE, related_name='schedules')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='preservation_schedules')
    next_scheduled_run = models.DateTimeField(help_text="When the next preservation should run")
    last_run = models.DateTimeField(null=True, blank=True, help_text="When the last preservation ran")
    is_active = models.BooleanField(default=True, help_text="Whether this schedule is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Data Preservation Schedule"
        verbose_name_plural = "Tenant Data Preservation Schedules"
        ordering = ['tenant__name', 'next_scheduled_run']
        unique_together = ['strategy', 'tenant']
    
    def __str__(self):
        return f"{self.strategy.name} for {self.tenant.name} - Next: {self.next_scheduled_run}"


# Automated Lifecycle Models (moved from automated_lifecycle.py)
class AutomatedTenantLifecycleRule(models.Model):
    """Model for defining automated tenant lifecycle management rules"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the lifecycle rule")
    description = models.TextField(blank=True, help_text="Description of the lifecycle rule")
    is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    
    # Condition fields
    condition_type = models.CharField(max_length=50, choices=[
        ('usage_based', 'Usage Based'),
        ('time_based', 'Time Based'),
        ('billing_based', 'Billing Based'),
        ('activity_based', 'Activity Based'),
        ('custom', 'Custom Logic'),
    ])
    condition_field = models.CharField(max_length=100, help_text="Field to check for the condition")
    condition_operator = models.CharField(max_length=20, choices=[
        ('equals', 'Equals'),
        ('not_equals', 'Not Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('greater_equal', 'Greater Than or Equal'),
        ('less_equal', 'Less Than or Equal'),
        ('contains', 'Contains'),
        ('not_contains', 'Not Contains'),
    ])
    condition_value = models.CharField(max_length=255, help_text="Value to compare against")
    
    # Action to perform
    action_type = models.CharField(max_length=50, choices=[
        ('suspend', 'Suspend Tenant'),
        ('terminate', 'Terminate Tenant'),
        ('archive', 'Archive Tenant'),
        ('reactivate', 'Reactivate Tenant'),
        ('send_notification', 'Send Notification'),
        ('update_plan', 'Update Plan'),
        ('custom', 'Custom Action'),
    ])
    
    # Action parameters
    action_parameters = models.JSONField(default=dict, blank=True, help_text="Parameters for the action")
    
    # Scheduling and timing
    evaluation_frequency = models.CharField(max_length=20, choices=[
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='daily')
    last_evaluated = models.DateTimeField(null=True, blank=True, help_text="When the rule was last evaluated")
    next_evaluation = models.DateTimeField(default=timezone.now, help_text="When to next evaluate the rule")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifecycle_rules_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Automated Tenant Lifecycle Rule"
        verbose_name_plural = "Automated Tenant Lifecycle Rules"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.action_type}"


class AutomatedTenantLifecycleEvent(models.Model):
    """Model for tracking automated lifecycle events"""
    id = models.AutoField(primary_key=True)
    rule = models.ForeignKey(AutomatedTenantLifecycleRule, on_delete=models.CASCADE, related_name='events')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='automated_lifecycle_events')
    event_type = models.CharField(max_length=50, choices=[
        ('rule_evaluated', 'Rule Evaluated'),
        ('action_taken', 'Action Taken'),
        ('action_skipped', 'Action Skipped'),
        ('error_occurred', 'Error Occurred'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ])
    details = models.TextField(blank=True, help_text="Details about the event")
    triggered_at = models.DateTimeField(default=timezone.now)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='automated_lifecycle_events_executed')
    
    class Meta:
        verbose_name = "Automated Tenant Lifecycle Event"
        verbose_name_plural = "Automated Tenant Lifecycle Events"
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.event_type} for {self.tenant.name} by {self.rule.name}"


class TenantLifecycleWorkflow(models.Model):
    """Model for managing tenant lifecycle workflows"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the workflow")
    description = models.TextField(blank=True, help_text="Description of the workflow")
    workflow_type = models.CharField(max_length=50, choices=[
        ('onboarding', 'Onboarding'),
        ('offboarding', 'Offboarding'),
        ('suspension', 'Suspension'),
        ('reactivation', 'Reactivation'),
        ('termination', 'Termination'),
        ('migration', 'Migration'),
    ])
    is_active = models.BooleanField(default=True, help_text="Whether this workflow is active")
    steps = models.JSONField(default=list, blank=True, help_text="Ordered list of steps in the workflow")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifecycle_workflows_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Lifecycle Workflow"
        verbose_name_plural = "Tenant Lifecycle Workflows"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.workflow_type}"


class TenantLifecycleWorkflowExecution(models.Model):
    """Model for tracking execution of lifecycle workflows"""
    id = models.AutoField(primary_key=True)
    workflow = models.ForeignKey(TenantLifecycleWorkflow, on_delete=models.CASCADE, related_name='executions')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='lifecycle_workflow_executions')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifecycle_workflow_executions')
    current_step = models.IntegerField(default=0, help_text="Current step in the workflow")
    total_steps = models.IntegerField(default=0, help_text="Total number of steps in the workflow")
    progress_percentage = models.FloatField(default=0.0, help_text="Progress percentage of the workflow")
    execution_log = models.TextField(blank=True, help_text="Log of workflow execution")
    error_message = models.TextField(blank=True, help_text="Error message if workflow failed")
    
    class Meta:
        verbose_name = "Tenant Lifecycle Workflow Execution"
        verbose_name_plural = "Tenant Lifecycle Workflow Executions"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.workflow.name} for {self.tenant.name} - {self.status}"
    
    def update_progress(self, current_step, total_steps):
        """Update the progress of the workflow"""
        self.current_step = current_step
        self.total_steps = total_steps
        if total_steps > 0:
            self.progress_percentage = (current_step / total_steps) * 100
        else:
            self.progress_percentage = 0
        self.save()


class TenantSuspensionWorkflow(models.Model):
    """Model for managing the tenant suspension workflow"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='suspension_workflows')
    status = models.CharField(max_length=20, choices=[
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='pending_approval')
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='suspension_workflows_initiated')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='suspension_workflows_approved')
    suspension_reason = models.TextField(help_text="Reason for the suspension")
    approval_notes = models.TextField(blank=True, help_text="Notes from the approver")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    steps_completed = models.JSONField(default=list, blank=True, help_text="List of steps that have been completed")
    total_steps = models.IntegerField(default=5, help_text="Total number of steps in the suspension workflow")
    
    class Meta:
        verbose_name = "Tenant Suspension Workflow"
        verbose_name_plural = "Tenant Suspension Workflows"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Suspension workflow for {self.tenant.name} - {self.status}"
    
    def approve(self, approved_by_user, notes=''):
        """Approve the suspension workflow"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_notes = notes
        self.approved_at = timezone.now()
        self.save()
    
    def complete_step(self, step_name):
        """Mark a step as completed"""
        if step_name not in self.steps_completed:
            self.steps_completed.append(step_name)
        self.save()


class TenantTerminationWorkflow(models.Model):
    """Model for managing the tenant termination workflow"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='termination_workflows')
    status = models.CharField(max_length=20, choices=[
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='pending_approval')
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='termination_workflows_initiated')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='termination_workflows_approved')
    termination_reason = models.TextField(help_text="Reason for the termination")
    approval_notes = models.TextField(blank=True, help_text="Notes from the approver")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    steps_completed = models.JSONField(default=list, blank=True, help_text="List of steps that have been completed")
    total_steps = models.IntegerField(default=7, help_text="Total number of steps in the termination workflow")
    data_preservation_required = models.BooleanField(default=True, help_text="Whether data preservation is required")
    data_preservation_record = models.ForeignKey('tenants.TenantDataPreservation', on_delete=models.SET_NULL, null=True, blank=True, related_name='termination_workflows')
    
    class Meta:
        verbose_name = "Tenant Termination Workflow"
        verbose_name_plural = "Tenant Termination Workflows"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Termination workflow for {self.tenant.name} - {self.status}"
    
    def approve(self, approved_by_user, notes=''):
        """Approve the termination workflow"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_notes = notes
        self.approved_at = timezone.now()
        self.save()
    
    def complete_step(self, step_name):
        """Mark a step as completed"""
        if step_name not in self.steps_completed:
            self.steps_completed.append(step_name)
        self.save()


class TenantRole(TenantAwareModel):
    """
    Tenant-specific roles for internal team members
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)
    is_assignable = models.BooleanField(default=True)
    permissions = models.ManyToManyField('auth.Permission', blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['tenant', 'name']
        ordering = ['order', 'name']
        verbose_name = "Tenant Role"
        verbose_name_plural = "Tenant Roles"
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class TenantTerritory(TenantAwareModel):
    """
    Tenant-specific territories for internal team members
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    region_code = models.CharField(max_length=50, blank=True)
    country_codes = models.JSONField(default=list, blank=True, help_text="List of country codes covered by this territory")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['tenant', 'name']
        ordering = ['order', 'name']
        verbose_name = "Tenant Territory"
        verbose_name_plural = "Tenant Territories"
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class TenantMember(TenantAwareModel):
    """
    Internal team members within a tenant
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_member')
    role = models.ForeignKey(TenantRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    territory = models.ForeignKey(TenantTerritory, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # Employment details
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('onboarding', 'Onboarding'),
        ('leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ], default='onboarding')
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    
    # Performance metrics
    quota_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    quota_period = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], default='quarterly')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, 
                                        help_text="Commission rate (e.g. 10.0 for 10%)")
    
    # Territory performance metrics
    territory_performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                     help_text="Performance score within assigned territory (0-100)")
    territory_quota_attainment = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                    help_text="Percentage of territory quota attained")
    territory_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                   help_text="Lead to opportunity conversion rate in territory (%)")
    territory_revenue_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, 
                                                        help_text="Revenue contribution to assigned territory")
    
    # Contact information
    phone = models.CharField(max_length=50, blank=True)
    
    class Meta:
        unique_together = ['tenant', 'user']
        verbose_name = "Tenant Member"
        verbose_name_plural = "Tenant Members"
    
    def __str__(self):
        return f"{self.user.email} - {self.tenant.name}"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.email
