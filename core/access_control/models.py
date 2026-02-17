
from django.db import models
from core.models import User
from tenants.models import Tenant
from .role_models import Role


class AccessControl(models.Model):
    """
    Master definition for permissions, feature toggles, and feature entitlements.
    Does NOT store assignments to specific tenants/users/roles.
    """
    ACCESS_TYPES = [
        ('permission', 'Permission - User/Role Specific'),
        ('feature_flag', 'Feature Toggle - On/Off Control'),
        ('entitlement', 'Feature Entitlement - Plan Based'),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Display name for the access control")
    key = models.CharField(max_length=255, unique=True, help_text="Unique identifier") 
    description = models.TextField(blank=True)
    
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    
    # Defaults
    default_enabled = models.BooleanField(default=True, help_text="Default state when assigned")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Valid configuration schema (optional)
    config_schema = models.JSONField(default=dict, blank=True, help_text="JSON Schema for config_data validation")
    
    class Meta:
        verbose_name = "Access Control Definition"
        verbose_name_plural = "Access Control Definitions"
    
    def __str__(self):
        return f"{self.name} ({self.key}) [{self.get_access_type_display()}]"


class TenantAccessControl(models.Model):
    """
    Assigns an Access Control to a Tenant (Entitlements, Feature Flags)
    """
    id = models.AutoField(primary_key=True)
    access_control = models.ForeignKey(AccessControl, on_delete=models.CASCADE, related_name='tenant_assignments')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='access_controls')
    
    is_enabled = models.BooleanField(default=True)
    config_data = models.JSONField(default=dict, blank=True, help_text="Configuration specific to this tenant assignment")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['access_control', 'tenant'], name='unique_tenant_access_assignment')
        ]
        verbose_name = "Tenant Access Assignment"
        verbose_name_plural = "Tenant Access Assignments"

    def __str__(self):
        return f"{self.tenant.name} -> {self.access_control.name}"


class RoleAccessControl(models.Model):
    """
    Assigns an Access Control (Permission) to a Role
    """
    id = models.AutoField(primary_key=True)
    access_control = models.ForeignKey(AccessControl, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    
    is_enabled = models.BooleanField(default=True)
    config_data = models.JSONField(default=dict, blank=True, help_text="Configuration specific to this role assignment (e.g. field-level permissions)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['access_control', 'role'], name='unique_role_access_assignment')
        ]
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"
        
    def __str__(self):
        return f"{self.role.name} -> {self.access_control.name}"


class UserAccessControl(models.Model):
    """
    Assigns an Access Control (Permission) directly to a User
    """
    id = models.AutoField(primary_key=True)
    access_control = models.ForeignKey(AccessControl, on_delete=models.CASCADE, related_name='user_assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_controls')
    
    is_enabled = models.BooleanField(default=True)
    config_data = models.JSONField(default=dict, blank=True, help_text="Configuration specific to this user assignment")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['access_control', 'user'], name='unique_user_access_assignment')
        ]
        verbose_name = "User Permission"
        verbose_name_plural = "User Permissions"

    def __str__(self):
        return f"{self.user.username} -> {self.access_control.name}"