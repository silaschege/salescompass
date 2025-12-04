from django.db import models
from django.conf import settings
from core.models import TenantModel, TimeStampedModel
from opportunities.models import Opportunity
from products.models import Product

class CommissionPlan(TenantModel):
    """
    Defines a commission plan that can be assigned to users.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
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
        return self.name

class CommissionRule(TenantModel):
    """
    Specific rules within a plan (e.g., 10% on hardware, 5% on software).
    """
    plan = models.ForeignKey(CommissionPlan, on_delete=models.CASCADE, related_name='rules', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='commission_rules', help_text="Specific product this rule applies to. Leave blank for all.")
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
        return f"{self.plan.name} - {self.rate_value}% ({self.get_rate_type_display()})"

class UserCommissionPlan(TenantModel):
    """
    Assigns a plan to a user for a specific period.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_plans')
    plan = models.ForeignKey(CommissionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.plan}"

class Quota(TenantModel):
    """
    Sales target for a user in a given period.
    """
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_records')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='commissions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    rate_applied = models.DecimalField(max_digits=5, decimal_places=2, help_text="The percentage rate used.")
    date_earned = models.DateField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('paid', 'Paid')], default='pending')
    
    def __str__(self):
        return f"{self.user} - {self.amount} on {self.opportunity}"

class Adjustment(TenantModel):
    """
    Bonuses, deductions, or draws.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commission_adjustments')
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Positive for bonus, negative for deduction.")
    description = models.CharField(max_length=255)
    date = models.DateField()
    type = models.CharField(max_length=20, choices=[('bonus', 'Bonus'), ('deduction', 'Deduction'), ('draw', 'Draw'), ('clawback', 'Clawback')])

    def __str__(self):
        return f"{self.user} - {self.type}: {self.amount}"
