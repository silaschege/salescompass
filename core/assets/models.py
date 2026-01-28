from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from decimal import Decimal

DEPRECIATION_METHOD_CHOICES = [
    ('straight_line', 'Straight Line'),
    ('declining_balance', 'Declining Balance'),
    ('no_depreciation', 'No Depreciation'),
]

ASSET_STATUS_CHOICES = [
    ('active', 'Active'),
    ('disposed', 'Disposed'),
    ('sold', 'Sold'),
    ('fully_depreciated', 'Fully Depreciated'),
]

class AssetCategory(TenantModel):
    name = models.CharField(max_length=100)
    depreciation_method = models.CharField(max_length=20, choices=DEPRECIATION_METHOD_CHOICES, default='straight_line')
    useful_life_years = models.IntegerField(default=5)
    
    # Integration with Accounting
    asset_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_as_cost')
    depreciation_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_depreciation_expense')
    accumulated_depreciation_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_accumulated_depreciation')
    
    # IAS 36 & 16 Extensions
    impairment_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_impairment_loss')
    revaluation_surplus_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_revaluation_surplus')

    class Meta:
        verbose_name_plural = "Asset Categories"
        unique_together = ['tenant', 'name']

    def __str__(self):
        return self.name

class FixedAsset(TenantModel):
    asset_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT)
    
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    current_value = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    # IAS 16 & 36 Compliance Extensions
    accumulated_impairment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revaluation_surplus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Component Accounting
    component_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='components', help_text="Support for IAS 16 component approach")
    
    # IFRS 16 Right-of-Use
    is_leased = models.BooleanField(default=False)
    lease_term_months = models.IntegerField(null=True, blank=True)
    
    # IAS 38 Intangibles
    is_intangible = models.BooleanField(default=False)
    
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=ASSET_STATUS_CHOICES, default='active')
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.current_value = self.purchase_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.asset_number})"

    def calculate_depreciation(self, target_date=None):
        """
        Calculate current cumulative depreciation and book value.
        target_date: Default to today.
        """
        from datetime import date
        if target_date is None:
            target_date = date.today()
            
        if self.category.depreciation_method == 'no_depreciation' or target_date <= self.purchase_date:
            return Decimal('0')

        # Years/Months between purchase and target
        diff_years = (target_date.year - self.purchase_date.year) + (target_date.month - self.purchase_date.month) / 12.0
        
        if diff_years <= 0:
            return Decimal('0')

        if self.category.depreciation_method == 'straight_line':
            # Straight Line: (Cost - Salvage) / Life
            annual_depreciation = (self.purchase_cost - self.salvage_value) / Decimal(str(self.category.useful_life_years))
            total_depreciation = annual_depreciation * Decimal(str(diff_years))
            
            # Cap at (Cost - Salvage)
            max_depreciation = self.purchase_cost - self.salvage_value
            return min(total_depreciation, max_depreciation).quantize(Decimal('0.01'))
            
        elif self.category.depreciation_method == 'declining_balance':
            # Simple Declining Balance (e.g., 20% flat of current value annually)
            # This is a bit more complex for partial years, but let's approximate
            rate = Decimal('2.0') / Decimal(str(self.category.useful_life_years)) # 200% declining
            years_passed = int(diff_years)
            remaining_value = self.purchase_cost
            for _ in range(years_passed):
                remaining_value *= (Decimal('1') - rate)
            
            # Partial months
            partial_year = Decimal(str(diff_years)) - Decimal(str(years_passed))
            if partial_year > 0:
                remaining_value *= (Decimal('1') - (rate * partial_year))

            total_depreciation = self.purchase_cost - remaining_value
            
            # Cap at salvage
            max_depreciation = self.purchase_cost - self.salvage_value
            return min(total_depreciation, max_depreciation).quantize(Decimal('0.01'))

        return Decimal('0')


class Depreciation(TenantModel):
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='depreciations')
    period = models.ForeignKey('accounting.FiscalPeriod', on_delete=models.PROTECT, null=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Ideally links to a journal entry
    journal_entry = models.ForeignKey('accounting.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset} - {self.date}: {self.amount}"

class AssetImpairment(TenantModel):
    """
    Records loss of economic benefit per IAS 36.
    """
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='impairments')
    date = models.DateField()
    impairment_loss = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    
    journal_entry = models.ForeignKey('accounting.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Impairment: {self.asset.name} - {self.impairment_loss}"

class AssetRevaluation(TenantModel):
    """
    Tracks fair value adjustments per IAS 16 revaluation model.
    """
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='revaluations')
    date = models.DateField()
    new_fair_value = models.DecimalField(max_digits=12, decimal_places=2)
    adjustment_amount = models.DecimalField(max_digits=12, decimal_places=2) # Positive if surplus, negative if loss
    
    journal_entry = models.ForeignKey('accounting.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revaluation: {self.asset.name} - {self.new_fair_value}"
