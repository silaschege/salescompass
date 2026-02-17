
"""
Seed initial access control entries for all registered apps in SalesCompass.

This command creates the required entries for each app in the apps registry:
1. Creates AccessControl definitions (Entitlement, Feature Flag, Permission) for each app.
2. Assigns these controls to all existing tenants and their roles.

Usage:
    python manage.py seed_access_control_entries
"""
from django.core.management.base import BaseCommand
from access_control.models import AccessControl, TenantAccessControl, RoleAccessControl
from access_control.role_models import Role
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Seed initial access control entries for all registered apps'

    def handle(self, *args, **options):
        # Import the apps registry
        from core.apps_registry import AVAILABLE_APPS
        
        created_count = 0
        updated_count = 0

        # Get all existing tenants
        tenants = Tenant.objects.all()
        
        if not tenants.exists():
            self.stdout.write(
                self.style.WARNING('No tenants found. Please create at least one tenant first.')
            )
            # We can still check for definition creation, but skipping assignments for now.
        else:
            # Ensure default roles exist for each tenant
            for tenant in tenants:
                for role_data in Role.get_default_roles():
                    role, created = Role.objects.get_or_create(
                        name=role_data['name'],
                        tenant=tenant,
                        defaults={
                            'description': role_data['description'],
                            'is_system_role': role_data['is_system_role'],
                            'is_assignable': role_data['is_assignable'],
                        }
                    )
                    if created:
                        self.stdout.write(f"Created default role '{role.name}' for tenant {tenant.name}")

        for app in AVAILABLE_APPS:
            app_id = app['id']
            app_name = app['name']
            app_description = app.get('description', f'Access to {app_name} module')

            # 1. Create AccessControl DEFINITIONS
            
            # Entitlement Definition
            entitlement_key = f"{app_id}.entitlement"
            entitlement_def, created = AccessControl.objects.update_or_create(
                key=entitlement_key,
                defaults={
                    'name': f'{app_name} Entitlement',
                    'description': f'{app_description} - Entitlement',
                    'access_type': 'entitlement',
                    'default_enabled': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created Definition: {entitlement_def.name}'))

            # Feature Flag Definition
            feature_key = f"{app_id}.feature"
            feature_def, created = AccessControl.objects.update_or_create(
                key=feature_key,
                defaults={
                    'name': f'{app_name} Feature',
                    'description': f'{app_description} - Feature Toggle',
                    'access_type': 'feature_flag',
                    'default_enabled': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created Definition: {feature_def.name}'))

            # Permission Definition (General access)
            permission_key = f"{app_id}.permission" 
            permission_def, created = AccessControl.objects.update_or_create(
                key=permission_key,
                defaults={
                    'name': f'{app_name} Access',
                    'description': f'{app_description} - General Access Permission',
                    'access_type': 'permission',
                    'default_enabled': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created Definition: {permission_def.name}'))

            # 2. Assign to Tenants (Entitlements & Features)
            for tenant in tenants:
                # Assign Entitlement
                TenantAccessControl.objects.get_or_create(
                    tenant=tenant,
                    access_control=entitlement_def,
                    defaults={'is_enabled': True}
                )
                
                # Assign Feature Flag
                TenantAccessControl.objects.get_or_create(
                    tenant=tenant,
                    access_control=feature_def,
                    defaults={'is_enabled': True}
                )
                
            # 3. Assign to Roles (Permissions)
            # For each tenant, get roles and assign permission
            for tenant in tenants:
                # Admin Role gets everything
                admin_role = Role.objects.filter(tenant=tenant, name='Tenant Admin').first()
                if admin_role:
                    RoleAccessControl.objects.get_or_create(
                        role=admin_role,
                        access_control=permission_def,
                        defaults={'is_enabled': True}
                    )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Access control seeding completed.'
            )
        )
