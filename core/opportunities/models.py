from django.db import models
from core.models import TimeStampedModel, TenantModel
from core.models import User
from accounts.models import Account
from core.managers import VisibilityAwareManager

class OpportunityStage(TenantModel):
    name = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    probability = models.FloatField(default=0.0, help_text="Default probability for this stage (0-100)")
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return self.name

class Opportunity(TenantModel):
    name = models.CharField(max_length=255)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='opportunities')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    stage = models.ForeignKey(OpportunityStage, on_delete=models.PROTECT, related_name='opportunities')
    close_date = models.DateField()
    probability = models.FloatField(default=0.0)  # 0.0–1.0
    
    # ESG
    esg_tagged = models.BooleanField(default=False)
    esg_impact_description = models.TextField(blank=True)
    
    # Products
    products = models.ManyToManyField('products.Product', through='OpportunityProduct')
    
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    objects = VisibilityAwareManager()

    @property
    def weighted_value(self):
        return float(self.amount) * self.probability

    def __str__(self):
        return f"{self.name} ({self.account.name})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_stage = None
        
        if not is_new:
            try:
                old_instance = Opportunity.objects.get(pk=self.pk)
                old_stage = old_instance.stage
            except Opportunity.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        from automation.utils import emit_event
        
        if is_new:
            emit_event('opportunities.created', {
                'opportunity_id': self.id,
                'name': self.name,
                'amount': float(self.amount),
                'stage': self.stage.name,
                'owner_id': self.owner_id if self.owner else None,
                'tenant_id': self.tenant_id
            })
            
        # Check for stage changes
        if old_stage and old_stage != self.stage:
            emit_event('opportunities.stage_changed', {
                'opportunity_id': self.id,
                'old_stage': old_stage.name,
                'new_stage': self.stage.name,
                'tenant_id': self.tenant_id
            })
            
            if self.stage.is_won and not old_stage.is_won:
                emit_event('opportunities.won', {
                    'opportunity_id': self.id,
                    'amount': float(self.amount),
                    'name': self.name,
                    'owner_id': self.owner_id if self.owner else None,
                    'tenant_id': self.tenant_id
                })
            elif self.stage.is_lost and not old_stage.is_lost:
                emit_event('opportunities.lost', {
                    'opportunity_id': self.id,
                    'amount': float(self.amount),
                    'name': self.name,
                    'tenant_id': self.tenant_id
                })


class OpportunityProduct(TenantModel):
    """
    Products associated with an opportunity.
    """
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.opportunity.name}"


class ForecastSnapshot(TenantModel):
    """
    Daily snapshot of sales forecast for reporting.
    """
    date = models.DateField()
    total_pipeline_value = models.DecimalField(max_digits=16, decimal_places=2)
    weighted_forecast = models.DecimalField(max_digits=16, decimal_places=2)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    class Meta:
        unique_together = [('date', 'tenant_id')]


class WinLossAnalysis(TenantModel):
    """
    Win/loss analysis records for opportunities.
    """
    opportunity = models.OneToOneField(Opportunity, on_delete=models.CASCADE)
    is_won = models.BooleanField()
    win_reason = models.TextField(blank=True)
    loss_reason = models.TextField(blank=True)
    competitor_name = models.CharField(max_length=255, blank=True)
    sales_cycle_days = models.IntegerField(default=0)
    deal_size_category = models.CharField(
        max_length=20,
        choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')],
        default='medium'
    )

    def __str__(self):
        return f"{'Won' if self.is_won else 'Lost'}: {self.opportunity.name}"