from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from core.models import User
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Migrate existing records to use dynamic choice models instead of hardcoded choices'

    def handle(self, *args, **options):
        # Get all tenants to migrate choices for each
        tenants = Tenant.objects.all()
        
        if not tenants.exists():
            self.stdout.write(
                self.style.WARNING('No tenants found. Please create at least one tenant first.')
            )
            return

        # Define mapping of models and their fields to migrate
        migration_mappings = [
            # Leads app
            {
                'model_name': 'Lead',
                'app_label': 'leads',
                'mappings': [
                    {'old_field': 'industry', 'new_field': 'industry_ref', 'choice_model': 'Industry', 'lookup_field': 'industry_name'},
                    {'old_field': 'lead_source', 'new_field': 'source_ref', 'choice_model': 'LeadSource', 'lookup_field': 'source_name'},
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'LeadStatus', 'lookup_field': 'status_name'},
                ]
            },
            
            # Core app
            {
                'model_name': 'SystemConfiguration',
                'app_label': 'core',
                'mappings': [
                    {'old_field': 'data_type', 'new_field': 'data_type_ref', 'choice_model': 'SystemConfigType', 'lookup_field': 'name'},
                    {'old_field': 'category', 'new_field': 'category_ref', 'choice_model': 'SystemConfigCategory', 'lookup_field': 'name'},
                ]
            },
            
            # Billing app
            {
                'model_name': 'Plan',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'tier', 'new_field': 'tier_ref', 'choice_model': 'PlanTier', 'lookup_field': 'tier_name'},
                ]
            },
            {
                'model_name': 'Subscription',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'SubscriptionStatus', 'lookup_field': 'status_name'},
                ]
            },
            {
                'model_name': 'CreditAdjustment',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'adjustment_type', 'new_field': 'adjustment_type_ref', 'choice_model': 'AdjustmentType', 'lookup_field': 'type_name'},
                ]
            },
            {
                'model_name': 'PaymentProviderConfig',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'name', 'new_field': 'name_ref', 'choice_model': 'PaymentProvider', 'lookup_field': 'provider_name'},
                ]
            },
            {
                'model_name': 'PaymentMethod',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'type', 'new_field': 'type_ref', 'choice_model': 'PaymentType', 'lookup_field': 'type_name'},
                ]
            },
            
            # Dashboard app
            {
                'model_name': 'DashboardWidget',
                'app_label': 'dashboard',
                'mappings': [
                    {'old_field': 'widget_type_old', 'new_field': 'widget_type_ref', 'choice_model': 'WidgetType', 'lookup_field': 'widget_name'},
                    {'old_field': 'category_old', 'new_field': 'category_ref', 'choice_model': 'WidgetCategory', 'lookup_field': 'category_name'},
                ]
            },
            
            # Tasks app
            {
                'model_name': 'Task',
                'app_label': 'tasks',
                'mappings': [
                    {'old_field': 'priority', 'new_field': 'priority_ref', 'choice_model': 'TaskPriority', 'lookup_field': 'priority_name'},
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'TaskStatus', 'lookup_field': 'status_name'},
                    {'old_field': 'task_type', 'new_field': 'task_type_ref', 'choice_model': 'TaskType', 'lookup_field': 'type_name'},
                    {'old_field': 'recurrence_pattern', 'new_field': 'recurrence_pattern_ref', 'choice_model': 'RecurrencePattern', 'lookup_field': 'pattern_name'},
                ]
            },
            {
                'model_name': 'TaskTemplate',
                'app_label': 'tasks',
                'mappings': [
                    {'old_field': 'priority', 'new_field': 'priority_ref', 'choice_model': 'TaskPriority', 'lookup_field': 'priority_name'},
                    {'old_field': 'task_type', 'new_field': 'task_type_ref', 'choice_model': 'TaskType', 'lookup_field': 'type_name'},
                ]
            },
            
            # Marketing app
            {
                'model_name': 'Campaign',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'CampaignStatus', 'lookup_field': 'status_name'},
                ]
            },
            {
                'model_name': 'EmailTemplate',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'category', 'new_field': 'category_ref', 'choice_model': 'EmailCategory', 'lookup_field': 'category_name'},
                ]
            },
            {
                'model_name': 'LandingPageBlock',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'block_type', 'new_field': 'block_type_ref', 'choice_model': 'BlockType', 'lookup_field': 'type_name'},
                ]
            },
            {
                'model_name': 'MessageTemplate',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'message_type', 'new_field': 'message_type_ref', 'choice_model': 'MessageType', 'lookup_field': 'type_name'},
                    {'old_field': 'category', 'new_field': 'category_ref', 'choice_model': 'MessageCategory', 'lookup_field': 'category_name'},
                ]
            },
            {
                'model_name': 'EmailCampaign',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'email_provider', 'new_field': 'email_provider_ref', 'choice_model': 'EmailProvider', 'lookup_field': 'provider_name'},
                ]
            },
            
            # Opportunities app
            {
                'model_name': 'WinLossAnalysis',
                'app_label': 'opportunities',
                'mappings': [
                    {'old_field': 'deal_size_category', 'new_field': 'deal_size_category_ref', 'choice_model': 'DealSizeCategory', 'lookup_field': 'category_name'},
                ]
            },
            {
                'model_name': 'OpportunityStage',
                'app_label': 'opportunities',
                'mappings': [
                    {'old_field': 'pipeline_type', 'new_field': 'pipeline_type_ref', 'choice_model': 'PipelineType', 'lookup_field': 'pipeline_type_name'},
                ]
            },
            
            # Accounts app
            {
                'model_name': 'OrganizationMember',
                'app_label': 'accounts',
                'mappings': [
                    {'old_field': 'role', 'new_field': 'role_ref', 'choice_model': 'TeamRole', 'lookup_field': 'role_name'},
                    {'old_field': 'territory', 'new_field': 'territory_ref', 'choice_model': 'Territory', 'lookup_field': 'territory_name'},
                ]
            },
        ]

        # Process each tenant
        for tenant in tenants:
            self.stdout.write(f'Migrating records for tenant: {tenant.name}')
            
            for mapping in migration_mappings:
                try:
                    # Get the model class
                    model_class = apps.get_model(mapping['app_label'], mapping['model_name'])
                    
                    # Check if model has tenant field
                    has_tenant = any(f.name in ['tenant', 'tenant_id'] for f in model_class._meta.fields)
                    
                    # Get records
                    if has_tenant:
                        records = model_class.objects.filter(tenant_id=tenant.id)
                    else:
                        # Only process global models once (on the first tenant iteration or similar)
                        # Actually, to be simple, let's just process it for every tenant if it's small, 
                        # or only once if we track it. But since this script loops tenants, 
                        # global models will be processed multiple times. We should skip if already done.
                        if tenant != tenants.first():
                            continue
                        records = model_class.objects.all()
                    
                    for record in records:
                        # Process each field mapping
                        for field_mapping in mapping['mappings']:
                            old_field = field_mapping['old_field']
                            new_field = field_mapping['new_field']
                            choice_model_name = field_mapping['choice_model']
                            
                            # Get the old field value
                            old_value = getattr(record, old_field, None)
                            
                            if old_value:
                                # Get the corresponding dynamic choice model
                                choice_model = apps.get_model(mapping['app_label'], choice_model_name)
                                
                                # Check if choice model has tenant field
                                choice_has_tenant = any(f.name in ['tenant', 'tenant_id'] for f in choice_model._meta.fields)
                                
                                # Find the matching dynamic choice record
                                try:
                                    lookup_field = field_mapping.get('lookup_field', 'name')
                                    filter_kwargs = {lookup_field: old_value}
                                    
                                    if choice_has_tenant:
                                        filter_kwargs['tenant_id'] = tenant.id
                                        choice_record = choice_model.objects.get(**filter_kwargs)
                                    else:
                                        choice_record = choice_model.objects.get(**filter_kwargs)
                                    
                                    # Set the new field to reference the dynamic choice
                                    setattr(record, new_field, choice_record)
                                    
                                    self.stdout.write(
                                        f'  Migrated {mapping["model_name"]}.{old_field}={old_value} -> {new_field}'
                                    )
                                except choice_model.DoesNotExist:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'    Choice record not found: {choice_model_name} with {lookup_field}={old_value} for {"tenant=" + str(tenant.id) if choice_has_tenant else "global"}'
                                        )
                                    )
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.ERROR(
                                            f'    ERROR migrating {mapping["model_name"]}.{old_field}: {str(e)}\n'
                                            f'    Mapping: {field_mapping}\n'
                                            f'    Filter: {filter_kwargs}'
                                        )
                                    )
                                    raise e
                    
                    # Save all the updated records in a batch
                    for record in records:
                        record.save()
                
                except LookupError:
                    self.stdout.write(
                        self.style.WARNING(f'Model {mapping["model_name"]} not found in app {mapping["app_label"]}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully migrated records to use dynamic choice models')
        )
