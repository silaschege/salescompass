from django.core.management.base import BaseCommand
from billing.models import Plan, PlanFeatureAccess, PlanModuleAccess

class Command(BaseCommand):
    help = 'Initialize default plan features and modules'

    def handle(self, *args, **options):
        # Create or get default plans
        basic_plan, created = Plan.objects.get_or_create(
            name='Basic',
            defaults={
                'description': 'Basic plan with essential features',
                'price': 29.00,
                'is_active': True
            }
        )
        
        starter_plan, created = Plan.objects.get_or_create(
            name='Starter',
            defaults={
                'description': 'Starter plan with core modules',
                'price': 49.00,
                'is_active': True
            }
        )
        
        premium_plan, created = Plan.objects.get_or_create(
            name='Premium',
            defaults={
                'description': 'Premium plan with all features',
                'price': 99.00,
                'is_active': True
            }
        )
        
        # Define features for Basic Plan
        basic_plan_features = [
            # Leads features (all except analytics)
            {'feature_key': 'leads_basic', 'feature_name': 'Basic Leads Management', 'feature_category': 'leads', 'is_available': True},
            {'feature_key': 'leads_create', 'feature_name': 'Create Leads', 'feature_category': 'leads', 'is_available': True},
            {'feature_key': 'leads_edit', 'feature_name': 'Edit Leads', 'feature_category': 'leads', 'is_available': True},
            {'feature_key': 'leads_delete', 'feature_name': 'Delete Leads', 'feature_category': 'leads', 'is_available': True},
            {'feature_key': 'leads_import', 'feature_name': 'Import Leads', 'feature_category': 'leads', 'is_available': True},
            {'feature_key': 'leads_export', 'feature_name': 'Export Leads', 'feature_category': 'leads', 'is_available': True},
            {'feature_key': 'leads_assign', 'feature_name': 'Assign Leads', 'feature_category': 'leads', 'is_available': True},
            # Exclude: leads_analytics
            
            # Sales features (all except reports)
            {'feature_key': 'sales_basic', 'feature_name': 'Basic Sales Management', 'feature_category': 'sales', 'is_available': True},
            {'feature_key': 'sales_create', 'feature_name': 'Create Opportunities', 'feature_category': 'sales', 'is_available': True},
            {'feature_key': 'sales_edit', 'feature_name': 'Edit Opportunities', 'feature_category': 'sales', 'is_available': True},
            {'feature_key': 'sales_delete', 'feature_name': 'Delete Opportunities', 'feature_category': 'sales', 'is_available': True},
            # Exclude: sales_reports
            
            # Engagement features
            {'feature_key': 'engagement_basic', 'feature_name': 'Basic Engagement', 'feature_category': 'engagement', 'is_available': True},
            {'feature_key': 'engagement_email', 'feature_name': 'Email Engagement', 'feature_category': 'engagement', 'is_available': True},
            {'feature_key': 'engagement_sms', 'feature_name': 'SMS Engagement', 'feature_category': 'engagement', 'is_available': True},
            
            # Proposals features
            {'feature_key': 'proposals_basic', 'feature_name': 'Basic Proposals', 'feature_category': 'proposals', 'is_available': True},
            {'feature_key': 'proposals_create', 'feature_name': 'Create Proposals', 'feature_category': 'proposals', 'is_available': True},
            {'feature_key': 'proposals_edit', 'feature_name': 'Edit Proposals', 'feature_category': 'proposals', 'is_available': True},
            
            # Billing features
            {'feature_key': 'billing_basic', 'feature_name': 'Basic Billing', 'feature_category': 'billing', 'is_available': True},
        ]
        
        # Define features for Starter Plan
        starter_plan_features = [
            # All Basic features
            *basic_plan_features,
            
            # Leads analytics (not in Basic)
            {'feature_key': 'leads_analytics', 'feature_name': 'Leads Analytics', 'feature_category': 'leads', 'is_available': True},
            
            # Sales reports (not in Basic)
            {'feature_key': 'sales_reports', 'feature_name': 'Sales Reports', 'feature_category': 'sales', 'is_available': True},
            
            # Products features
            {'feature_key': 'products_basic', 'feature_name': 'Basic Products', 'feature_category': 'products', 'is_available': True},
            {'feature_key': 'products_create', 'feature_name': 'Create Products', 'feature_category': 'products', 'is_available': True},
            {'feature_key': 'products_edit', 'feature_name': 'Edit Products', 'feature_category': 'products', 'is_available': True},
        ]
        
        # Define features for Premium Plan
        premium_plan_features = [
            # All Starter features
            *starter_plan_features,
            
            # Advanced features
            {'feature_key': 'advanced_analytics', 'feature_name': 'Advanced Analytics', 'feature_category': 'analytics', 'is_available': True},
            {'feature_key': 'ai_predictions', 'feature_name': 'AI Predictions', 'feature_category': 'ai', 'is_available': True},
            {'feature_key': 'custom_reports', 'feature_name': 'Custom Reports', 'feature_category': 'reports', 'is_available': True},
            {'feature_key': 'api_access', 'feature_name': 'Full API Access', 'feature_category': 'api', 'is_available': True},
            {'feature_key': 'white_label', 'feature_name': 'White Label', 'feature_category': 'branding', 'is_available': True},
        ]
        
        # Create features for each plan
        for feature_data in basic_plan_features:
            PlanFeatureAccess.objects.get_or_create(
                plan=basic_plan,
                feature_key=feature_data['feature_key'],
                defaults=feature_data
            )
        
        for feature_data in starter_plan_features:
            PlanFeatureAccess.objects.get_or_create(
                plan=starter_plan,
                feature_key=feature_data['feature_key'],
                defaults=feature_data
            )
        
        for feature_data in premium_plan_features:
            PlanFeatureAccess.objects.get_or_create(
                plan=premium_plan,
                feature_key=feature_data['feature_key'],
                defaults=feature_data
            )
        
        # Define modules for Basic Plan
        basic_plan_modules = [
            {'module_name': 'leads', 'module_display_name': 'Leads', 'is_available': True},
            {'module_name': 'sales', 'module_display_name': 'Sales', 'is_available': True},
            {'module_name': 'engagement', 'module_display_name': 'Engagement', 'is_available': True},
            {'module_name': 'proposals', 'module_display_name': 'Proposals', 'is_available': True},
            {'module_name': 'billing', 'module_display_name': 'Billing', 'is_available': True},
        ]
        
        # Define modules for Starter Plan
        starter_plan_modules = [
            {'module_name': 'leads', 'module_display_name': 'Leads', 'is_available': True},
            {'module_name': 'sales', 'module_display_name': 'Sales', 'is_available': True},
            {'module_name': 'engagement', 'module_display_name': 'Engagement', 'is_available': True},
            {'module_name': 'proposals', 'module_display_name': 'Proposals', 'is_available': True},
            {'module_name': 'products', 'module_display_name': 'Products', 'is_available': True},
            {'module_name': 'billing', 'module_display_name': 'Billing', 'is_available': True},
        ]
        
        # Define modules for Premium Plan
        premium_plan_modules = [
            {'module_name': 'leads', 'module_display_name': 'Leads', 'is_available': True},
            {'module_name': 'sales', 'module_display_name': 'Sales', 'is_available': True},
            {'module_name': 'engagement', 'module_display_name': 'Engagement', 'is_available': True},
            {'module_name': 'proposals', 'module_display_name': 'Proposals', 'is_available': True},
            {'module_name': 'products', 'module_display_name': 'Products', 'is_available': True},
            {'module_name': 'reports', 'module_display_name': 'Reports', 'is_available': True},
            {'module_name': 'analytics', 'module_display_name': 'Analytics', 'is_available': True},
            {'module_name': 'settings', 'module_display_name': 'Settings', 'is_available': True},
            {'module_name': 'billing', 'module_display_name': 'Billing', 'is_available': True},
        ]
        
        # Create modules for each plan
        for module_data in basic_plan_modules:
            PlanModuleAccess.objects.get_or_create(
                plan=basic_plan,
                module_name=module_data['module_name'],
                defaults=module_data
            )
        
        for module_data in starter_plan_modules:
            PlanModuleAccess.objects.get_or_create(
                plan=starter_plan,
                module_name=module_data['module_name'],
                defaults=module_data
            )
        
        for module_data in premium_plan_modules:
            PlanModuleAccess.objects.get_or_create(
                plan=premium_plan,
                module_name=module_data['module_name'],
                defaults=module_data
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized plan features and modules for {basic_plan.name}, {starter_plan.name}, and {premium_plan.name}'
            )
        )