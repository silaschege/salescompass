from django.core.management.base import BaseCommand
from access_control.models import AccessControl

class Command(BaseCommand):
    help = 'Register billing module access control definitions'

    def handle(self, *args, **options):
        permissions = [
            {
                'key': 'billing.dashboard',
                'name': 'Billing Dashboard',
                'description': 'Access to the main billing dashboard',
                'access_type': 'permission'
            },
            {
                'key': 'billing.plans',
                'name': 'Plan Management',
                'description': 'View and manage subscription plans',
                'access_type': 'permission'
            },
            {
                'key': 'billing.subscriptions',
                'name': 'Subscription Management',
                'description': 'View and manage tenant subscriptions',
                'access_type': 'permission'
            },
            {
                'key': 'billing.invoices',
                'name': 'Invoice Management',
                'description': 'View and manage invoices',
                'access_type': 'permission'
            },
            {
                'key': 'billing.payments',
                'name': 'Payment Management',
                'description': 'View and manage payments',
                'access_type': 'permission'
            },
            {
                'key': 'billing.reports.view',
                'name': 'Billing Reports',
                'description': 'View billing and revenue reports',
                'access_type': 'permission'
            },
            {
                'key': 'billing.admin.revenue',
                'name': 'Revenue Admin',
                'description': 'Admin access to revenue analytics',
                'access_type': 'permission'
            },
            {
                'key': 'billing.admin.config',
                'name': 'Billing Configuration',
                'description': 'Access to billing system configuration',
                'access_type': 'permission'
            },
            {
                'key': 'billing.admin.adjustments',
                'name': 'Credit Adjustments',
                'description': 'Manage credit and debit adjustments',
                'access_type': 'permission'
            },
        ]

        for perm_data in permissions:
            ac, created = AccessControl.objects.update_or_create(
                key=perm_data['key'],
                defaults={
                    'name': perm_data['name'],
                    'description': perm_data['description'],
                    'access_type': perm_data['access_type'],
                    'default_enabled': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created permission: {ac.key}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated permission: {ac.key}"))

        self.stdout.write(self.style.SUCCESS("Billing permissions registered successfully"))
