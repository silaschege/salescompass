from django.db import models
from django.utils import timezone
from tenants.models import TenantAwareModel as TenantModel
from core.models import TimeStampedModel, User
from products.models import Product

class InspectionRule(TenantModel, TimeStampedModel):
    """
    Defines what to check for a specific product or category.
    """
    name = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inspection_rules', null=True, blank=True)
    check_list = models.JSONField(help_text="JSON list of check items. Each item should be a dict with keys: id, label, type (bool, number, photo, text), required.")
    is_required_on_receipt = models.BooleanField(default=True)
    
    # Acceptance Sampling (AQL)
    sampling_type = models.CharField(max_length=20, choices=[
        ('100_percent', '100% Inspection'),
        ('acceptance_sampling', 'Acceptance Sampling (AQL)'),
    ], default='100_percent')
    aql_level = models.FloatField(null=True, blank=True, choices=[
        (0.65, '0.65'), (1.0, '1.0'), (1.5, '1.5'), (2.5, '2.5'), (4.0, '4.0'), (6.5, '6.5')
    ], help_text="Acceptable Quality Level")
    inspection_level = models.CharField(max_length=5, null=True, blank=True, choices=[
        ('S-1', 'S-1'), ('S-2', 'S-2'), ('S-3', 'S-3'), ('S-4', 'S-4'),
        ('I', 'General I'), ('II', 'General II'), ('III', 'General III')
    ], default='II')
    
    def __str__(self):
        return self.name

class InspectionLog(TenantModel, TimeStampedModel):
    """
    Result of a quality check.
    """
    STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('conditional', 'Conditional Pass'),
    ]

    rule = models.ForeignKey(InspectionRule, on_delete=models.CASCADE, related_name='logs')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections_performed')
    
    # Link to source (Purchase Order, Return, or Work Order)
    source_reference = models.CharField(max_length=100, help_text="PO #, WO #, etc.")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='passed')
    results_data = models.JSONField(help_text="Responses to the checklist items")
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"Inspection for {self.source_reference} - {self.status}"

class NonConformanceReport(TenantModel, TimeStampedModel):
    """
    Detailed report when a quality check fails.
    """
    inspection_log = models.OneToOneField(InspectionLog, on_delete=models.CASCADE, related_name='ncr')
    issue_description = models.TextField()
    root_cause = models.TextField(blank=True)
    action_taken = models.CharField(max_length=100, choices=[
        ('return_to_vendor', 'Return to Vendor'),
        ('rework', 'Rework Required'),
        ('scrap', 'Scrap Asset'),
        ('accept_as_is', 'Accept as is (Minor)'),
    ], blank=True)
    rca_type = models.CharField(max_length=20, choices=[
        ('5_whys', '5 Whys'),
        ('fishbone', 'Fishbone Diagram'),
        ('other', 'Other/None'),
    ], default='other')
    rca_data = models.JSONField(null=True, blank=True, help_text="Structured RCA findings (JSON)")
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"NCR for {self.inspection_log.source_reference}"

class InspectionAttachment(TenantModel, TimeStampedModel):
    """
    Photos or documents attached to an inspection.
    """
    inspection_log = models.ForeignKey(InspectionLog, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='quality_control/attachments/')
    caption = models.CharField(max_length=255, blank=True)
    item_id = models.CharField(max_length=50, blank=True, help_text="ID of the checklist item this attachment relates to")

    def __str__(self):
        return f"Attachment for {self.inspection_log}"

class CAPA(TenantModel, TimeStampedModel):
    """
    Corrective and Preventive Action (CAPA) tracking.
    """
    source_ncr = models.ForeignKey(NonConformanceReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas')
    capa_type = models.CharField(max_length=20, choices=[
        ('corrective', 'Corrective Action'),
        ('preventive', 'Preventive Action'),
    ], default='corrective')
    title = models.CharField(max_length=200)
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    action_plan = models.TextField()
    verification_plan = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('proposed', 'Proposed'),
        ('in_progress', 'In Progress'),
        ('verification', 'Verification'),
        ('closed', 'Closed'),
    ], default='proposed')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_capas')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_capas')
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"CAPA-{self.id:04d}: {self.title}"

class QualityCheckLibrary(TenantModel, TimeStampedModel):
    """
    Library of reusable standard quality check items.
    """
    label = models.CharField(max_length=255, help_text="The question or check item text")
    check_type = models.CharField(max_length=20, choices=[
        ('bool', 'Pass/Fail'),
        ('number', 'Value Range'),
        ('text', 'Observations'),
        ('photo', 'Visual Evidence'),
    ], default='bool')
    category = models.CharField(max_length=100, blank=True, help_text="Optional category for grouping (e.g., Safety, Packaging)")
    description = models.TextField(blank=True, help_text="Optional instructions for the inspector")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.label} ({self.get_check_type_display()})"

    class Meta:
        verbose_name = "Quality Check"
        verbose_name_plural = "Quality Check Library"
        ordering = ['category', 'label']
