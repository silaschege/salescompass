
"""
Seed initial access control entries for all registered apps in SalesCompass.

This command creates the required entries for each app in the apps registry:
1. An entitlement record (access_type='entitlement', scope_type='tenant')
2. A feature flag record (access_type='feature_flag', scope_type='tenant')
3. A permission record for each role (access_type='permission', scope_type='role')

Usage:
    python manage.py seed_access_control_entries
"""
from django.core.management.base import BaseCommand
from access_control.models import AccessControl
from accounts.models import Role
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Seed initial access control entries for all registered apps'

    def handle(self, *args, **options):
        # Import the apps registry
        from core.apps_registry import AVAILABLE_APPS
        
        created_count = 0
        updated_count = 0

        # Get all existing tenants and roles
        tenants = Tenant.objects.all()
        roles = Role.objects.all()
        
        if not tenants.exists():
            self.stdout.write(
                self.style.WARNING('No tenants found. Please create at least one tenant first.')
            )
            return

        if not roles.exists():
            self.stdout.write(
                self.style.WARNING('No roles found. Please create at least one role first.')
            )
            return

        for app in AVAILABLE_APPS:
            app_id = app['id']
            app_name = app['name']
            app_description = app.get('description', f'Access to {app_name} module')

            # Create entitlement record for each tenant
            for tenant in tenants:
                entitlement, created = AccessControl.objects.update_or_create(
                    key=app_id,
                    scope_type='tenant',
                    tenant=tenant,
                    access_type='entitlement',
                    defaults={
                        'name': f'{app_name} Entitlement',
                        'description': f'{app_description} - Feature Entitlement',
                        'is_enabled': True,
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created entitlement: {entitlement.name} for tenant {tenant.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated entitlement: {entitlement.name} for tenant {tenant.name}')
                    )

            # Create feature flag record for each tenant
            for tenant in tenants:
                feature_flag, created = AccessControl.objects.update_or_create(
                    key=app_id,
                    scope_type='tenant',
                    tenant=tenant,
                    access_type='feature_flag',
                    defaults={
                        'name': f'{app_name} Feature Flag',
                        'description': f'{app_description} - Feature Toggle',
                        'is_enabled': True,
                        'rollout_percentage': 100,
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created feature flag: {feature_flag.name} for tenant {tenant.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated feature flag: {feature_flag.name} for tenant {tenant.name}')
                    )

            # Create permission record for each role
            for role in roles:
                for tenant in tenants:
                    # Find a user with this role and tenant to associate with the role
                    # We need to check if there are users with this role in this tenant
                    permission, created = AccessControl.objects.update_or_create(
                        key=app_id,
                        scope_type='role',
                        role=role,
                        tenant=tenant,  # Also associate with tenant
                        access_type='permission',
                        defaults={
                            'name': f'{app_name} Permission',
                            'description': f'{app_description} - Role Permission for {role.name}',
                            'is_enabled': True,
                        }
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created permission: {permission.name} for role {role.name} in tenant {tenant.name}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated permission: {permission.name} for role {role.name} in tenant {tenant.name}')
                        )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Access control entries seeded: {created_count} created, {updated_count} updated'
            )
        )
