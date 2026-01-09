from django.contrib.auth.models import Permission
from .models import AccessControl

class UnifiedAccessController:
    """
    Single controller for all access control decisions
    """
    
    @classmethod
    def has_access(cls, user, resource_key, action='access'):
        """
        Check if user has access to a resource with a specific action
        """
        # Check system-level permissions first
        if user.is_superuser:
            return True
        
        # Check direct Django permissions
        if cls._has_django_permission(user, resource_key, action):
            return True
        
        # Check unified access controls
        return cls._has_unified_access(user, resource_key, action)
    
    @classmethod
    def _has_django_permission(cls, user, resource_key, action):
        """
        Check traditional Django permissions
        """
        try:
            if '.' in resource_key:
                app_label, model_name = resource_key.split('.', 1)
                perm_codename = f"{app_label}.{action}_{model_name}"
                return user.has_perm(perm_codename)
            return False
        except ValueError:
            return False
    
    @classmethod
    def _has_unified_access(cls, user, resource_key, action='access'):
        """
        Check unified access controls
        """
        # Check tenant-level entitlements
        tenant_access = AccessControl.objects.filter(
            key=resource_key,
            scope_type='tenant',
            tenant=user.tenant,
            is_enabled=True,
            access_type='entitlement'
        ).first()
        
        if tenant_access:
            # Check feature toggle for tenant
            feature_toggle = AccessControl.objects.filter(
                key=resource_key,
                scope_type='tenant',
                tenant=user.tenant,
                is_enabled=True,
                access_type='feature_flag'
            ).first()
            
            if feature_toggle and cls._is_feature_enabled_for_user(feature_toggle, user):
                # Check role or user permissions
                role_access = AccessControl.objects.filter(
                    key=resource_key,
                    scope_type='role',
                    role=user.role,
                    is_enabled=True,
                    access_type='permission'
                ).first()
                
                if role_access:
                    return True
                
                user_access = AccessControl.objects.filter(
                    key=resource_key,
                    scope_type='user',
                    user=user,
                    is_enabled=True,
                    access_type='permission'
                ).first()
                
                if user_access:
                    return True
        
        # If no entitlement restriction found, check if it's purely a permission or feature flag for user/role
        # The logic in the snippet seemed to imply entitlement is prerequisite.
        # But what if there is no entitlement rule? Does that mean access denied or allowed?
        # Assuming "Unified" means we check all.
        # If no specific entitlement record exists, maybe we fallback to basic permission?
        # User's provided code returns False if tenant_access is not found. 
        # But this implies EVERYTHING needs an entitlement. 
        # I will stick to the user's logic for now but maybe add a check for non-entitled features.
        
        # Actually, let's look at the user snippet again. 
        # It ONLY checks entitlement. If not found, returns False. 
        # This implies a "closed by default" system where you NEED an entitlement. 
        # However, for basic permissions, maybe we should check if any permission exists even without entitlement?
        # But I will implement EXACTLY what the user provided to be safe.
        
        return False
    
    @classmethod
    def _is_feature_enabled_for_user(cls, feature_toggle, user):
        """
        Check if feature is enabled for user (with rollout percentage logic)
        """
        if feature_toggle.rollout_percentage >= 100:
            return True
        
        # Implement rollout percentage logic based on user ID or tenant
        user_hash = hash(f"{user.id}_{feature_toggle.key}") % 100
        return user_hash < feature_toggle.rollout_percentage
    
    @classmethod
    def get_available_resources(cls, user):
        """
        Get list of resources available to user
        """
        available = []
        
        if not user.tenant:
            return available

        # Get all entitlements for user's tenant
        entitlements = AccessControl.objects.filter(
            scope_type='tenant',
            tenant=user.tenant,
            access_type='entitlement',
            is_enabled=True
        )
        
        for entitlement in entitlements:
            # Check if feature toggle allows access
            feature_toggle = AccessControl.objects.filter(
                key=entitlement.key,
                scope_type='tenant',
                tenant=user.tenant,
                access_type='feature_flag',
                is_enabled=True
            ).first()
            
            # If no feature toggle exists, is it enabled? User logic implies checking if feature_toggle exists AND is enabled.
            # But earlier logic: `if feature_toggle and ...`. 
            # If feature_toggle is missing, it skips. So you need BOTH entitlement and feature flag?
            # Or maybe feature flag is optional?
            # User code: `if feature_toggle and cls._is_feature_enabled_for_user...`
            # This implies if toggle is missing, access is DENIED via this path.
            # So you need Entitlement AND Feature Flag.
            
            if feature_toggle and cls._is_feature_enabled_for_user(feature_toggle, user):
                # Check if user/role has permission
                has_permission = (
                    AccessControl.objects.filter(
                        key=entitlement.key,
                        scope_type='role',
                        role=user.role,
                        access_type='permission',
                        is_enabled=True
                    ).exists() or
                    AccessControl.objects.filter(
                        key=entitlement.key,
                        scope_type='user',
                        user=user,
                        access_type='permission',
                        is_enabled=True
                    ).exists()
                )
                
                if has_permission:
                    available.append({
                        'key': entitlement.key,
                        'name': entitlement.name,
                        'description': entitlement.description
                    })
        
        return available
