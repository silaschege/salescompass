from django.db import models
from core.models import User
from core.object_permissions import ObjectPermissionPolicy

class TenantMemberObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permissions for TenantMember
    """
    @classmethod
    def can_view(cls, user: User, obj) -> bool:
        if user.is_superuser:
            return True
        # Users can view members of their own tenant
        return obj.tenant_id == user.tenant_id
    
    @classmethod
    def can_change(cls, user: User, obj) -> bool:
        if user.is_superuser:
            return True
        # Only tenant admins or users with specific permissions can change members
        if hasattr(user, 'tenant_admin') and user.tenant_admin == obj.tenant:
            return True
        # Check if user is a tenant admin (different implementation might be needed based on system design)
        # For now, let's stick to the basic tenant isolation
        return (user.tenant_id == obj.tenant_id and 
                user.has_perm('tenants.change_tenantmember'))
    
    @classmethod
    def can_delete(cls, user: User, obj) -> bool:
        if user.is_superuser:
            return True
        # Only tenant admins can delete members
        if hasattr(user, 'tenant_admin') and user.tenant_admin == obj.tenant:
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset) -> models.QuerySet:
        # Users can only see members of their own tenant
        if user.is_superuser:
            return queryset
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()
