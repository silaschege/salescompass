from django.core.management.base import BaseCommand
from billing.models import Plan
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds default subscription plans with module and feature configurations'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Starter',
                'price': 0.00,
                'max_users': 1,
                'config': {
                    'leads': {
                        'enabled': True,
                        'display_name': 'Leads',
                        'features': {
                            'lead_management': True,
                            'lead_scoring': False,
                            'lead_analytics': False
                        }
                    },
                    'engagement': {
                        'enabled': True,
                        'display_name': 'Engagement',
                        'features': {
                            'email_tracking': True,
                            'activity_log': True
                        }
                    },
                    'sales': {'enabled': False, 'features': {}},
                    'proposals': {'enabled': False, 'features': {}}
                }
            },
            {
                'name': 'Basic',
                'price': 49.00,
                'max_users': 5,
                'config': {
                    'leads': {
                        'enabled': True,
                        'display_name': 'Leads',
                        'features': {
                            'lead_management': True,
                            'lead_scoring': True,
                            'lead_analytics': False
                        }
                    },
                    'sales': {
                        'enabled': True,
                        'display_name': 'Sales',
                        'features': {
                            'opportunity_management': True,
                            'sales_reports': False
                        }
                    },
                    'proposals': {
                        'enabled': True,
                        'display_name': 'Proposals',
                        'features': {
                            'proposal_creation': True,
                            'basic_templates': True
                        }
                    },
                    'engagement': {'enabled': True, 'features': {'email_tracking': True}}
                }
            },
            {
                'name': 'Professional',
                'price': 149.00,
                'max_users': 15,
                'config': {
                    'leads': {
                        'enabled': True,
                        'display_name': 'Leads All-Access',
                        'features': {
                            'lead_management': True,
                            'lead_scoring': True,
                            'lead_analytics': True
                        }
                    },
                    'sales': {
                        'enabled': True,
                        'display_name': 'Sales Pro',
                        'features': {
                            'opportunity_management': True,
                            'sales_reports': True,
                            'forecasting': True
                        }
                    },
                    'proposals': {
                        'enabled': True,
                        'display_name': 'Proposals Pro',
                        'features': {
                            'proposal_creation': True,
                            'advanced_templates': True,
                            'e_signatures': True
                        }
                    },
                    'engagement': {'enabled': True, 'features': {'email_tracking': True, 'automation': True}}
                }
            }
        ]

        for plan_data in plans:
            plan, created = Plan.objects.update_or_create(
                name=plan_data['name'],
                defaults={
                    'price': plan_data['price'],
                    'max_users': plan_data['max_users'],
                    'features_config': plan_data['config'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated plan: {plan.name}"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded default plans"))
