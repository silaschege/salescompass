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
                    {'old_field': 'industry', 'new_field': 'industry_ref', 'choice_model': 'Industry'},
                    {'old_field': 'lead_source', 'new_field': 'source_ref', 'choice_model': 'LeadSource'},
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'LeadStatus'},
                ]
            },
            
            # Core app
            {
                'model_name': 'SystemConfiguration',
                'app_label': 'core',
                'mappings': [
                    {'old_field': 'data_type', 'new_field': 'data_type_ref', 'choice_model': 'SystemConfigType'},
                    {'old_field': 'category', 'new_field': 'category_ref', 'choice_model': 'SystemConfigCategory'},
                ]
            },
            {
                'model_name': 'SystemEventLog',
                'app_label': 'core',
                'mappings': [
                    {'old_field': 'event_type', 'new_field': 'event_type_ref', 'choice_model': 'SystemEventType'},
                    {'old_field': 'severity', 'new_field': 'severity_ref', 'choice_model': 'SystemEventSeverity'},
                ]
            },
            {
                'model_name': 'SystemHealthCheck',
                'app_label': 'core',
                'mappings': [
                    {'old_field': 'check_type', 'new_field': 'check_type_ref', 'choice_model': 'HealthCheckType'},
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'HealthCheckStatus'},
                ]
            },
            {
                'model_name': 'MaintenanceWindow',
                'app_label': 'core',
                'mappings': [
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'MaintenanceStatus'},
                    {'old_field': 'maintenance_type', 'new_field': 'maintenance_type_ref', 'choice_model': 'MaintenanceType'},
                ]
            },
            {
                'model_name': 'PerformanceMetric',
                'app_label': 'core',
                'mappings': [
                    {'old_field': 'metric_type', 'new_field': 'metric_type_ref', 'choice_model': 'PerformanceMetricType'},
                    {'old_field': 'environment', 'new_field': 'environment_ref', 'choice_model': 'PerformanceEnvironment'},
                ]
            },
            {
                'model_name': 'SystemNotification',
                'app_label': 'core',
                'mappings': [
                    {'old_field': 'notification_type', 'new_field': 'notification_type_ref', 'choice_model': 'NotificationType'},
                    {'old_field': 'priority', 'new_field': 'priority_ref', 'choice_model': 'NotificationPriority'},
                ]
            },
            
            # Billing app
            {
                'model_name': 'Plan',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'tier', 'new_field': 'tier_ref', 'choice_model': 'PlanTier'},
                ]
            },
            {
                'model_name': 'Subscription',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'SubscriptionStatus'},
                ]
            },
            {
                'model_name': 'CreditAdjustment',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'adjustment_type', 'new_field': 'adjustment_type_ref', 'choice_model': 'AdjustmentType'},
                ]
            },
            {
                'model_name': 'PaymentProviderConfig',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'name', 'new_field': 'name_ref', 'choice_model': 'PaymentProvider'},
                ]
            },
            {
                'model_name': 'PaymentMethod',
                'app_label': 'billing',
                'mappings': [
                    {'old_field': 'type', 'new_field': 'type_ref', 'choice_model': 'PaymentType'},
                ]
            },
            
            # Dashboard app
            {
                'model_name': 'DashboardWidget',
                'app_label': 'dashboard',
                'mappings': [
                    {'old_field': 'widget_type', 'new_field': 'widget_type_ref', 'choice_model': 'WidgetType'},
                    {'old_field': 'category', 'new_field': 'category_ref', 'choice_model': 'WidgetCategory'},
                ]
            },
            
            # Tasks app
            {
                'model_name': 'Task',
                'app_label': 'tasks',
                'mappings': [
                    {'old_field': 'priority', 'new_field': 'priority_ref', 'choice_model': 'TaskPriority'},
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'TaskStatus'},
                    {'old_field': 'task_type', 'new_field': 'task_type_ref', 'choice_model': 'TaskType'},
                    {'old_field': 'recurrence_pattern', 'new_field': 'recurrence_pattern_ref', 'choice_model': 'RecurrencePattern'},
                ]
            },
            {
                'model_name': 'TaskTemplate',
                'app_label': 'tasks',
                'mappings': [
                    {'old_field': 'priority', 'new_field': 'priority_ref', 'choice_model': 'TaskPriority'},
                    {'old_field': 'task_type', 'new_field': 'task_type_ref', 'choice_model': 'TaskType'},
                ]
            },
            
            # Settings app
            {
                'model_name': 'Setting',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'setting_type', 'new_field': 'setting_type_ref', 'choice_model': 'SettingType'},
                ]
            },
            {
                'model_name': 'CustomField',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'model_name', 'new_field': 'model_name_ref', 'choice_model': 'ModelChoice'},
                    {'old_field': 'field_type', 'new_field': 'field_type_ref', 'choice_model': 'FieldType'},
                ]
            },
            {
                'model_name': 'ModuleLabel',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'module_key', 'new_field': 'module_key_ref', 'choice_model': 'ModuleChoice'},
                ]
            },
            {
                'model_name': 'TeamMember',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'role', 'new_field': 'role_ref', 'choice_model': 'TeamRole'},
                    {'old_field': 'territory', 'new_field': 'territory_ref', 'choice_model': 'Territory'},
                ]
            },
            {
                'model_name': 'AssignmentRule',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'module', 'new_field': 'module_ref', 'choice_model': 'ModuleChoice'},
                    {'old_field': 'rule_type', 'new_field': 'rule_type_ref', 'choice_model': 'AssignmentRuleType'},
                ]
            },
            {
                'model_name': 'PipelineStage',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'pipeline_type', 'new_field': 'pipeline_type_ref', 'choice_model': 'PipelineType'},
                ]
            },
            {
                'model_name': 'EmailIntegration',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'provider', 'new_field': 'provider_ref', 'choice_model': 'EmailProvider'},
                ]
            },
            {
                'model_name': 'BehavioralScoringRule',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'action_type', 'new_field': 'action_type_ref', 'choice_model': 'ActionType'},
                ]
            },
            {
                'model_name': 'DemographicScoringRule',
                'app_label': 'settings_app',
                'mappings': [
                    {'old_field': 'operator', 'new_field': 'operator_ref', 'choice_model': 'OperatorType'},
                ]
            },
            
            # Reports app
            {
                'model_name': 'Report',
                'app_label': 'reports',
                'mappings': [
                    {'old_field': 'report_type', 'new_field': 'report_type_ref', 'choice_model': 'ReportType'},
                    {'old_field': 'schedule_frequency', 'new_field': 'schedule_frequency_ref', 'choice_model': 'ReportScheduleFrequency'},
                ]
            },
            {
                'model_name': 'ReportSchedule',
                'app_label': 'reports',
                'mappings': [
                    {'old_field': 'frequency', 'new_field': 'frequency_ref', 'choice_model': 'ReportScheduleFrequency'},
                ]
            },
            {
                'model_name': 'ReportExport',
                'app_label': 'reports',
                'mappings': [
                    {'old_field': 'export_format', 'new_field': 'export_format_ref', 'choice_model': 'ExportFormat'},
                ]
            },
            {
                'model_name': 'ReportTemplate',
                'app_label': 'reports',
                'mappings': [
                    {'old_field': 'template_type', 'new_field': 'template_type_ref', 'choice_model': 'TemplateType'},
                    {'old_field': 'template_format', 'new_field': 'template_format_ref', 'choice_model': 'TemplateFormat'},
                ]
            },
            {
                'model_name': 'ReportAnalytics',
                'app_label': 'reports',
                'mappings': [
                    {'old_field': 'action', 'new_field': 'action_ref', 'choice_model': 'ReportAction'},
                ]
            },
            {
                'model_name': 'ReportSubscriber',
                'app_label': 'reports',
                'mappings': [
                    {'old_field': 'subscription_type', 'new_field': 'subscription_type_ref', 'choice_model': 'SubscriptionType'},
                    {'old_field': 'report_format', 'new_field': 'report_format_ref', 'choice_model': 'ReportFormat'},
                ]
            },
            {
                'model_name': 'ReportNotification',
                'app_label': 'reports',
                'mappings': [
                    {'old_field': 'notification_channel', 'new_field': 'notification_channel_ref', 'choice_model': 'NotificationChannel'},
                ]
            },
            
            # Marketing app
            {
                'model_name': 'Campaign',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'status', 'new_field': 'status_ref', 'choice_model': 'CampaignStatus'},
                ]
            },
            {
                'model_name': 'EmailTemplate',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'category', 'new_field': 'category_ref', 'choice_model': 'EmailCategory'},
                ]
            },
            {
                'model_name': 'LandingPageBlock',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'block_type', 'new_field': 'block_type_ref', 'choice_model': 'BlockType'},
                ]
            },
            {
                'model_name': 'MessageTemplate',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'message_type', 'new_field': 'message_type_ref', 'choice_model': 'MessageType'},
                    {'old_field': 'category', 'new_field': 'category_ref', 'choice_model': 'MessageCategory'},
                ]
            },
            {
                'model_name': 'EmailCampaign',
                'app_label': 'marketing',
                'mappings': [
                    {'old_field': 'email_provider', 'new_field': 'email_provider_ref', 'choice_model': 'EmailProvider'},
                ]
            },
            
            # Opportunities app
            {
                'model_name': 'WinLossAnalysis',
                'app_label': 'opportunities',
                'mappings': [
                    {'old_field': 'deal_size_category', 'new_field': 'deal_size_category_ref', 'choice_model': 'DealSizeCategory'},
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
                    
                    # Get all records for this tenant
                    records = model_class.objects.filter(tenant_id=tenant.id)
                    
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
                                
                                # Find the matching dynamic choice record
                                try:
                                    choice_record = choice_model.objects.get(
                                        name=old_value,
                                        tenant_id=tenant.id
                                    )
                                    
                                    # Set the new field to reference the dynamic choice
                                    setattr(record, new_field, choice_record)
                                    
                                    self.stdout.write(
                                        f'  Migrated {mapping["model_name"]}.{old_field}={old_value} -> {new_field}'
                                    )
                                except choice_model.DoesNotExist:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'    Choice record not found: {choice_model_name} with name={old_value} for tenant={tenant.id}'
                                        )
                                    )
                    
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
