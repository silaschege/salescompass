from django.contrib.auth.models import Permission
from .models import AccessControl, TenantAccessControl, RoleAccessControl, UserAccessControl
from django.db.models import Q
from django.core.cache import cache
import logging
from billing.plan_access_service import PlanAccessService

logger = logging.getLogger(__name__)

class UnifiedAccessController:
    """
    Single controller for all access control decisions
    """
    
    @classmethod
    def has_access(cls, user, resource_key, action='access'):
        """
        Check if user has access to a resource with a specific action
        """
        cache_key = f"access_{user.id}_{resource_key}_{action}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check system-level permissions first
        if user.is_superuser:
            result = True
        else:
            # Check direct Django permissions
            if cls._has_django_permission(user, resource_key, action):
                result = True
            else:
                # Check unified access controls
                result = cls._has_unified_access(user, resource_key, action)
        
        # Cache for 5 minutes (300 seconds)
        cache.set(cache_key, result, 300)
        return result
    
    @classmethod
    def has_access_with_reason(cls, user, resource_key, action='access'):
        """
        Check access and return detailed reason for debugging
        """
        reasons = []
        
        # Check system-level permissions first
        if user.is_superuser:
            return True, ["User is superuser"]
        
        # Check direct Django permissions
        if cls._has_django_permission(user, resource_key, action):
            return True, ["Django permission granted"]
        
        # Check unified access controls
        result, reason_details = cls._has_unified_access_with_reason(user, resource_key, action)
        reasons.extend(reason_details)
        
        return result, reasons

    @classmethod
    def get_user_permissions_summary(cls, user):
        """
        Get all permissions for a user for debugging purposes
        """
        permissions = {
            'django_permissions': [],
            'unified_permissions': [],
            'feature_flags': [],
            'entitlements': []
        }
        
        # Get Django permissions
        permissions['django_permissions'] = list(user.user_permissions.values_list('codename', flat=True))
        
        # Get Tenant Entitlements/Flags
        if user.tenant:
            tenant_assignments = TenantAccessControl.objects.filter(
                tenant=user.tenant, 
                is_enabled=True
            ).select_related('access_control')
            
            for assignment in tenant_assignments:
                ac = assignment.access_control
                info = {'key': ac.key, 'name': ac.name, 'type': ac.access_type, 'source': 'tenant'}
                if ac.access_type == 'entitlement':
                    permissions['entitlements'].append(info)
                elif ac.access_type == 'feature_flag':
                    permissions['feature_flags'].append(info)
        
        # Get Role Permissions
        if user.role:
            role_assignments = RoleAccessControl.objects.filter(
                role=user.role, 
                is_enabled=True
            ).select_related('access_control')
            for assignment in role_assignments:
                ac = assignment.access_control
                if ac.access_type == 'permission':
                    permissions['unified_permissions'].append({
                        'key': ac.key, 'name': ac.name, 'type': ac.access_type, 'source': 'role'
                    })

        # Get User Permissions
        user_assignments = UserAccessControl.objects.filter(
            user=user, 
            is_enabled=True
        ).select_related('access_control')
        for assignment in user_assignments:
            ac = assignment.access_control
            if ac.access_type == 'permission':
                permissions['unified_permissions'].append({
                    'key': ac.key, 'name': ac.name, 'type': ac.access_type, 'source': 'user'
                })
        
        return permissions

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
            logger.warning(f"Invalid resource key format: {resource_key}")
            return False
    
    @classmethod
    def get_access_config(cls, user, resource_key):
        """
        Get the consolidated configuration for a resource (Field-Level Permissions)
        Target: User overrides Role, Role overrides Tenant
        """
        config = {}
        
        try:
            access_def = AccessControl.objects.get(key=resource_key)
        except AccessControl.DoesNotExist:
            return config

        # 1. Tenant Config (Base)
        if user.tenant:
            tenant_assign = TenantAccessControl.objects.filter(
                tenant=user.tenant, access_control=access_def, is_enabled=True
            ).first()
            if tenant_assign and tenant_assign.config_data:
                config.update(tenant_assign.config_data)

        # 2. Role Config (Hierarchy: Parent -> Child)
        if user.role:
            # Get role hierarchy from top (root) to bottom (current)
            hierarchy = []
            current = user.role
            while current:
                hierarchy.insert(0, current)
                current = current.parent
            
            # Apply configs down the chain
            for role in hierarchy:
                role_assign = RoleAccessControl.objects.filter(
                    role=role, access_control=access_def, is_enabled=True
                ).first()
                if role_assign and role_assign.config_data:
                    config.update(role_assign.config_data)

        # 3. User Config (Override)
        user_assign = UserAccessControl.objects.filter(
            user=user, access_control=access_def, is_enabled=True
        ).first()
        if user_assign and user_assign.config_data:
            config.update(user_assign.config_data)
            
        return config

    @classmethod
    def _has_unified_access(cls, user, resource_key, action='access'):
        """
        Check unified access controls with hierarchy support
        """
        # 0. Get the Definition
        try:
            access_def = AccessControl.objects.get(key=resource_key)
        except AccessControl.DoesNotExist:
            return False

        # 1. Check Tenant Entitlement/Feature Flag
        if user.tenant and (access_def.access_type in ['entitlement', 'feature_flag']):
            return TenantAccessControl.objects.filter(
                tenant=user.tenant,
                access_control=access_def,
                is_enabled=True
            ).exists()

        if access_def.access_type == 'permission':
            # 2. Check User Assignment (Direct)
            if UserAccessControl.objects.filter(
                user=user, access_control=access_def, is_enabled=True
            ).exists():
                return True
            
            # 3. Check Role Assignment (with Hierarchy)
            if user.role and user.tenant:
                current_role = user.role
                while current_role:
                    if RoleAccessControl.objects.filter(
                        role=current_role, access_control=access_def, is_enabled=True
                    ).exists():
                        return True
                    current_role = current_role.parent

            # 4. Check Tenant Assignment (Cascade)
            # If a permission is assigned to the Tenant, we treat it as available to all users in that tenant
            if user.tenant:
                if TenantAccessControl.objects.filter(
                    tenant=user.tenant, access_control=access_def, is_enabled=True
                ).exists():
                    return True

        # 5. Check Billing System Fallback (If key starts with 'billing.')
        if resource_key.startswith('billing.') and user.tenant and user.tenant.plan:
            # Simple check: if it's billing.dashboard, just check if billing module is enabled
            if resource_key == 'billing.dashboard':
                return PlanAccessService.get_module_access(user.tenant.plan, 'billing')
            
            # For other billing keys, could check specific features if mapped
            # For now, if they have 'billing' module, give them basic billing access
            # unless it's a specific admin config key
            if '.admin.' not in resource_key:
                return PlanAccessService.get_module_access(user.tenant.plan, 'billing')
        
        return False

    @classmethod
    def _has_unified_access_with_reason(cls, user, resource_key, action='access'):
        reasons = []
        try:
            access_def = AccessControl.objects.get(key=resource_key)
        except AccessControl.DoesNotExist:
            return False, ["Resource definition not found"]

        reasons.append(f"Checking access for {resource_key} ({access_def.access_type})")

        if access_def.access_type in ['entitlement', 'feature_flag']:
             if not user.tenant:
                 return False, ["User has no tenant"]
             
             assignment = TenantAccessControl.objects.filter(
                 tenant=user.tenant, access_control=access_def, is_enabled=True
             ).first()
             
             if assignment:
                 return True, ["Tenant has active assignment"]
             else:
                 return False, ["Tenant does NOT have assignment"]

        if access_def.access_type == 'permission':
            # Check User
            if UserAccessControl.objects.filter(user=user, access_control=access_def, is_enabled=True).exists():
                return True, ["User assigned directly"]
            
            # Check Role Hierarchy
            if user.role:
                current_role = user.role
                while current_role:
                    if RoleAccessControl.objects.filter(role=current_role, access_control=access_def, is_enabled=True).exists():
                        return True, [f"Inherited from Role: {current_role.name}"]
                    current_role = current_role.parent
                reasons.append("No permission found in role hierarchy")
            
            # Check Tenant Assignment
            if user.tenant:
                if TenantAccessControl.objects.filter(tenant=user.tenant, access_control=access_def, is_enabled=True).exists():
                    return True, ["Inherited from Tenant Assignment"]
                reasons.append("No permission found on Tenant")

        return False, ["No permission found"]
    
    @classmethod
  
    def get_available_resources(cls, user):
        """
        Get list of resources available to user
        """
        available = []
        
        if not user.tenant:
            return available

        # Get Tenant Entitlements/Features
        tenant_assignments = TenantAccessControl.objects.filter(
            tenant=user.tenant,
            is_enabled=True
        ).select_related('access_control')
        
        for assign in tenant_assignments:
            ac = assign.access_control
            if ac.access_type in ['entitlement', 'feature_flag']:
                # Extract base key (e.g., 'leads.entitlement' -> 'leads')
                # This ensures keys match the app IDs in AVAILABLE_APPS
                base_key = ac.key.rsplit('.', 1)[0] if '.' in ac.key else ac.key
                available.append({
                        'key': base_key,
                        'name': ac.name,
                        'description': ac.description
                })

        # ALSO check permissions assigned to user's role
        if user.role:
            # Get role hierarchy permissions
            current_role = user.role
            while current_role:
                role_assignments = RoleAccessControl.objects.filter(
                    role=current_role,
                    is_enabled=True
                ).select_related('access_control')
                
                for assign in role_assignments:
                    ac = assign.access_control
                    if ac.access_type == 'permission':
                        base_key = ac.key.rsplit('.', 1)[0] if '.' in ac.key else ac.key
                        # Only add if not already in available list
                        if not any(item['key'] == base_key for item in available):
                            available.append({
                                'key': base_key,
                                'name': ac.name,
                                'description': ac.description
                            })
                current_role = current_role.parent

        # ALSO check direct user permissions
        user_assignments = UserAccessControl.objects.filter(
            user=user,
            is_enabled=True
        ).select_related('access_control')

        for assign in user_assignments:
            ac = assign.access_control
            if ac.access_type == 'permission':
                base_key = ac.key.rsplit('.', 1)[0] if '.' in ac.key else ac.key
                # Only add if not already in available list
                if not any(item['key'] == base_key for item in available):
                    available.append({
                        'key': base_key,
                        'name': ac.name,
                        'description': ac.description
                    })

        return available
    @classmethod
    def grant_access(cls, user, resource_key, access_type='permission', scope_type='user', **kwargs):
        """
        Grant access helper (updated for new models)
        """
        # Get or create definition
        access_def, _ = AccessControl.objects.get_or_create(
            key=resource_key,
            defaults={
                'name': kwargs.get('name', resource_key),
                'access_type': access_type
            }
        )
        
        if scope_type == 'user':
            UserAccessControl.objects.create(user=user, access_control=access_def, is_enabled=True)
        elif scope_type == 'role' and kwargs.get('role'):
            RoleAccessControl.objects.create(role=kwargs.get('role'), access_control=access_def, is_enabled=True)
        elif scope_type == 'tenant' and kwargs.get('tenant'):
            TenantAccessControl.objects.create(tenant=kwargs.get('tenant'), access_control=access_def, is_enabled=True)

        # Clear cache
        cache.delete_pattern(f"access_{user.id}_*_*")
        
        return access_def

    @classmethod
    def revoke_access(cls, user, resource_key, scope_type='user'):
        """
        Revoke access helper
        """
        try:
            access_def = AccessControl.objects.get(key=resource_key)
             
            if scope_type == 'user':
                UserAccessControl.objects.filter(user=user, access_control=access_def).delete()
            # ... implement others
            
            cache.delete_pattern(f"access_{user.id}_*_*")
            return True
        except AccessControl.DoesNotExist:
            return False