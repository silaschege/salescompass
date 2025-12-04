"""
Seed initial feature flags for SalesCompass Control Plane.

Usage:
    python manage.py seed_feature_flags
"""
from django.core.management.base import BaseCommand
from feature_flags.models import FeatureFlag


class Command(BaseCommand):
    help = 'Seed initial feature flags for core modules'

    def handle(self, *args, **options):
        flags = [
            {
                'key': 'beta_features',
                'name': 'Beta Features',
                'description': 'Enable access to beta features for testing',
                'is_active': False,
                'rollout_percentage': 0,
            },
            {
                'key': 'api_v2',
                'name': 'API v2',
                'description': 'Enable API version 2 endpoints',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'new_reports',
                'name': 'New Reports Engine',
                'description': 'Enable the new advanced reporting engine',
                'is_active': False,
                'rollout_percentage': 0,
            },
            {
                'key': 'leads_module',
                'name': 'Leads Module',
                'description': 'Enable the Leads management module',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'opportunities_module',
                'name': 'Opportunities Module',
                'description': 'Enable the Opportunities/Pipeline module',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'cases_module',
                'name': 'Cases Module',
                'description': 'Enable the Customer Support Cases module',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'nps_module',
                'name': 'NPS Surveys Module',
                'description': 'Enable the Net Promoter Score surveys module',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'marketing_module',
                'name': 'Marketing Module',
                'description': 'Enable the Marketing campaigns and email templates module',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'automation_module',
                'name': 'Automation Module',
                'description': 'Enable workflow automation features',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'engagement_module',
                'name': 'Engagement Module',
                'description': 'Enable customer engagement tracking and Next Best Actions',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'commissions_module',
                'name': 'Commissions Module',
                'description': 'Enable sales commissions tracking',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'audit_logging',
                'name': 'Audit Logging',
                'description': 'Enable detailed audit logging for compliance',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'advanced_analytics',
                'name': 'Advanced Analytics',
                'description': 'Enable advanced analytics and AI-powered insights',
                'is_active': False,
                'rollout_percentage': 0,
            },
            {
                'key': 'multi_currency',
                'name': 'Multi-Currency Support',
                'description': 'Enable multi-currency for international deals',
                'is_active': False,
                'rollout_percentage': 0,
            },
            {
                'key': 'custom_fields',
                'name': 'Custom Fields',
                'description': 'Enable custom fields on all entities',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'api_rate_limiting',
                'name': 'API Rate Limiting',
                'description': 'Enable API rate limiting per tenant',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'webhooks',
                'name': 'Webhooks',
                'description': 'Enable webhook integrations',
                'is_active': True,
                'rollout_percentage': 100,
            },
            {
                'key': 'email_integration',
                'name': 'Email Integration',
                'description': 'Enable email sending capabilities',
                'is_active': False,
                'rollout_percentage': 0,
            },
            {
                'key': 'telephony_integration',
                'name': 'Telephony Integration',
                'description': 'Enable Wazo telephony integration for calls',
                'is_active': False,
                'rollout_percentage': 0,
            },
            {
                'key': 'stripe_billing',
                'name': 'Stripe Billing Integration',
                'description': 'Enable Stripe payment processing',
                'is_active': False,
                'rollout_percentage': 0,
            },
        ]

        created_count = 0
        updated_count = 0

        for flag_data in flags:
            flag, created = FeatureFlag.objects.update_or_create(
                key=flag_data['key'],
                defaults={
                    'name': flag_data['name'],
                    'description': flag_data['description'],
                    'is_active': flag_data['is_active'],
                    'rollout_percentage': flag_data['rollout_percentage'],
                    'created_by': 'system',
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {flag.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {flag.name}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Feature flags seeded: {created_count} created, {updated_count} updated'))
        self.stdout.write(self.style.SUCCESS(f'Total active flags: {FeatureFlag.objects.filter(is_active=True).count()}'))
