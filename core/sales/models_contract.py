from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import TimeStampedModel
from decimal import Decimal

class SalesContract(TenantModel, TimeStampedModel):
    """
    IFRS 15 Master Contract representing an agreement with a customer.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
    ]

    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='sales_contracts')
    contract_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    total_contract_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    proposal = models.ForeignKey('proposals.Proposal', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.contract_number})"

class PerformanceObligation(TenantModel, TimeStampedModel):
    """
    IFRS 15 Step 2: Distinct goods or services promised in a contract.
    """
    RECOGNITION_METHOD_CHOICES = [
        ('point_in_time', 'Point in Time (e.g., Delivery)'),
        ('over_time', 'Over Time (e.g., Service Subscription)'),
        ('milestone', 'Milestone Based'),
    ]

    STATUS_CHOICES = [
        ('unfulfilled', 'Unfulfilled'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
    ]

    contract = models.ForeignKey(SalesContract, on_delete=models.CASCADE, related_name='obligations')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Transaction price allocated per IFRS 15 Step 4")
    recognized_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    recognition_method = models.CharField(max_length=20, choices=RECOGNITION_METHOD_CHOICES, default='point_in_time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unfulfilled')
    
    # Timing (for 'over_time' recognition)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Financial Integration
    deferred_revenue_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='contract_liabilities')
    revenue_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='contract_revenue')

    def __str__(self):
        return f"{self.name} - {self.contract.contract_number}"

class RevenueSchedule(TenantModel, TimeStampedModel):
    """
    Individual events for revenue recognition.
    """
    obligation = models.ForeignKey(PerformanceObligation, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_recognized = models.BooleanField(default=False)
    
    journal_entry = models.ForeignKey('accounting.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.obligation.name}: {self.amount} on {self.date}"
