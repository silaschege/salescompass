
from django.core.management.base import BaseCommand
import json
from core.models import User
from tenants.models import Tenant
from access_control.models import AccessControl, TenantAccessControl, RoleAccessControl, UserAccessControl
from access_control.role_models import Role
from access_control.controller import UnifiedAccessController

class Command(BaseCommand):
    help = 'Verifies Advanced Authorization (Role Hierarchy and Field-Level Permissions)'

    def handle(self, *args, **options):
        self.stdout.write("--- Verifying Advanced Authorization ---")
        
        # Setup Data
        tenant, _ = Tenant.objects.get_or_create(name="Hierarchy Test Tenant", subdomain="hierarchy-test")
        
        # 1. Create Roles (Parent -> Child)
        parent_role, _ = Role.objects.get_or_create(name="Parent Role", tenant=tenant)
        child_role, _ = Role.objects.get_or_create(name="Child Role", tenant=tenant, parent=parent_role)
        self.stdout.write(f"Created Hierarchy: {child_role.name} -> {parent_role.name}")
        
        # 2. Create User assigned to Child Role
        user, _ = User.objects.get_or_create(email="child_role_user@example.com", defaults={'username': 'child_role_user'})
        user.set_password('password')
        user.tenant = tenant
        user.role = child_role
        user.save()
        self.stdout.write(f"Created User: {user.email} with Role: {user.role.name}")
        
        # 3. Define Access Control
        permission_x, _ = AccessControl.objects.get_or_create(
            key="permission.hierarchy_test", 
            defaults={'name': 'Hierarchy Permission', 'access_type': 'permission'}
        )
        
        # 4. Assign Permission to PARENT Role (with config)
        RoleAccessControl.objects.get_or_create(
            role=parent_role, 
            access_control=permission_x,
            defaults={'is_enabled': True, 'config_data': {'level': 'parent', 'inherited': True}}
        )
        self.stdout.write(f"Assigned '{permission_x.key}' to Parent Role")
        
        # 5. Verify Access (Should be inherited)
        has_access = UnifiedAccessController.has_access(user, "permission.hierarchy_test")
        status = "PASS" if has_access else "FAIL"
        self.stdout.write(f"User Access Check (Inherited): {status} (Expected: True)")
        
        if not has_access:
            _, reason = UnifiedAccessController.has_access_with_reason(user, "permission.hierarchy_test")
            self.stdout.write(f"Reason: {reason}")

        # 6. Verify Config Merging
        self.stdout.write("\n--- Verifying Config Merging ---")
        
        # Add User-specific assignment with override
        UserAccessControl.objects.get_or_create(
            user=user,
            access_control=permission_x,
            defaults={'is_enabled': True, 'config_data': {'level': 'user', 'user_specific': True}}
        )
        self.stdout.write("Added direct User assignment with config override.")
        
        # Check Access Config
        config = UnifiedAccessController.get_access_config(user, "permission.hierarchy_test")
        self.stdout.write(f"Merged Config: {json.dumps(config, indent=2)}")
        
        if config.get('level') == 'user' and config.get('inherited') is True:
            self.stdout.write("Config Merge: PASS (User overrode 'level', preserved 'inherited')")
        else:
            self.stdout.write("Config Merge: FAIL or Partial. Check output above.")

