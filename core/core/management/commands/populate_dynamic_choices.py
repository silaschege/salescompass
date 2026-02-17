from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from core.models import User
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Populate dynamic choice models with initial data from hardcoded choices'

    def handle(self, *args, **options):
        # Get all tenants to populate choices for each
        tenants = Tenant.objects.all()
        
        if not tenants.exists():
            self.stdout.write(
                self.style.WARNING('No tenants found. Please create at least one tenant first.')
            )
            return

        # Define mapping of choice models to their hardcoded choices
        choice_mappings = [
            # Leads app
            {
                'model_name': 'Industry',
                'app_label': 'leads',
                'choices': [
                    ('tech', 'Technology'),
                    ('manufacturing', 'Manufacturing'),
                    ('finance', 'Finance'),
                    ('healthcare', 'Healthcare'),
                    ('retail', 'Retail'),
                    ('energy', 'Energy'),
                    ('education', 'Education'),
                    ('other', 'Other'),
                ]
            },
            {
                'model_name': 'LeadSource',
                'app_label': 'leads',
                'choices': [
                    ('web', 'Web Form'),
                    ('event', 'Event'),
                    ('referral', 'Referral'),
                    ('ads', 'Paid Ads'),
                    ('manual', 'Manual Entry'),
                ]
            },
            {
                'model_name': 'LeadStatus',
                'app_label': 'leads',
                'choices': [
                    ('new', 'New'),
                    ('contacted', 'Contacted'),
                    ('qualified', 'Qualified'),
                    ('unqualified', 'Unqualified'),
                    ('converted', 'Converted'),
                ]
            },
            
            # Core app
            {
                'model_name': 'SystemConfigType',
                'app_label': 'core',
                'choices': [
                    ('string', 'String'),
                    ('integer', 'Integer'),
                    ('boolean', 'Boolean'),
                    ('json', 'JSON'),
                    ('file', 'File Path'),
                ]
            },
            {
                'model_name': 'SystemConfigCategory',
                'app_label': 'core',
                'choices': [
                    ('general', 'General'),
                    ('security', 'Security'),
                    ('email', 'Email'),
                    ('authentication', 'Authentication'),
                    ('integration', 'Integration'),
                    ('performance', 'Performance'),
                ]
            },
            {
                'model_name': 'SystemEventType',
                'app_label': 'core',
                'choices': [
                    ('system_start', 'System Start'),
                    ('system_stop', 'System Stop'),
                    ('maintenance', 'Maintenance'),
                    ('backup', 'Backup'),
                    ('restore', 'Restore'),
                    ('configuration_change', 'Configuration Change'),
                    ('security_scan', 'Security Scan'),
                    ('patch_install', 'Patch Install'),
                    ('monitoring_alert', 'Monitoring Alert'),
                ]
            },
            {
                'model_name': 'SystemEventSeverity',
                'app_label': 'core',
                'choices': [
                    ('info', 'Information'),
                    ('warning', 'Warning'),
                    ('error', 'Error'),
                    ('critical', 'Critical'),
                ]
            },
            {
                'model_name': 'HealthCheckType',
                'app_label': 'core',
                'choices': [
                    ('database', 'Database Connection'),
                    ('cache', 'Cache Health'),
                    ('storage', 'Storage Space'),
                    ('network', 'Network Connectivity'),
                    ('api', 'API Response Time'),
                    ('memory', 'Memory Usage'),
                    ('cpu', 'CPU Usage'),
                    ('disk_io', 'Disk I/O'),
                    ('process', 'Process Health'),
                ]
            },
            {
                'model_name': 'HealthCheckStatus',
                'app_label': 'core',
                'choices': [
                    ('healthy', 'Healthy'),
                    ('warning', 'Warning'),
                    ('error', 'Error'),
                    ('critical', 'Critical'),
                ]
            },
            {
                'model_name': 'MaintenanceStatus',
                'app_label': 'core',
                'choices': [
                    ('scheduled', 'Scheduled'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                ]
            },
            {
                'model_name': 'MaintenanceType',
                'app_label': 'core',
                'choices': [
                    ('system_update', 'System Update'),
                    ('database_maintenance', 'Database Maintenance'),
                    ('security_patch', 'Security Patch'),
                    ('backup_restore', 'Backup/Restore'),
                    ('infrastructure_upgrade', 'Infrastructure Upgrade'),
                ]
            },
            {
                'model_name': 'PerformanceMetricType',
                'app_label': 'core',
                'choices': [
                    ('response_time', 'API Response Time'),
                    ('throughput', 'Request Throughput'),
                    ('concurrency', 'Concurrent Users'),
                    ('memory_usage', 'Memory Usage'),
                    ('cpu_usage', 'CPU Usage'),
                    ('database_queries', 'Database Query Time'),
                    ('cache_hit_ratio', 'Cache Hit Ratio'),
                    ('disk_io', 'Disk I/O'),
                ]
            },
            {
                'model_name': 'PerformanceEnvironment',
                'app_label': 'core',
                'choices': [
                    ('development', 'Development'),
                    ('staging', 'Staging'),
                    ('production', 'Production'),
                ]
            },
            {
                'model_name': 'NotificationType',
                'app_label': 'core',
                'choices': [
                    ('info', 'Information'),
                    ('warning', 'Warning'),
                    ('alert', 'Alert'),
                    ('maintenance', 'Maintenance Notice'),
                    ('system_update', 'System Update'),
                ]
            },
            {
                'model_name': 'NotificationPriority',
                'app_label': 'core',
                'choices': [
                    ('low', 'Low'),
                    ('normal', 'Normal'),
                    ('high', 'High'),
                    ('urgent', 'Urgent'),
                ]
            },
            
            # Billing app
            {
                'model_name': 'PlanTier',
                'app_label': 'billing',
                'choices': [
                    ('starter', 'Starter'),
                    ('pro', 'Pro'),
                    ('enterprise', 'Enterprise'),
                ]
            },
            {
                'model_name': 'SubscriptionStatus',
                'app_label': 'billing',
                'choices': [
                    ('active', 'Active'),
                    ('past_due', 'Past Due'),
                    ('canceled', 'Canceled'),
                    ('incomplete', 'Incomplete'),
                    ('trialing', 'Trialing'),
                ]
            },
            {
                'model_name': 'AdjustmentType',
                'app_label': 'billing',
                'choices': [
                    ('credit', 'Credit'),
                    ('refund', 'Refund'),
                    ('discount', 'Discount'),
                ]
            },
            {
                'model_name': 'PaymentProvider',
                'app_label': 'billing',
                'choices': [
                    ('stripe', 'Stripe'),
                    ('mpesa', 'M-Pesa'),
                    ('paypal', 'PayPal'),
                    ('flutterwave', 'Flutterwave'),
                    ('paystack', 'Paystack'),
                ]
            },
            {
                'model_name': 'PaymentType',
                'app_label': 'billing',
                'choices': [
                    ('card', 'Credit/Debit Card'),
                    ('mobile_money', 'Mobile Money'),
                    ('bank_account', 'Bank Account'),
                    ('wallet', 'Digital Wallet'),
                ]
            },
            
            # Dashboard app
            {
                'model_name': 'WidgetType',
                'app_label': 'dashboard',
                'choices': [
                    ('revenue', 'Revenue Chart'),
                    ('pipeline', 'Sales Pipeline'),
                    ('tasks', 'Task List'),
                    ('leads', 'Lead Metrics'),
                    ('accounts', 'Accounts Overview'),
                    ('opportunities', 'Opportunities Overview'),
                    ('cases', 'Support Cases'),
                    ('nps', 'NPS Score'),
                    ('communication', 'Communication Stats'),
                    ('engagement', 'Engagement Metrics'),
                    ('sales', 'Sales Performance'),
                    ('products', 'Product Metrics'),
                    ('proposals', 'Proposal Pipeline'),
                    ('marketing', 'Marketing Campaigns'),
                    ('commissions', 'Commission Tracking'),
                    ('reports', 'Report Dashboard'),
                    ('leaderboard', 'Sales Leaderboard'),
                    ('activity', 'Recent Activity'),
                    ('automation', 'Automation Workflows'),
                    ('settings', 'System Settings'),
                    ('learn', 'Learning Progress'),
                    ('developer', 'Developer Tools'),
                    ('billing', 'Billing Overview'),
                    ('infrastructure', 'Infrastructure Usage'),
                    ('tenants', 'Tenant Management'),
                    ('audit_logs', 'Audit Logs'),
                    ('feature_flags', 'Feature Flags'),
                    ('global_alerts', 'Global Alerts'),
                ]
            },
            {
                'model_name': 'WidgetCategory',
                'app_label': 'dashboard',
                'choices': [
                    ('leads', 'Leads'),
                    ('opportunities', 'Opportunities'),
                    ('revenue', 'Revenue'),
                    ('sales', 'Sales'),
                    ('tasks', 'Tasks'),
                    ('cases', 'Cases'),
                    ('accounts', 'Accounts'),
                    ('products', 'Products'),
                    ('proposals', 'Proposals'),
                    ('communication', 'Communication'),
                    ('engagement', 'Engagement'),
                    ('nps', 'NPS'),
                    ('analytics', 'Analytics'),
                    ('billing', 'Billing'),
                    ('commissions', 'Commissions'),
                    ('infrastructure', 'Infrastructure'),
                    ('tenants', 'Tenants'),
                    ('marketing', 'Marketing'),
                    ('automation', 'Automation'),
                    ('learn', 'Learning'),
                    ('developer', 'Developer'),
                    ('control_plane', 'Control Plane'),
                    ('general', 'General'),
                ]
            },
            
            # Tasks app
            {
                'model_name': 'TaskPriority',
                'app_label': 'tasks',
                'choices': [
                    ('low', 'Low'),
                    ('medium', 'Medium'),
                    ('high', 'High'),
                    ('critical', 'Critical'),
                ]
            },
            {
                'model_name': 'TaskStatus',
                'app_label': 'tasks',
                'choices': [
                    ('todo', 'To Do'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                    ('overdue', 'Overdue'),
                ]
            },
            {
                'model_name': 'TaskType',
                'app_label': 'tasks',
                'choices': [
                    ('lead_review', 'Lead Review'),
                    ('lead_contact', 'Lead Contact'),
                    ('lead_qualify', 'Lead Qualification'),
                    ('account_followup', 'Account Follow-up'),
                    ('opportunity_demo', 'Opportunity Demo'),
                    ('proposal_followup', 'Proposal Follow-up'),
                    ('renewal_reminder', 'Renewal Reminder'),
                    ('csat_followup', 'CSAT Follow-up'),
                    ('case_escalation', 'Case Escalation'),
                    ('nps_detractor', 'NPS Detractor Follow-up'),
                    ('esg_engagement', 'ESG Engagement'),
                    ('custom', 'Custom Task'),
                ]
            },
            {
                'model_name': 'RecurrencePattern',
                'app_label': 'tasks',
                'choices': [
                    ('none', 'None'),
                    ('daily', 'Daily'),
                    ('weekly', 'Weekly'),
                    ('monthly', 'Monthly'),
                    ('quarterly', 'Quarterly'),
                    ('yearly', 'Yearly'),
                ]
            },
            
            # Settings app
            {
                'model_name': 'SettingType',
                'app_label': 'settings_app',
                'choices': [
                    ('text', 'Text'),
                    ('number', 'Number'),
                    ('boolean', 'Boolean'),
                    ('select', 'Dropdown'),
                    ('json', 'JSON'),
                ]
            },
            {
                'model_name': 'ModelChoice',
                'app_label': 'settings_app',
                'choices': [
                    ('Account', 'Account'),
                    ('Lead', 'Lead'),
                    ('Opportunity', 'Opportunity'),
                    ('Product', 'Product'),
                    ('Case', 'Case'),
                ]
            },
            {
                'model_name': 'FieldType',
                'app_label': 'settings_app',
                'choices': [
                    ('text', 'Text'),
                    ('number', 'Number'),
                    ('date', 'Date'),
                    ('boolean', 'Checkbox'),
                    ('select', 'Dropdown'),
                    ('textarea', 'Text Area'),
                ]
            },
            {
                'model_name': 'ModuleChoice',
                'app_label': 'settings_app',
                'choices': [
                    ('leads', 'Leads'),
                    ('accounts', 'Accounts'),
                    ('opportunities', 'Opportunities'),
                    ('cases', 'Cases'),
                    ('proposals', 'Proposals'),
                    ('products', 'Products'),
                    ('tasks', 'Tasks'),
                    ('dashboard', 'Dashboard'),
                    ('reports', 'Reports'),
                    ('commissions', 'Commissions'),
                ]
            },
            {
                'model_name': 'TeamRole',
                'app_label': 'settings_app',
                'choices': [
                    ('sales_rep', 'Sales Representative'),
                    ('sales_manager', 'Sales Manager'),
                    ('account_manager', 'Account Manager'),
                    ('sales_director', 'Sales Director'),
                    ('ceo', 'CEO'),
                    ('admin', 'Administrator'),
                ]
            },
            {
                'model_name': 'Territory',
                'app_label': 'settings_app',
                'choices': [
                    ('north_america', 'North America'),
                    ('emea', 'EMEA'),
                    ('apac', 'APAC'),
                    ('latam', 'Latin America'),
                ]
            },
            {
                'model_name': 'AssignmentRuleType',
                'app_label': 'settings_app',
                'choices': [
                    ('round_robin', 'Round Robin'),
                    ('territory', 'Territory-Based'),
                    ('load_balanced', 'Load Balanced'),
                    ('criteria', 'Criteria-Based'),
                ]
            },
            {
                'model_name': 'PipelineType',
                'app_label': 'settings_app',
                'choices': [
                    ('sales', 'Sales Pipeline'),
                    ('support', 'Support Pipeline'),
                    ('onboarding', 'Customer Onboarding'),
                    ('renewal', 'Renewal Process'),
                ]
            },
            {
                'model_name': 'EmailProvider',
                'app_label': 'settings_app',
                'choices': [
                    ('gmail', 'Gmail'),
                    ('outlook', 'Outlook/Office 365'),
                ]
            },
            {
                'model_name': 'ActionType',
                'app_label': 'settings_app',
                'choices': [
                    ('email_open', 'Email Open'),
                    ('link_click', 'Link Click'),
                    ('web_visit', 'Website Visit'),
                    ('form_submit', 'Form Submission'),
                    ('content_download', 'Content Download'),
                    ('landing_page_visit', 'Landing Page Visit'),
                ]
            },
            {
                'model_name': 'OperatorType',
                'app_label': 'settings_app',
                'choices': [
                    ('equals', 'Equals'),
                    ('contains', 'Contains'),
                    ('in', 'In List'),
                    ('gt', 'Greater Than'),
                    ('lt', 'Less Than'),
                ]
            },
            
            # Reports app
            {
                'model_name': 'ReportType',
                'app_label': 'reports',
                'choices': [
                    ('sales_performance', 'Sales Performance'),
                    ('esg_impact', 'ESG Impact'),
                    ('pipeline_forecast', 'Pipeline Forecast'),
                    ('csrd_compliance', 'CSRD Compliance'),
                    ('leads_recent', 'Leads (Last 7 Days)'),
                    ('cases_recent', 'Cases (Last 3 Months)'),
                    ('custom', 'Custom'),
                ]
            },
            {
                'model_name': 'ReportScheduleFrequency',
                'app_label': 'reports',
                'choices': [
                    ('daily', 'Daily'),
                    ('weekly', 'Weekly'),
                    ('monthly', 'Monthly'),
                    ('quarterly', 'Quarterly'),
                ]
            },
            {
                'model_name': 'ExportFormat',
                'app_label': 'reports',
                'choices': [
                    ('csv', 'CSV'),
                    ('xlsx', 'Excel'),
                    ('pdf', 'PDF'),
                ]
            },
            {
                'model_name': 'WidgetType',
                'app_label': 'reports',
                'choices': [
                    ('kpi_card', 'KPI Card'),
                    ('chart', 'Chart'),
                    ('table', 'Data Table'),
                    ('trend', 'Trend Chart'),
                ]
            },
            {
                'model_name': 'TemplateType',
                'app_label': 'reports',
                'choices': [
                    ('financial', 'Financial'),
                    ('sales', 'Sales'),
                    ('marketing', 'Marketing'),
                    ('customer', 'Customer'),
                    ('operational', 'Operational'),
                ]
            },
            {
                'model_name': 'TemplateFormat',
                'app_label': 'reports',
                'choices': [
                    ('html', 'HTML'),
                    ('markdown', 'Markdown'),
                    ('json', 'JSON'),
                    ('xml', 'XML'),
                ]
            },
            {
                'model_name': 'ReportAction',
                'app_label': 'reports',
                'choices': [
                    ('viewed', 'Viewed'),
                    ('downloaded', 'Downloaded'),
                    ('shared', 'Shared'),
                    ('scheduled', 'Scheduled'),
                ]
            },
            {
                'model_name': 'ReportFormat',
                'app_label': 'reports',
                'choices': [
                    ('web', 'Web View'),
                    ('email', 'Email Report'),
                    ('pdf', 'PDF Export'),
                    ('dashboard', 'Dashboard Widget'),
                ]
            },
            {
                'model_name': 'SubscriptionType',
                'app_label': 'reports',
                'choices': [
                    ('instant', 'Instant'),
                    ('scheduled', 'Scheduled'),
                    ('on_demand', 'On Demand'),
                ]
            },
            {
                'model_name': 'NotificationChannel',
                'app_label': 'reports',
                'choices': [
                    ('email', 'Email'),
                    ('web', 'Web Notification'),
                    ('slack', 'Slack'),
                    ('teams', 'Microsoft Teams'),
                ]
            },
            
            # Marketing app
            {
                'model_name': 'CampaignStatus',
                'app_label': 'marketing',
                'choices': [
                    ('draft', 'Draft'),
                    ('scheduled', 'Scheduled'),
                    ('sending', 'Sending'),
                    ('sent', 'Sent'),
                    ('paused', 'Paused'),
                    ('cancelled', 'Cancelled'),
                ]
            },
            {
                'model_name': 'EmailProvider',
                'app_label': 'marketing',
                'choices': [
                    ('ses', 'Amazon SES'),
                    ('sendgrid', 'SendGrid'),
                    ('mailgun', 'Mailgun'),
                    ('native', 'Django Email'),
                ]
            },
            {
                'model_name': 'BlockType',
                'app_label': 'marketing',
                'choices': [
                    ('hero', 'Hero Section'),
                    ('features', 'Features'),
                    ('testimonials', 'Testimonials'),
                    ('pricing', 'Pricing'),
                    ('cta', 'Call to Action'),
                    ('faq', 'FAQ'),
                    ('text', 'Text Content'),
                    ('image', 'Image'),
                    ('video', 'Video'),
                    ('form', 'Contact Form'),
                ]
            },
            {
                'model_name': 'EmailCategory',
                'app_label': 'marketing',
                'choices': [
                    ('newsletter', 'Newsletter'),
                    ('transactional', 'Transactional'),
                    ('follow_up', 'Follow-up'),
                    ('welcome', 'Welcome'),
                    ('reminder', 'Reminder'),
                    ('promotional', 'Promotional'),
                    ('other', 'Other'),
                ]
            },
            {
                'model_name': 'MessageType',
                'app_label': 'marketing',
                'choices': [
                    ('sms', 'SMS'),
                    ('in_app', 'In-App Message'),
                    ('push', 'Push Notification'),
                    ('slack', 'Slack Message'),
                ]
            },
            {
                'model_name': 'MessageCategory',
                'app_label': 'marketing',
                'choices': [
                    ('reminder', 'Reminder'),
                    ('notification', 'Notification'),
                    ('alert', 'Alert'),
                    ('update', 'Update'),
                    ('other', 'Other'),
                ]
            },
            
            # Opportunities app
            {
                'model_name': 'DealSizeCategory',
                'app_label': 'opportunities',
                'choices': [
                    ('small', 'Small'),
                    ('medium', 'Medium'),
                    ('large', 'Large'),
                ]
            },
        ]

        # Process each tenant
        for tenant in tenants:
            self.stdout.write(f'Populating choices for tenant: {tenant.name}')
            
            for mapping in choice_mappings:
                try:
                    # Get the model class
                    model_class = apps.get_model(mapping['app_label'], mapping['model_name'])
                    
                    # Create choices for this tenant
                    for name, label in mapping['choices']:
                        # Check if the choice already exists for this tenant
                        obj, created = model_class.objects.get_or_create(
                            name=name,
                            tenant_id=tenant.id,
                            defaults={
                                'label': label,
                                'is_active': True,
                                'is_system': True
                            }
                        )
                        
                        if created:
                            self.stdout.write(
                                f'  Created {mapping["model_name"]} choice: {name} -> {label}'
                            )
                        else:
                            self.stdout.write(
                                f'  Skipped existing {mapping["model_name"]} choice: {name}'
                            )
                
                except LookupError:
                    self.stdout.write(
                        self.style.WARNING(f'Model {mapping["model_name"]} not found in app {mapping["app_label"]}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated dynamic choice models with initial data')
        )
