from django.db import models
from django.utils.text import slugify
import uuid

class Tenant(models.Model):
    """
    Represents a tenant (organization) in the system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Billing
    plan = models.ForeignKey('billing.Plan', on_delete=models.SET_NULL, null=True, blank=True)
    subscription_status = models.CharField(max_length=50, default='trialing')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Branding & Customization
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#6f42c1', help_text="Hex color code")
    secondary_color = models.CharField(max_length=7, default='#e3e6f3', help_text="Hex color code")
    business_hours = models.JSONField(default=dict, blank=True, help_text="e.g., {'monday': '9:00-17:00', ...}")
    default_currency = models.CharField(max_length=3, default='USD', help_text="ISO 4217 currency code")
    date_format = models.CharField(max_length=20, default='%Y-%m-%d', help_text="Python date format string")
    time_zone = models.CharField(max_length=50, default='UTC')
    
    # Settings
    settings = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    # Lifecycle Management Methods
    def suspend(self, reason=""):
        """Suspend the tenant account"""
        self.subscription_status = 'suspended'
        if reason:
            self.settings['suspension_reason'] = reason
        self.is_active = False
        self.save()
    
    def archive(self):
        """Archive the tenant account"""
        self.subscription_status = 'archived'
        self.is_active = False
        self.save()
    
    def reactivate(self):
        """Reactivate a suspended or archived tenant"""
        self.subscription_status = 'active'
        self.is_active = True
        if 'suspension_reason' in self.settings:
            del self.settings['suspension_reason']
        self.save()
    
    def soft_delete(self):
        """Soft delete the tenant (mark as inactive)"""
        self.is_active = False
        self.subscription_status = 'deleted'
        self.save()
    
    # Status Check Properties
    @property
    def is_suspended(self):
        return self.subscription_status == 'suspended'
    
    @property
    def is_archived(self):
        return self.subscription_status == 'archived'
    
    @property
    def is_trial(self):
        return self.subscription_status == 'trialing'
    
    @property
    def has_active_subscription(self):
        return self.subscription_status == 'active' and self.is_active
    
    # Branding Methods
    def update_branding(self, primary_color=None, secondary_color=None, logo=None):
        """Update tenant branding configuration"""
        if primary_color:
            self.primary_color = primary_color
        if secondary_color:
            self.secondary_color = secondary_color
        if logo:
            self.logo = logo
        self.save()
    
    # Domain Management
    def set_custom_domain(self, domain):
        """Assign a custom domain to the tenant"""
        self.domain = domain
        self.save()
    
    def remove_custom_domain(self):
        """Remove custom domain"""
        self.domain = None
        self.save()
    
    # Settings Management
    def update_settings(self, **kwargs):
        """Update tenant settings"""
        self.settings.update(kwargs)
        self.save()
    
    def get_setting(self, key, default=None):
        """Get a specific setting value"""
        return self.settings.get(key, default)
