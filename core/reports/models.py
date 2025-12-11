from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
from core.models import User

# Legacy choices - kept for backward compatibility during migration
REPORT_TYPE_CHOICES = [
    ('sales_performance', 'Sales Performance'),
    ('esg_impact', 'ESG Impact'),
    ('pipeline_forecast', 'Pipeline Forecast'),
    ('csrd_compliance', 'CSRD Compliance'),
    ('leads_recent', 'Leads (Last 7 Days)'),
    ('cases_recent', 'Cases (Last 3 Months)'),
    ('custom', 'Custom'),
]

SCHEDULE_FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
]

EXPORT_FORMATS = [
    ('csv', 'CSV'),
    ('xlsx', 'Excel'),
    ('pdf', 'PDF'),
]

WIDGET_TYPES = [
    ('kpi_card', 'KPI Card'),
    ('chart', 'Chart'),
    ('table', 'Data Table'),
    ('trend', 'Trend Chart'),
]

TEMPLATE_TYPES = [
    ('financial', 'Financial'),
    ('sales', 'Sales'),
    ('marketing', 'Marketing'),
    ('customer', 'Customer'),
    ('operational', 'Operational'),
]

TEMPLATE_FORMATS = [
    ('html', 'HTML'),
    ('markdown', 'Markdown'),
    ('json', 'JSON'),
    ('xml', 'XML'),
]

ACTION_CHOICES = [
    ('viewed', 'Viewed'),
    ('downloaded', 'Downloaded'),
    ('shared', 'Shared'),
    ('scheduled', 'Scheduled'),
]

REPORT_FORMAT_CHOICES = [
    ('web', 'Web View'),
    ('email', 'Email Report'),
    ('pdf', 'PDF Export'),
    ('dashboard', 'Dashboard Widget'),
]

SUBSCRIPTION_TYPES = [
    ('instant', 'Instant'),
    ('scheduled', 'Scheduled'),
    ('on_demand', 'On Demand'),
]

NOTIFICATION_CHANNELS = [
    ('email', 'Email'),
    ('web', 'Web Notification'),
    ('slack', 'Slack'),
    ('teams', 'Microsoft Teams'),
]


class ReportType(TenantModel):
    """
    Dynamic report type values - allows tenant-specific report type tracking.
    """
    type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'sales_performance', 'custom'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Sales Performance', 'Custom'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'type_name']
        unique_together = [('tenant', 'type_name')]
        verbose_name_plural = 'Report Types'
    
    def __str__(self):
        return self.label


