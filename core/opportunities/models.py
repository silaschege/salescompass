from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from settings_app.models import AssignmentRuleType
from settings_app.models import AssignmentRuleType

from core.managers import VisibilityAwareManager

# Legacy choices - kept for backward compatibility during migration
DEAL_SIZE_CATEGORIES = [
    ('small', 'Small'),
    ('medium', 'Medium'),
    ('large', 'Large'),
    ('enterprise', 'Enterprise'),
]

PIPELINE_TYPE_CHOICES = [
    ('sales', 'Sales Pipeline'),
    ('support', 'Support Pipeline'),
    ('onboarding', 'Customer Onboarding'),
    ('renewal', 'Renewal Process'),
]

class PipelineType(TenantModel):
    """
    Dynamic pipeline type values - allows tenant-specific pipeline type tracking.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="opportunity_pipeline_types"
    )
    pipeline_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'sales', 'support'")
    label = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    pipeline_type_is_active = models.BooleanField(default=True, help_text="Whether this pipeline type is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'pipeline_type_name']
        unique_together = [('tenant', 'pipeline_type_name')]
        verbose_name_plural = 'Pipeline Types'
    
    def __str__(self):
        return self.label



class DealSizeCategory(TenantModel):
    """
    Dynamic deal size category values - allows tenant-specific category tracking.
    """
    category_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'small', 'medium'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Small', 'Medium'
    order = models.IntegerField(default=0)
    category_is_active = models.BooleanField(default=True, help_text="Whether this category is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'category_name']
        unique_together = [('tenant', 'category_name')]
        verbose_name_plural = 'Deal Size Categories'
    
    def __str__(self):
        return self.label


class OpportunityStage(TenantModel):
    pipeline_type = models.CharField(max_length=50, choices=PIPELINE_TYPE_CHOICES, default='sales')
    # Dynamic field
    pipeline_type_ref = models.ForeignKey(
        PipelineType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='stages',
        help_text="Dynamic pipeline type"
    )
    opportunity_stage_name = models.CharField(max_length=100)
    stage_description = models.TextField(blank=True, help_text="Description of the pipeline stage")
    order = models.IntegerField(default=0)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Default probability (0-100)")
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return self.opportunity_stage_name

class Opportunity(TenantModel, TimeStampedModel):
    opportunity_name = models.CharField(max_length=255)
    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opportunities')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    stage = models.ForeignKey(OpportunityStage, on_delete=models.PROTECT, related_name='opportunities')
    close_date = models.DateField()
    expected_closing_date = models.DateField(null=True, blank=True, help_text="Expected closing date for more accurate forecasting")
    probability = models.FloatField(default=0.0)  # 0.0–1.0
    
    # Sales cycle tracking
    sales_cycle_length = models.PositiveIntegerField(null=True, blank=True, help_text="Length of the sales cycle in days")
    
    # Deal categorization
    deal_size_category = models.CharField(
        max_length=20,
        choices=DEAL_SIZE_CATEGORIES,
        default='medium',
        help_text="Size category of the deal (small, medium, large, enterprise) (legacy field)"
    )
    # New dynamic field
    deal_size_category_ref = models.ForeignKey(
        DealSizeCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='opportunities',
        help_text="Dynamic deal size category (replaces deal_size_category field)"
    )
    
    # Financial tracking
    customer_acquisition_cost = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Customer acquisition cost for this opportunity"
    )
    expected_clv = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Expected customer lifetime value"
    )
    
    # ESG
    esg_tagged = models.BooleanField(default=False)
    esg_impact_description = models.TextField(blank=True)
    
    # Products
    products = models.ManyToManyField('products.Product', through='OpportunityProduct')
    
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


    objects = VisibilityAwareManager()

    @property
    def weighted_value(self):
        return float(self.amount) * self.probability

    @property
    def probability_adjusted_value(self):
        """
        Calculate the probability adjusted value that factors in probability and time value.
        If expected_closing_date is provided, we can factor in time value considerations.
        For now, we'll implement a basic version that multiplies amount by probability.
        """
        if self.expected_closing_date:
            # Calculate time factor based on expected closing date
            from datetime import date
            today = date.today()
            days_to_close = (self.expected_closing_date - today).days
            
            # Time value factor: closer opportunities have higher value
            # Using a simple linear decay factor where opportunities further in the future
            # have reduced probability-adjusted value
            time_factor = 1.0
            if days_to_close > 90:  # More than 3 months out
                time_factor = 0.9
            elif days_to_close > 180:  # More than 6 months out
                time_factor = 0.8
            elif days_to_close > 365:  # More than a year out
                time_factor = 0.7
            
            return float(self.amount) * self.probability * time_factor
        else:
            # If no expected closing date, just use probability
            return float(self.amount) * self.probability

    @property
    def roi_potential(self):
        """
        Calculate potential return on investment.
        ROI = (Expected CLV - CAC) / CAC
        Returns None if CAC is 0 or None to avoid division by zero.
        """
        if not self.customer_acquisition_cost or self.customer_acquisition_cost == 0:
            return None
        
        if self.expected_clv is not None:
            roi = (float(self.expected_clv) - float(self.customer_acquisition_cost)) / float(self.customer_acquisition_cost)
            return roi
        else:
            return None

    def __str__(self):
        return f"{self.opportunity_name} ({self.account.email})"

    def calculate_sales_velocity(self):
        """
        Calculate sales velocity: opportunities moved per day/time period
        """
        from datetime import date, timedelta
        from django.utils import timezone
        
        # Calculate how long this opportunity has been in the system
        if self.created_at:
            days_open = (timezone.now().date() - self.created_at.date()).days
        else:
            days_open = 1 # Default to 1 day if no creation date
        
        if days_open <= 0:
            days_open = 1  # Avoid division by zero or negative values
        
        # Sales velocity could be calculated as the value moved per day
        # We'll calculate it as the weighted value per day the opportunity has been open
        velocity = self.weighted_value / days_open
        
        return velocity

    def calculate_conversion_rate(self, tenant_id=None):
        """
        Track opportunity conversion rates
        """
        from django.db.models import Count
        
        # Count all opportunities for the tenant
        all_opps_query = Opportunity.objects.all()
        if tenant_id:
            all_opps_query = all_opps_query.filter(tenant_id=tenant_id)
        else:
            all_opps_query = all_opps_query.filter(tenant_id=self.tenant_id)
        
        total_opportunities = all_opps_query.count()
        
        # Count won opportunities
        won_opps_query = all_opps_query.filter(stage__is_won=True)
        won_opportunities = won_opps_query.count()
        
        if total_opportunities == 0:
            return 0  # Avoid division by zero
        
        conversion_rate = (won_opportunities / total_opportunities) * 100
        return conversion_rate

    def calculate_average_sales_cycle(self, tenant_id=None):
        """
        Calculate average time to close deals
        """
        from django.db.models import Avg
        from datetime import date
        
        # Calculate average days to close for won opportunities
        # We'll use WinLossAnalysis if available, otherwise estimate from close_date
        if self.stage.is_won and self.close_date:
            # Calculate days from creation to close date
            if self.created_at:
                days_to_close = (self.close_date - self.created_at.date()).days
                return days_to_close
            else:
                return 0
        
        # If not won yet, return estimated days based on current stage and probability
        if self.created_at:
            days_open = (date.today() - self.created_at.date()).days
            # Estimate based on current probability
            estimated_days = days_open / max(self.probability, 0.01) if self.probability > 0 else days_open * 10
            return estimated_days
        else:
            return 0

    def calculate_pipeline_velocity(self, start_date=None, end_date=None, tenant_id=None):
        """
        Calculate the speed of opportunities moving through pipeline
        """
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        # Calculate pipeline velocity as total weighted value moved per time period
        queryset = Opportunity.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        else:
            queryset = queryset.filter(tenant_id=self.tenant_id)
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Calculate total weighted value of opportunities in the period
        total_weighted_value = sum(opp.weighted_value for opp in queryset)
        
        # Calculate time period in days
        if start_date and end_date:
            days_period = (end_date - start_date).days
            if days_period <= 0:
                days_period = 1
        else:
            days_period = 30 # Default to 30 days if no dates specified
        
        # Calculate velocity as value per day
        velocity = total_weighted_value / days_period
        return velocity

    def get_sales_velocity_trend(self, months=6, tenant_id=None):
        """
        Track sales velocity over time
        """
        from django.utils import timezone
        from datetime import datetime, timedelta
        import calendar
        
        velocity_trends = []
        today = timezone.now().date()
        
        for i in range(months):
            # Calculate date range for this month
            end_date = today - timedelta(days=i*30)
            start_date = end_date - timedelta(days=30)
            
            # Get opportunities for this month
            opps_for_period = Opportunity.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            
            if tenant_id:
                opps_for_period = opps_for_period.filter(tenant_id=tenant_id)
            else:
                opps_for_period = opps_for_period.filter(tenant_id=self.tenant_id)
            
            # Calculate total weighted value for this period
            total_weighted_value = sum(opp.weighted_value for opp in opps_for_period)
            
            # Calculate velocity (value per day)
            days_in_period = 30
            if total_weighted_value > 0:
                velocity = total_weighted_value / days_in_period
            else:
                velocity = 0
            
            velocity_trends.append({
                'month': start_date.strftime('%Y-%m'),
                'velocity': velocity,
                'total_value': total_weighted_value,
                'opportunity_count': opps_for_period.count(),
                'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            })
        
        # Reverse to show most recent first
        return list(reversed(velocity_trends))

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
                'name': self.opportunity_name,
                'amount': float(self.amount),
                'stage': self.stage.opportunity_stage_name,
                'owner_id': self.owner_id if self.owner else None,
                'tenant_id': self.tenant_id
            })
            
        # Check for stage changes
        if old_stage and old_stage != self.stage:
            emit_event('opportunities.stage_changed', {
                'opportunity_id': self.id,
                'old_stage': old_stage.opportunity_stage_name,
                'new_stage': self.stage.opportunity_stage_name,
                'tenant_id': self.tenant_id
            })
            
            if self.stage.is_won and not old_stage.is_won:
                emit_event('opportunities.won', {
                    'opportunity_id': self.id,
                    'amount': float(self.amount),
                    'name': self.opportunity_name,
                    'owner_id': self.owner_id if self.owner else None,
                    'tenant_id': self.tenant_id
                })
            elif self.stage.is_lost and not old_stage.is_lost:
                emit_event('opportunities.lost', {
                    'opportunity_id': self.id,
                    'amount': float(self.amount),
                    'name': self.opportunity_name,
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
        return f"{self.quantity}x {self.product.name} in {self.opportunity.opportunity_name}"


class ForecastSnapshot(TenantModel):
    """
    Daily snapshot of sales forecast for reporting.
    """
    date = models.DateField()
    total_pipeline_value = models.DecimalField(max_digits=16, decimal_places=2)
    weighted_forecast = models.DecimalField(max_digits=16, decimal_places=2)
    class Meta:
        unique_together = [('date', 'tenant')]


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
        choices=DEAL_SIZE_CATEGORIES,
        default='medium'
    )
    # New dynamic field
    deal_size_category_ref = models.ForeignKey(
        DealSizeCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='win_loss_analyses',
        help_text="Dynamic deal size category (replaces deal_size_category field)"
    )

    def __str__(self):
        return f"{'Won' if self.is_won else 'Lost'}: {self.opportunity.opportunity_name}"

class AssignmentRule(TenantModel):
    """
    Assignment rules specifically for Opportunities.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="opportunity_assignment_rules"
    )
    RULE_TYPE_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('territory', 'Territory-Based'),
        ('load_balanced', 'Load Balanced'),
        ('criteria', 'Criteria-Based'),
    ]

    assignment_rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    # Dynamic field reference
    rule_type_ref = models.ForeignKey(
        AssignmentRuleType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='opportunity_assignment_rules',
        help_text="Dynamic rule type (replaces rule_type field)"
    )
    criteria = models.JSONField(default=dict, blank=True, help_text="Matching criteria, e.g., {'stage': 'negotiation', 'value_gt': 10000}")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunity_assigned_rules')
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    priority = models.IntegerField(default=1, help_text="Priority of the rule (lower numbers = higher priority)")

    def __str__(self):
        return self.assignment_rule_name
