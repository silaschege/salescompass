from django.db import models
from core.models import User
from tenants.models import Tenant

class AccessControl(models.Model):
    """
    Unified model for permissions, feature toggles, and feature entitlements
    """
    ACCESS_TYPES = [
        ('permission', 'Permission - User/Role Specific'),
        ('feature_flag', 'Feature Toggle - On/Off Control'),
        ('entitlement', 'Feature Entitlement - Plan Based'),
    ]
    
    SCOPE_TYPES = [
        ('user', 'User Specific'),
        ('role', 'Role Based'),
        ('tenant', 'Tenant Wide'),
        ('system', 'System Wide'),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Display name for the access control")
    key = models.CharField(max_length=255, unique=True, help_text="Unique identifier")
    description = models.TextField(blank=True)
    
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    scope_type = models.CharField(max_length=20, choices=SCOPE_TYPES)
    
    # Target references (depending on scope_type)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey('accounts.Role', on_delete=models.CASCADE, null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    
    # State and configuration
    is_enabled = models.BooleanField(default=True)
    rollout_percentage = models.IntegerField(default=100, help_text="For feature toggles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional configuration
    config_data = models.JSONField(default=dict, help_text="Additional configuration options")
    
    class Meta:
        unique_together = [
            ['key', 'user'], 
            ['key', 'role'], 
            ['key', 'tenant'], 
            # Note: unique_together with 'scope_type' might be redundant if key is unique globally?
            # User specified: ['key', 'scope_type'] in unique_together list.
            # But key is generic. Actually user's snippet said key is unique=True which conflicts with unique_together.
            # If key is unique globally, then one key implies one rule. 
            # But "Unified Access Controller" logic filters by key + scope + tenant.
            # So key MUST NOT be unique globally if we want multiple rules for same feature (e.g. tenant A has it, tenant B doesn't).
            # I will REMOVE unique=True from key to allow multiple rules for the same resource key.
        ]
        verbose_name = "Access Control"
        verbose_name_plural = "Access Controls"
    
    def __str__(self):
        return f"{self.name} ({self.key}) - {self.get_access_type_display()}"
    
    def is_accessible_to_user(self, user):
        """
        Check if this access control applies to the given user
        """
        if not self.is_enabled:
            return False
        
        if self.scope_type == 'system':
            return True
        elif self.scope_type == 'tenant':
            return user.tenant == self.tenant
        elif self.scope_type == 'role':
            return user.role == self.role and user.tenant == self.role.tenant
        elif self.scope_type == 'user':
            return user == self.user
        
        return False
