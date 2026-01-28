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
    check_list = models.JSONField(help_text="JSON list of check items (e.g., ['Visual damage', 'Functionality'])")
    is_required_on_receipt = models.BooleanField(default=True)
    
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
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"NCR for {self.inspection_log.source_reference}"
