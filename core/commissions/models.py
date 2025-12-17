from django.db import models
from django.conf import settings
from core.models import  TimeStampedModel
from opportunities.models import Opportunity
from tenants.models import TenantAwareModel as TenantModel
from products.models import Product

class CommissionPlan(TenantModel):
    """
    Defines a commission plan that can be assigned to users.
    """
    commission_plan_id = models.AutoField(primary_key=True)
    commission_plan_name = models.CharField(max_length=100)
    commission_plan_description = models.TextField(blank=True)
    commission_plan_is_active = models.BooleanField(default=True)
    
    BASIS_CHOICES = [
        ('revenue', 'Total Revenue'),
        ('margin', 'Gross Margin/Profit'),
        ('units', 'Units Sold'),
        ('acv', 'Annual Contract Value (ACV)'),
        ('mrr', 'Monthly Recurring Revenue (MRR)'),
    ]
    basis = models.CharField(max_length=20, choices=BASIS_CHOICES, default='revenue')
    
    PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')

    def __str__(self):
        return self.commission_plan_name

class CommissionRule(TenantModel):
    """
    Specific rules within a plan (e.g., 10% on hardware, 5% on software).
    """
    commission_rule_id = models.AutoField(primary_key=True)
    commission_rule_plan = models.ForeignKey(CommissionPlan, on_delete=models.CASCADE, related_name='rules', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, help_text="Specific product this rule applies to. Leave blank for all.")

    product_category = models.CharField(max_length=100, blank=True, help_text="Category of products this rule applies to.")
    
    RATE_TYPE_CHOICES = [
        ('flat', 'Flat Rate'),
        ('tiered', 'Tiered Rate'),
    ]
    rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='flat')
    
    rate_value = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage (e.g. 10.00 for 10%) or fixed amount.")
    
    # For Tiered Rates
    tier_min_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Minimum sales amount for this tier.")
    tier_max_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="Maximum sales amount for this tier. Leave blank for infinity.")

    def __str__(self):
        return f"{self.commission_rule_plan.commission_plan_name if self.commission_rule_plan else 'No Plan'} - {self.rate_value}% ({self.get_rate_type_display()})"

class UserCommissionPlan(TenantModel):
    """
    Assigns a plan to a user for a specific period.
    """
    user_commission_plan_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_plans')
    assigned_plan = models.ForeignKey(CommissionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.assigned_plan}"

class Quota(TenantModel):
    """
    Sales target for a user in a given period.
    """
    quota_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quotas')
    period_start = models.DateField()
    period_end = models.DateField()
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    
    def __str__(self):
        return f"{self.user} - {self.period_start} to {self.period_end}: {self.target_amount}"

class Commission(TenantModel):
    """
    Record of commission earned from a specific opportunity.
    """
    commission_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_records')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='commissions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    rate_applied = models.DecimalField(max_digits=5, decimal_places=2, help_text="The percentage rate used.")
    date_earned = models.DateField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('paid', 'Paid')], default='pending')
    payment_record = models.ForeignKey('CommissionPayment', on_delete=models.SET_NULL, null=True, blank=True, related_name='commissions')
    
    def __str__(self):
        return f"{self.user} - {self.amount} on {self.opportunity}"

class Adjustment(TenantModel):
    """
    Bonuses, deductions, or draws.
    """
    adjustment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_adjustments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Positive for bonus, negative for deduction.")
    adjusted_description = models.CharField(max_length=255)
    date = models.DateField()
    type = models.CharField(max_length=20, choices=[('bonus', 'Bonus'), ('deduction', 'Deduction'), ('draw', 'Draw'), ('clawback', 'Clawback')])

    def __str__(self):
        return f"{self.user} - {self.type}: {self.amount}"

class CommissionPayment(TenantModel):
    """
    Tracks actual payments of commissions to users.
    """
    commission_payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_payments')
    period_start = models.DateField()
    period_end = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_date = models.DateField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('calculated', 'Calculated'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='calculated')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user} - {self.period_start} to {self.period_end}: {self.total_amount}"
