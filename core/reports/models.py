from django.db import models
from core.models import TenantModel

# Remove this import - it causes circular dependency
# from core.models import User

REPORT_TYPES = [
    ('sales_performance', 'Sales Performance'),
    ('esg_impact', 'ESG Impact'),
    ('pipeline_forecast', 'Pipeline Forecast'),
    ('csrd_compliance', 'CSRD Compliance'),
    ('leads_recent', 'Leads (Last 7 Days)'),
    ('cases_recent', 'Cases (Last 3 Months)'),
    ('custom', 'Custom'),
]

SCHEDULE_FREQUENCY = [
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

class Report(TenantModel):
    """
    Custom report definition.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    is_active = models.BooleanField(default=True)
    # Use string reference instead of direct import
    owner = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Report configuration (JSON for flexibility)
    config = models.JSONField(default=dict, help_text="""
        {
            "entities": ["account", "opportunity"],
            "fields": ["name", "amount", "esg_score"],
            "filters": {"industry": "manufacturing"},
            "group_by": "owner",
            "sort_by": "amount"
        }
    """)
    
    # Dashboard embedding
    is_dashboard_widget = models.BooleanField(default=False)
    widget_position = models.CharField(max_length=50, blank=True)  # e.g., "top-left"
    widget_size = models.CharField(max_length=20, default='medium')  # small, medium, large

    def __str__(self):
        return self.name


class ReportSchedule(TenantModel):
    """
    Scheduled report delivery.
    """
    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='schedules')
    frequency = models.CharField(max_length=20, choices=SCHEDULE_FREQUENCY)
    recipients = models.JSONField(default=list)  # list of email addresses
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS, default='csv')
    next_run = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.report.name} ({self.frequency})"


class ReportExport(TenantModel):
    """
    Generated report export.
    """
    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    file = models.FileField(upload_to='report_exports/')
    # Use string reference
    generated_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.report.name} - {self.created_at}"


class DashboardWidget(TenantModel):
    """
    Dashboard widget configuration.
    """
    WIDGET_TYPES = [
        ('kpi_card', 'KPI Card'),
        ('chart', 'Chart'),
        ('table', 'Data Table'),
        ('trend', 'Trend Chart'),
    ]
    
    name = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    report = models.ForeignKey('Report', on_delete=models.CASCADE)
    position = models.CharField(max_length=20, default='main')  # main, sidebar, footer
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)  # widget-specific config

    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"