class ReportScheduleFrequency(TenantModel):
    """
    Dynamic report schedule frequency values - allows tenant-specific frequency tracking.
    """
    frequency_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'daily', 'weekly'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Daily', 'Weekly'
    order = models.IntegerField(default=0)
    frequency_is_active = models.BooleanField(default=True, help_text="Whether this frequency is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'frequency_name']
        unique_together = [('tenant', 'frequency_name')]
        verbose_name_plural = 'Report Schedule Frequencies'
    
    def __str__(self):
        return self.label


class ExportFormat(TenantModel):
    """
    Dynamic export format values - allows tenant-specific format tracking.
    """
    format_name = models.CharField(max_length=10, db_index=True, help_text="e.g., 'csv', 'xlsx'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=20)  # e.g., 'CSV', 'Excel'
    order = models.IntegerField(default=0)
    format_is_active = models.BooleanField(default=True, help_text="Whether this format is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'format_name']
        unique_together = [('tenant', 'format_name')]
        verbose_name_plural = 'Export Formats'
    
    def __str__(self):
        return self.label





class TemplateType(TenantModel):
    """
    Dynamic template type values - allows tenant-specific template type tracking.
    """
    template_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'financial', 'sales'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Financial', 'Sales'
    order = models.IntegerField(default=0)
    template_type_is_active = models.BooleanField(default=True, help_text="Whether this template type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'template_type_name']
        unique_together = [('tenant', 'template_type_name')]
        verbose_name_plural = 'Template Types'
    
    def __str__(self):
        return self.label


class TemplateFormat(TenantModel):
    """
    Dynamic template format values - allows tenant-specific format tracking.
    """
    format_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'html', 'markdown'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=20)  # e.g., 'HTML', 'Markdown'
    order = models.IntegerField(default=0)
    format_is_active = models.BooleanField(default=True, help_text="Whether this format is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'format_name']
        unique_together = [('tenant', 'format_name')]
        verbose_name_plural = 'Template Formats'
    
    def __str__(self):
        return self.label


class ReportAction(TenantModel):
    """
    Dynamic report action values - allows tenant-specific action tracking.
    """
    action_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'viewed', 'downloaded'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Viewed', 'Downloaded'
    order = models.IntegerField(default=0)
    action_is_active = models.BooleanField(default=True, help_text="Whether this action is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'action_name']
        unique_together = [('tenant', 'action_name')]
        verbose_name_plural = 'Report Actions'
    
    def __str__(self):
        return self.label


class ReportFormat(TenantModel):
    """
    Dynamic report format values - allows tenant-specific format tracking.
    """
    format_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'web', 'email'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Web View', 'Email Report'
    order = models.IntegerField(default=0)
    format_is_active = models.BooleanField(default=True, help_text="Whether this format is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'format_name']
        unique_together = [('tenant', 'format_name')]
        verbose_name_plural = 'Report Formats'
    
    def __str__(self):
        return self.label


class SubscriptionType(TenantModel):
    """
    Dynamic subscription type values - allows tenant-specific subscription type tracking.
    """
    subscription_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'instant', 'scheduled'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Instant', 'Scheduled'
    order = models.IntegerField(default=0)
    subscription_type_is_active = models.BooleanField(default=True, help_text="Whether this subscription type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'subscription_type_name']
        unique_together = [('tenant', 'subscription_type_name')]
        verbose_name_plural = 'Subscription Types'
    
    def __str__(self):
        return self.label


class NotificationChannel(TenantModel):
    """
    Dynamic notification channel values - allows tenant-specific channel tracking.
    """
    channel_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'email', 'web'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Email', 'Web Notification'
    order = models.IntegerField(default=0)
    channel_is_active = models.BooleanField(default=True, help_text="Whether this channel is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'channel_name']
        unique_together = [('tenant', 'channel_name')]
        verbose_name_plural = 'Notification Channels'
    
    def __str__(self):
        return self.label


class Report(TenantModel):
    report_name = models.CharField(max_length=255, help_text="Name of the report")  # Renamed from 'name' to avoid conflict
    report_description = models.TextField(blank=True, help_text="Description of the report")  # Renamed from 'description' to avoid conflict with base class
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    # New dynamic field
    report_type_ref = models.ForeignKey(
        'ReportType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='reports',
        help_text="Dynamic report type (replaces report_type field)"
    )
    query_config = models.JSONField(default=dict, blank=True, help_text="Configuration for the report query")
    report_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    is_scheduled = models.BooleanField(default=False, help_text="Whether this report runs on a schedule")
    schedule_frequency = models.CharField(max_length=50, choices=SCHEDULE_FREQUENCY_CHOICES, blank=True)
    # New dynamic field
    schedule_frequency_ref = models.ForeignKey(
        'ReportScheduleFrequency',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='reports',
        help_text="Dynamic schedule frequency (replaces schedule_frequency field)"
    )
    last_run = models.DateTimeField(null=True, blank=True, help_text="When the report was last generated")
    last_run_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    # New dynamic field for status will be handled separately if needed
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_created')
    report_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    report_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.report_name


SCHEDULE_FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('yearly', 'Yearly'),
]

class ReportSchedule(TenantModel):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='schedules')
    schedule_name = models.CharField(max_length=255, help_text="Name of the report schedule")  # Renamed from 'name' to avoid conflict
    schedule_description = models.TextField(blank=True, help_text="Description of the schedule")  # Renamed from 'description' to avoid conflict with base class
    frequency = models.CharField(max_length=20, choices=SCHEDULE_FREQUENCY_CHOICES)
    # New dynamic field
    frequency_ref = models.ForeignKey(
        'ReportScheduleFrequency',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_schedules',
        help_text="Dynamic frequency (replaces frequency field)"
    )
    recipients = models.JSONField(default=list)
    schedule_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    next_run = models.DateTimeField()
    last_run = models.DateTimeField(null=True, blank=True)
    schedule_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    schedule_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.schedule_name} - {self.report.report_name}"


class ReportExport(TenantModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    # New dynamic field
    export_format_ref = models.ForeignKey(
        'ExportFormat',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_exports',
        help_text="Dynamic export format (replaces export_format field)"
    )
    file = models.FileField(upload_to='report_exports/')
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='report_exports_created')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    export_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.report.report_name} - {self.export_format}"


class ReportTemplate(TenantModel):
    template_name = models.CharField(max_length=255, help_text="Name of the report template")  # Renamed from 'name' to avoid conflict
    template_description = models.TextField(blank=True, help_text="Description of the report template")  # Renamed from 'description' to avoid conflict with base class
    template_type = models.CharField(max_length=100, choices=TEMPLATE_TYPES)
    # New dynamic field
    template_type_ref = models.ForeignKey(
        TemplateType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_templates',
        help_text="Dynamic template type (replaces template_type field)"
    )
    template_content = models.TextField(help_text="Template content (HTML, Markdown, etc.)")
    template_format = models.CharField(max_length=20, choices=TEMPLATE_FORMATS)
    # New dynamic field
    template_format_ref = models.ForeignKey(
        TemplateFormat,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_templates',
        help_text="Dynamic template format (replaces template_format field)"
    )
    template_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='report_templates_created')
    template_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    template_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.template_name


class ReportAnalytics(TenantModel):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='analytics')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_analytics')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    # New dynamic field
    action_ref = models.ForeignKey(
        ReportAction,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_analytics',
        help_text="Dynamic action (replaces action field)"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the action")

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.report.name}"


class ReportSubscriber(TenantModel):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='subscribers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribed_reports')
    email = models.EmailField(help_text="Email to send the report to (can be different from user's email)")
    subscription_type = models.CharField(max_length=50, choices=SUBSCRIPTION_TYPES)
    # New dynamic field
    subscription_type_ref = models.ForeignKey(
        SubscriptionType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_subscribers',
        help_text="Dynamic subscription type (replaces subscription_type field)"
    )
    report_format = models.CharField(max_length=20, choices=REPORT_FORMAT_CHOICES, default='email')
    # New dynamic field
    report_format_ref = models.ForeignKey(
        ReportFormat,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_subscribers',
        help_text="Dynamic report format (replaces report_format field)"
    )
    subscriber_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    subscriber_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    next_scheduled_send = models.DateTimeField(null=True, blank=True, help_text="When the report is next scheduled to be sent")

    def __str__(self):
        return f"{self.user.email} - {self.report.report_name}"


class ReportNotification(TenantModel):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    report_schedule = models.ForeignKey(ReportSchedule, on_delete=models.CASCADE, related_name='notifications')
    recipient_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    notification_channel = models.CharField(max_length=50, choices=NOTIFICATION_CHANNELS)
    # New dynamic field
    notification_channel_ref = models.ForeignKey(
        NotificationChannel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='report_notifications',
        help_text="Dynamic notification channel (replaces notification_channel field)"
    )
    notification_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.recipient_email} - {self.report_schedule.schedule_name}"
