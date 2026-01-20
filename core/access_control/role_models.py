"""
Role model for access control.

This module contains the Role model which was consolidated from accounts app
into access_control for unified permission management.
"""
from django.db import models
from tenants.models import Tenant


class Role(models.Model):
    """
    Model for managing user roles within the access control system.
    Roles are now tenant-aware for proper multi-tenant isolation.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, help_text="Display name for the role")
    description = models.TextField(blank=True)
    
    # Tenant association for multi-tenant support
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='roles',
        help_text="The tenant this role belongs to. Null for system-wide roles."
    )
    
    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent role from which permissions are inherited."
    )
    
    # Role metadata
    is_system_role = models.BooleanField(
        default=False, 
        help_text="System roles cannot be deleted and are available to all tenants."
    )
    is_assignable = models.BooleanField(
        default=True,
        help_text="Whether this role can be assigned to users."
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['name']
        unique_together = ['name', 'tenant']
    
    def __str__(self):
        if self.tenant:
            return f"{self.name} ({self.tenant.name})"
        return f"{self.name} (System)"
    
    @classmethod
    def get_default_roles(cls):
        """
        Returns the list of default roles to be created for new tenants.
        """
        return [
            {'name': 'Tenant Admin', 'description': 'Full administrative access to tenant resources.', 'is_system_role': True, 'is_assignable': True},
            {'name': 'Standard User', 'description': 'Standard access to tenant features.', 'is_system_role': False, 'is_assignable': True},
            {'name': 'Read Only', 'description': 'Read-only access to tenant data.', 'is_system_role': False, 'is_assignable': True},
        ]
