# NEW FILE: /home/silaskimani/Documents/replit/git/salescompass/core/access_control/management/commands/migrate_access_controls.py
from django.core.management.base import BaseCommand
from core.access_control.models import AccessControl
from core.access_control.role_models import Role
from core.models import User
from tenants.models import Tenant

class Command(BaseCommand):
    help = 'Migrate existing access controls to unified system'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually doing it')
        parser.add_argument('--app-name', type=str, help='Only migrate for specific app')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        app_name = options.get('app_name')
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting access control migration{" (dry run)" if dry_run else ""}')
        )
        
        # Example migration for a sample app - expand as needed
        self.migrate_billing_access_controls(dry_run, app_name)
        self.migrate_leads_access_controls(dry_run, app_name)
        self.migrate_other_app_access_controls(dry_run, app_name)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully completed access control migration')
        )

    def migrate_billing_access_controls(self, dry_run, app_name):
        """Migrate billing app access controls"""
        if app_name and app_name != 'billing':
            return
            
        billing_resources = [
            {'key': 'billing.dashboard', 'name': 'Billing Dashboard Access', 'type': 'permission'},
            {'key': 'billing.plans', 'name': 'Manage Billing Plans', 'type': 'permission'},
            {'key': 'billing.subscriptions', 'name': 'Manage Subscriptions', 'type': 'permission'},
            {'key': 'billing.payments', 'name': 'Manage Payments', 'type': 'permission'},
        ]
        
        for resource in billing_resources:
            if not dry_run:
                # Create default access controls for all tenants
                for tenant in Tenant.objects.all():
                    AccessControl.objects.get_or_create(
                        key=resource['key'],
                        name=resource['name'],
                        access_type=resource['type'],
                        scope_type='tenant',
                        tenant=tenant,
                        defaults={'is_enabled': True}
                    )
            
            self.stdout.write(f"  Migrated: {resource['key']}")

    def migrate_leads_access_controls(self, dry_run, app_name):
        """Migrate leads app access controls"""
        if app_name and app_name != 'leads':
            return
            
        leads_resources = [
            {'key': 'leads.view', 'name': 'View Leads', 'type': 'permission'},
            {'key': 'leads.create', 'name': 'Create Leads', 'type': 'permission'},
            {'key': 'leads.edit', 'name': 'Edit Leads', 'type': 'permission'},
            {'key': 'leads.delete', 'name': 'Delete Leads', 'type': 'permission'},
        ]
        
        for resource in leads_resources:
            if not dry_run:
                # Create default access controls for all tenants
                for tenant in Tenant.objects.all():
                    AccessControl.objects.get_or_create(
                        key=resource['key'],
                        name=resource['name'],
                        access_type=resource['type'],
                        scope_type='tenant',
                        tenant=tenant,
                        defaults={'is_enabled': True}
                    )
            
            self.stdout.write(f"  Migrated: {resource['key']}")

    def migrate_other_app_access_controls(self, dry_run, app_name):
        """Migrate other app access controls"""
        # Add more app-specific migrations here
        pass