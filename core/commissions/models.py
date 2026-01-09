from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from opportunities.models import Opportunity
from tenants.models import TenantAwareModel as TenantModel
from products.models import Product

class CommissionPlan(TimeStampedModel, TenantModel):
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

class CommissionRule(TimeStampedModel, TenantModel):
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
        ('accelerator', 'Accelerator'),
        ('decelerator', 'Decelerator'),
    ]
    rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES, default='flat')
    
    rate_value = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage (e.g. 10.00 for 10%) or fixed amount.")
    
    # For Tiered Rates
    tier_min_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Minimum sales amount for this tier.")
    tier_max_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="Maximum sales amount for this tier. Leave blank for infinity.")

    # For accelerator/decelerator
    performance_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Performance threshold for accelerator/decelerator (e.g., 90 for 90% attainment)")
    
    # For split commissions
    split_with = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='split_commissions', help_text="User to split commission with (for team deals)")
    split_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, help_text="Percentage of commission to give to the split user (e.g., 50 for 50%)")

    def __str__(self):
        return f"{self.commission_rule_plan.commission_plan_name if self.commission_rule_plan else 'No Plan'} - {self.rate_value}% ({self.get_rate_type_display()})"

class UserCommissionPlan(TimeStampedModel, TenantModel):
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

class Quota(TimeStampedModel, TenantModel):
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

class Commission(TimeStampedModel, TenantModel):
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
    
    # Add field to track if this commission was split
    is_split = models.BooleanField(default=False)
    original_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Original amount before any splits")

    def __str__(self):
        return f"{self.user} - {self.amount} on {self.opportunity}"

class SplitCommission(TimeStampedModel, TenantModel):
    """
    Records for split commissions between multiple users.
    """
    SPLIT_TYPE_CHOICES = [
        ('team_deal', 'Team Deal'),
        ('overlay', 'Overlay Commission'),
        ('referral', 'Referral'),
    ]
    
    split_commission_id = models.AutoField(primary_key=True)
    main_commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name='splits')
    split_with_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_splits')
    split_amount = models.DecimalField(max_digits=12, decimal_places=2)
    split_type = models.CharField(max_length=20, choices=SPLIT_TYPE_CHOICES, default='team_deal')
    split_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of original commission")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.split_with_user} - {self.split_amount} split from {self.main_commission}"

class Adjustment(TimeStampedModel, TenantModel):
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

class CommissionPayment(TimeStampedModel, TenantModel):
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

class CommissionPlanVersion(TimeStampedModel, TenantModel):
    """
    Versioning for commission plans to track changes over time.
    """
    plan_version_id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(CommissionPlan, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    effective_date = models.DateField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, help_text="Description of changes in this version")
    
    # Store the plan data as JSON for historical reference
    plan_data = models.JSONField(help_text="JSON representation of the plan at this version")
    
    def __str__(self):
        return f"{self.plan.commission_plan_name} - v{self.version_number}"

class CommissionPlanTemplate(TimeStampedModel, TenantModel):
    """
    Template for creating commission plans.
    """
    template_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    template_data = models.JSONField(help_text="JSON representation of the plan template")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class CommissionDispute(TimeStampedModel, TenantModel):
    """
    Record of disputes on commission calculations.
    """
    DISPUTE_STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    
    DISPUTE_REASON_CHOICES = [
        ('calculation_error', 'Calculation Error'),
        ('incorrect_rate', 'Incorrect Rate Applied'),
        ('wrong_user', 'Commission Assigned to Wrong User'),
        ('duplicate', 'Duplicate Commission'),
        ('other', 'Other'),
    ]
    
    dispute_id = models.AutoField(primary_key=True)
    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='raised_disputes')
    reason = models.CharField(max_length=50, choices=DISPUTE_REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=DISPUTE_STATUS_CHOICES, default='open')
    date_raised = models.DateTimeField(auto_now_add=True)
    date_resolved = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_disputes')
    resolution_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Dispute on {self.commission} - {self.get_status_display()}"

class CommissionAuditLog(TimeStampedModel, TenantModel):
    """
    Audit trail for commission calculations and changes.
    """
    AUDIT_ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('disputed', 'Disputed'),
        ('adjusted', 'Adjusted'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('deleted', 'Deleted'),
    ]
    
    audit_id = models.AutoField(primary_key=True)
    commission = models.ForeignKey(Commission, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=AUDIT_ACTION_CHOICES)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    old_values = models.JSONField(null=True, blank=True, help_text="JSON of old field values")
    new_values = models.JSONField(null=True, blank=True, help_text="JSON of new field values")
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.action} on {self.commission} by {self.performed_by}"