# File: /home/silaskimani/Documents/replit/git/salescompass/core/tenants/management/commands/setup_default_features.py
from django.core.management.base import BaseCommand
from core.models import User
from tenants.models import Tenant, TenantFeatureEntitlement

class Command(BaseCommand):
    help = 'Set up default feature entitlements for all tenants'

    def handle(self, *args, **options):
        # Define default features for all tenants
        default_features = [
            {
                'feature_key': 'basic_crm',
                'feature_name': 'Basic CRM',
                'is_enabled': True,
                'entitlement_type': 'always_enabled'
            },
            {
                'feature_key': 'leads_management',
                'feature_name': 'Leads Management',
                'is_enabled': True,
                'entitlement_type': 'always_enabled'
            },
            {
                'feature_key': 'opportunities_management',
                'feature_name': 'Opportunities Management',
                'is_enabled': True,
                'entitlement_type': 'always_enabled'
            },
            {
                'feature_key': 'accounts_management',
                'feature_name': 'Accounts Management',
                'is_enabled': True,
                'entitlement_type': 'always_enabled'
            },
            {
                'feature_key': 'reports_basic',
                'feature_name': 'Basic Reports',
                'is_enabled': True,
                'entitlement_type': 'always_enabled'
            },
            {
                'feature_key': 'data_export',
                'feature_name': 'Data Export',
                'is_enabled': True,
                'entitlement_type': 'plan_based'
            },
            {
                'feature_key': 'api_access',
                'feature_name': 'API Access',
                'is_enabled': False,
                'entitlement_type': 'premium'
            },
            {
                'feature_key': 'advanced_reporting',
                'feature_name': 'Advanced Reporting',
                'is_enabled': False,
                'entitlement_type': 'premium'
            },
        ]
        
        for tenant in Tenant.objects.all():
            for feature in default_features:
                # Create the feature entitlement if it doesn't exist
                _, created = TenantFeatureEntitlement.objects.get_or_create(
                    tenant=tenant,
                    feature_key=feature['feature_key'],
                    defaults={
                        'feature_name': feature['feature_name'],
                        'is_enabled': feature['is_enabled'],
                        'entitlement_type': feature['entitlement_type']
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created feature "{feature["feature_name"]}" for tenant "{tenant.name}"'
                        )
                    )
                else:
                    self.stdout.write(
                        f'Feature "{feature["feature_name"]}" already exists for tenant "{tenant.name}"'
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up default features for all tenants')
        )