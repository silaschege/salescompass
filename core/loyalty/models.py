from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User,TimeStampedModel
from decimal import Decimal

TRANSACTION_TYPE_CHOICES = [
    ('earn', 'Earn Points'),
    ('redeem', 'Redeem Points'),
    ('adjust', 'Manual Adjustment'),
    ('expire', 'Points Expiration'),
    ('refund', 'Refund Reversal'),
]

TIER_CHOICES = [
    ('bronze', 'Bronze'),
    ('silver', 'Silver'),
    ('gold', 'Gold'),
    ('platinum', 'Platinum'),
]

class LoyaltyProgram(TenantModel):
    """
    Configuration for the loyalty program.
    """
    program_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Earning Rules
    points_per_currency = models.DecimalField(
        max_digits=10, decimal_places=2, default=1.0,
        help_text="Points earned per 1 unit of currency spent"
    )
    
    # Redemption Rules
    redemption_conversion_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.01,
        help_text="Currency value of 1 point (e.g., 0.01 = 1 point is $0.01)"
    )
    
    min_redemption_points = models.IntegerField(default=100)
    
    # IFRS 15 / IPSAS 34 Compliance
    breakage_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.10'),
        help_text="Estimated percentage of points that will never be redeemed (for breakage recognition)"
    )
    default_expiry_days = models.IntegerField(
        default=365, help_text="Default points validity in days"
    )
    
    deferred_revenue_account = models.ForeignKey(
        'accounting.ChartOfAccount', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='loyalty_programs',
        help_text="Liability account for point values (IFRS 15 Performance Obligation)"
    )

    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Loyalty Program"
        unique_together = ['tenant', 'program_name']

    def __str__(self):
        return self.program_name


class CustomerLoyalty(TenantModel,TimeStampedModel):
    """
    Customer's loyalty account status.
    """
    customer = models.OneToOneField('accounts.Account', on_delete=models.CASCADE, related_name='loyalty_account')
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.PROTECT, related_name='members')
    
    points_balance = models.IntegerField(default=0)
    total_points_earned = models.IntegerField(default=0)
    
    current_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    joined_date = models.DateField(auto_now_add=True)
    
    last_activity_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Loyalty Profile"

    def __str__(self):
        return f"{self.customer} - {self.points_balance} pts"


class LoyaltyTransaction(TenantModel):
    """
    Ledger of all point changes.
    """
    loyalty_account = models.ForeignKey(CustomerLoyalty, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    points = models.IntegerField(help_text="Positive for earn, negative for redeem")
    
    reference_number = models.CharField(max_length=100, blank=True, help_text="POS Transaction ID or External Ref")
    description = models.CharField(max_length=255)
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Financial Tracking
    allocated_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Deferred revenue allocated to this transaction (IFRS 15)"
    )
    
    # Expiry Tracking
    expiry_date = models.DateField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type}: {self.points} ({self.loyalty_account.customer})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update balance
            self.loyalty_account.points_balance += self.points
            
            if self.points > 0:
                self.loyalty_account.total_points_earned += self.points
                
                # Set expiry if not provided
                if not self.expiry_date and self.loyalty_account.program.default_expiry_days:
                    from django.utils import timezone
                    self.expiry_date = timezone.now().date() + timezone.timedelta(days=self.loyalty_account.program.default_expiry_days)
                    kwargs['force_update'] = True # Ensure expiry date is saved
                    self.save(update_fields=['expiry_date'])

            self.loyalty_account.save()

class LoyaltyTier(TenantModel):
    """
    Tier definitions for loyalty levels.
    """
    tier_name = models.CharField(max_length=20, choices=TIER_CHOICES)
    min_points = models.IntegerField()
    level = models.IntegerField(help_text="Numeric level (e.g., 1 for Bronze, 2 for Silver)")
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    
    class Meta:
        ordering = ['level']
        unique_together = ['tenant', 'tier_name']

    def __str__(self):
        return self.get_tier_name_display()
