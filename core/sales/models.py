from django.db import models
<<<<<<< Updated upstream
from accounts.models import Account
from products.models import Product


SALE_TYPE_CHOICES = [
    ('hardware', 'Hardware Installation'),
    ('ship', 'Product Shipment'),
    ('software', 'Software License'),
]
=======
from core.models import User as Account
from settings_app.models import Territory, TeamMember
from django.db.models import Sum, Count, Avg
>>>>>>> Stashed changes



class CommissionRule(models.Model):
    """
    Rules for calculating sales commissions.
    """
    name = models.CharField(max_length=255)
    product_type = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Apply to all products of this type (matches pricing_model)"
    )
    specific_product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sales_commission_rules',
        help_text="Apply to specific product (overrides type)"
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.0, 
        help_text="Commission percentage (e.g. 10.0 for 10%)"
    )
    flat_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0, 
        help_text="Flat commission amount"
    )
    min_sales_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0, 
        help_text="Minimum sale amount required"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def applies_to_product(self, product):
        """Check if this rule applies to a given product."""
        if self.specific_product_id:
            return self.specific_product_id == product.id
        if self.product_type:
            return product.pricing_model == self.product_type
        return True


class Sale(models.Model):
    """
    Represents a completed sale transaction.
    """
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='sales'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sales'
    )
    sales_rep = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales_made',
        help_text="User credited with this sale"
    )
    sale_type = models.CharField(max_length=20, choices=SALE_TYPE_CHOICES, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product.name} for {self.account.name}"
    
    def calculate_commission(self, sales_rep=None):
        """
        Calculate commission for this sale.
        Returns the commission amount and the applied rule.
        """
        from django.utils import timezone
        
        sales_rep = sales_rep or self.sales_rep
        if not sales_rep:
            return 0, None
        
        today = timezone.now().date()
        
        rules = CommissionRule.objects.filter(
            is_active=True,
            start_date__lte=today,
        ).filter(
            models.Q(end_date__gte=today) | models.Q(end_date__isnull=True)
        ).filter(
            min_sales_amount__lte=self.amount
        ).order_by('-min_sales_amount')
        
        for rule in rules:
            if rule.applies_to_product(self.product):
                percentage_amount = (self.amount * rule.percentage / 100)
                total_commission = percentage_amount + rule.flat_amount
                return total_commission, rule
        
        return 0, None


class Commission(models.Model):
    """
    Recorded commission for a sale.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='commissions')
    sales_rep = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='commissions')
    rule_applied = models.ForeignKey(CommissionRule, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_earned = models.DateTimeField(auto_now_add=True)
    date_paid = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.sales_rep.email} - {self.amount} ({self.status})"
<<<<<<< Updated upstream
    
    @classmethod
    def create_from_sale(cls, sale, sales_rep=None):
        """
        Create a commission record from a sale.
        """
        sales_rep = sales_rep or sale.sales_rep
        if not sales_rep:
            return None
        
        amount, rule = sale.calculate_commission(sales_rep)
        
        if amount <= 0:
            return None
        
        return cls.objects.create(
            sale=sale,
            sales_rep=sales_rep,
            rule_applied=rule,
            amount=amount,
            status='pending',
        )
=======


class TerritoryPerformance(models.Model):
    """
    Model to track performance metrics for territories
    """
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='performance_metrics')
    period_start = models.DateField(help_text="Start date of the performance period")
    period_end = models.DateField(help_text="End date of the performance period")
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Total revenue generated in this territory")
    total_deals = models.IntegerField(default=0, help_text="Total number of deals closed in this territory")
    average_deal_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Average deal size in this territory")
    
    # Conversion metrics
    total_leads = models.IntegerField(default=0, help_text="Total leads in this territory")
    qualified_leads = models.IntegerField(default=0, help_text="Number of qualified leads in this territory")
    converted_leads = models.IntegerField(default=0, help_text="Number of converted leads in this territory")
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Lead to opportunity conversion rate (%)")
    
    # Opportunity metrics
    total_opportunities = models.IntegerField(default=0, help_text="Total opportunities in this territory")
    won_opportunities = models.IntegerField(default=0, help_text="Number of won opportunities in this territory")
    lost_opportunities = models.IntegerField(default=0, help_text="Number of lost opportunities in this territory")
    opportunity_win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Opportunity win rate (%)")
    
    # Team metrics
    team_member_count = models.IntegerField(default=0, help_text="Number of team members in this territory")
    active_sales_reps = models.IntegerField(default=0, help_text="Number of active sales representatives in this territory")
    
    # Performance indicators
    territory_quota = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Territory quota for the period")
    quota_attainment = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage of quota attainment (%)")
    
    # Date tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['territory', 'period_start', 'period_end']
        ordering = ['-period_end', 'territory__label']
    
    def __str__(self):
        return f"{self.territory.label} Performance ({self.period_start} to {self.period_end})"
    
    def calculate_metrics(self):
        """
        Calculate and update all territory performance metrics
        """
        # Calculate based on sales reps in this territory
        team_members_in_territory = TeamMember.objects.filter(territory_ref=self.territory)
        sales_reps = [tm.user for tm in team_members_in_territory if tm.role_ref and tm.role_ref.role_name in ['sales_rep', 'sales_manager']]
        
        # Calculate revenue and deals from sales by reps in this territory
        sales_in_territory = Sale.objects.filter(
            sales_rep__in=sales_reps,
            sale_date__date__gte=self.period_start,
            sale_date__date__lte=self.period_end
        )
        
        # Financial metrics
        revenue_data = sales_in_territory.aggregate(
            total_revenue=Sum('amount'),
            total_deals=Count('id'),
            avg_deal_size=Avg('amount')
        )
        
        self.total_revenue = revenue_data['total_revenue'] or 0
        self.total_deals = revenue_data['total_deals'] or 0
        self.average_deal_size = revenue_data['avg_deal_size'] or 0
        
        # Calculate conversion metrics (would need to integrate with leads/opportunities)
        # This is a simplified version - in a real implementation, you'd need to connect to leads and opportunities
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        leads_in_territory = Lead.objects.filter(
            owner__in=sales_reps,
            created_at__date__gte=self.period_start,
            created_at__date__lte=self.period_end
        )
        
        self.total_leads = leads_in_territory.count()
        self.qualified_leads = leads_in_territory.filter(status='qualified').count()
        self.converted_leads = leads_in_territory.filter(status='converted').count()
        
        if self.total_leads > 0:
            self.conversion_rate = (self.converted_leads / self.total_leads) * 100
        else:
            self.conversion_rate = 0.0
        
        # Opportunity metrics
        opportunities_in_territory = Opportunity.objects.filter(
            owner__in=sales_reps,
            created_at__date__gte=self.period_start,
            created_at__date__lte=self.period_end
        )
        
        self.total_opportunities = opportunities_in_territory.count()
        self.won_opportunities = opportunities_in_territory.filter(stage__is_won_stage=True).count()
        self.lost_opportunities = opportunities_in_territory.filter(stage__is_lost_stage=True).count()
        
        if self.total_opportunities > 0:
            self.opportunity_win_rate = (self.won_opportunities / self.total_opportunities) * 100
        else:
            self.opportunity_win_rate = 0.00
        
        # Team metrics
        self.team_member_count = team_members_in_territory.count()
        self.active_sales_reps = len(sales_reps)
        
        # Quota attainment (if territory has a quota set)
        # This would typically be set separately, for now using a default
        if self.territory_quota > 0:
            self.quota_attainment = (self.total_revenue / self.territory_quota) * 100
        else:
            self.quota_attainment = 0.00


class TerritoryAssignmentOptimizer(models.Model):
    """
    Model to store territory assignment optimization data and logic
    """
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='assignment_optimizations')
    optimization_date = models.DateTimeField(auto_now_add=True)
    optimization_type = models.CharField(max_length=50, choices=[
        ('load_balancing', 'Load Balancing'),
        ('performance_based', 'Performance Based'),
        ('geographic', 'Geographic'),
        ('capacity_based', 'Capacity Based'),
    ], default='load_balancing')
    
    # Optimization parameters
    current_load = models.IntegerField(default=0, help_text="Current workload in the territory")
    optimal_load = models.IntegerField(default=0, help_text="Optimal workload for the territory")
    load_balance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Score representing how balanced the load is (0-100)")
    
    # Performance metrics used for optimization
    territory_performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Overall performance score (0-100)")
    resource_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Resource utilization percentage (0-100)")
    
    # Recommendations
    recommended_team_size = models.IntegerField(default=0, help_text="Recommended team size for this territory")
    recommended_adjustments = models.TextField(blank=True, help_text="Text description of recommended adjustments")
    
    # Status and results
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    execution_time = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Time taken to run optimization in seconds")
    
    class Meta:
        ordering = ['-optimization_date']
    
    def __str__(self):
        return f"{self.territory.label} Optimization ({self.optimization_type}) - {self.optimization_date}"
    
    def run_optimization(self):
        """
        Run the territory assignment optimization algorithm
        """
        from core.models import User
        from settings_app.models import TeamMember
        
        # Get all team members in this territory
        team_members = TeamMember.objects.filter(territory_ref=self.territory)
        
        # Calculate current performance metrics
        self.current_load = team_members.count()
        
        # Calculate performance based on territory performance
        try:
            latest_performance = self.territory.performance_metrics.latest('period_end')
            self.territory_performance_score = latest_performance.opportunity_win_rate  # Use win rate as performance indicator
        except TerritoryPerformance.DoesNotExist:
            self.territory_performance_score = 50.00  # Default score if no performance data
        
        # Calculate optimal team size based on territory size and performance
        # This is a simplified algorithm - in practice, this would be more complex
        if self.territory_performance_score >= 70:
            # High performing territory might need more resources for growth
            self.recommended_team_size = self.current_load + 1
        elif self.territory_performance_score >= 50:
            # Average performing territory - maintain current size
            self.recommended_team_size = self.current_load
        else:
            # Low performing territory - might need restructuring
            self.recommended_team_size = max(1, self.current_load - 1)
        
        # Calculate load balance score (simplified)
        if self.current_load > 0:
            # For now, just use the performance score as a proxy for load balance
            self.load_balance_score = self.territory_performance_score
        else:
            self.load_balance_score = 0.00
        
        # Calculate resource utilization
        if self.recommended_team_size > 0:
            self.resource_utilization = (self.current_load / self.recommended_team_size) * 100
        else:
            self.resource_utilization = 0.00
        
        # Generate recommendations
        if self.current_load < self.recommended_team_size:
            self.recommended_adjustments = f"Consider adding {self.recommended_team_size - self.current_load} more team members to optimize performance."
        elif self.current_load > self.recommended_team_size:
            self.recommended_adjustments = f"Consider reducing team size by {self.current_load - self.recommended_team_size} members or redistributing to other territories."
        else:
            self.recommended_adjustments = "Current team size is optimal for this territory."
        
        self.status = 'completed'
        self.save()


# Extend the existing TeamMember model with territory performance metrics
# We'll add methods to the TeamMember model via a related model
class TeamMemberTerritoryMetrics(models.Model):
    """
    Model to track territory-specific metrics for team members
    """
    team_member = models.OneToOneField('settings_app.TeamMember', on_delete=models.CASCADE, related_name='territory_metrics')
    
    # Individual territory performance
    personal_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Personal revenue generated in assigned territory")
    personal_deals = models.IntegerField(default=0, help_text="Number of deals closed personally")
    personal_quota = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Personal quota for the territory")
    quota_attainment = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Personal quota attainment (%)")
    
    # Territory contribution metrics
    territory_revenue_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Contribution to overall territory revenue")
    territory_performance_rank = models.IntegerField(default=0, help_text="Rank within territory (1 is best performer)")
    
    # Efficiency metrics
    leads_handled = models.IntegerField(default=0, help_text="Number of leads handled in territory")
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Personal conversion rate (%)")
    avg_sales_cycle = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Average sales cycle in days")
    
    # Territory utilization
    territory_capacity_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Utilization of territory capacity (%)")
    
    # Performance indicators
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Overall performance score (0-100)")
    
    # Date tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.team_member.user.email} Territory Metrics"
    
    def calculate_metrics(self):
        """
        Calculate and update all territory metrics for this team member
        """
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        # Calculate metrics based on the team member's sales
        sales_by_member = Sale.objects.filter(
            sales_rep=self.team_member.user,
            sale_date__date__gte=self.team_member.hire_date or '190-01-01'
        )
        
        # Personal revenue and deals
        sales_data = sales_by_member.aggregate(
            total_revenue=Sum('amount'),
            total_deals=Count('id')
        )
        
        self.personal_revenue = sales_data['total_revenue'] or 0
        self.personal_deals = sales_data['total_deals'] or 0
        
        # Personal quota attainment
        if self.personal_quota > 0:
            self.quota_attainment = (self.personal_revenue / self.personal_quota) * 10
        else:
            self.quota_attainment = 0.00
        
        # Territory contribution - calculate percentage of territory's total revenue
        if self.team_member.territory_ref:
            try:
                territory_total = self.team_member.territory_ref.performance_metrics.latest('period_end').total_revenue
                if territory_total > 0:
                    self.territory_revenue_contribution = (self.personal_revenue / territory_total) * 10
                else:
                    self.territory_revenue_contribution = 0.00
            except TerritoryPerformance.DoesNotExist:
                self.territory_revenue_contribution = 0.00
        
        # Lead handling metrics
        leads_by_member = Lead.objects.filter(owner=self.team_member.user)
        self.leads_handled = leads_by_member.count()
        
        converted_leads = leads_by_member.filter(status='converted').count()
        if self.leads_handled > 0:
            self.conversion_rate = (converted_leads / self.leads_handled) * 100
        else:
            self.conversion_rate = 0.00
        
        # Calculate average sales cycle for won opportunities
        won_opportunities = Opportunity.objects.filter(
            owner=self.team_member.user,
            stage__is_won_stage=True
        )
        
        total_days = 0
        count = 0
        for opp in won_opportunities:
            if opp.created_at and opp.closed_date:
                days = (opp.closed_date - opp.created_at.date()).days
                total_days += days
                count += 1
        
        if count > 0:
            self.avg_sales_cycle = total_days / count
        else:
            self.avg_sales_cycle = 0.00
        
        # Calculate performance score based on multiple factors
        # Weighted average of different metrics
        revenue_weight = 0.3
        conversion_weight = 0.25
        quota_weight = 0.25
        deals_weight = 0.2
        
        # Normalize values to 0-100 scale
        revenue_score = min(100, (self.personal_revenue / 10000) * 10) if self.personal_revenue else 0  # Assuming $10k avg as 100%
        conversion_score = self.conversion_rate
        quota_score = min(100, self.quota_attainment)
        deals_score = min(100, (self.personal_deals / 10) * 20) if self.personal_deals else 0 # Assuming 10 deals avg as 100%
        
        self.performance_score = (
            revenue_score * revenue_weight +
            conversion_score * conversion_weight +
            quota_score * quota_weight +
            deals_score * deals_weight
        )
        
        # Calculate territory performance rank (would need to compare with other members in same territory)
        # This is a simplified version - in practice, you'd need to compare with all members in the same territory
        self.territory_performance_rank = 1  # Placeholder, would need actual ranking logic
        
        # Calculate territory capacity utilization
        # This would depend on the territory's total capacity vs individual contribution
        self.territory_capacity_utilization = self.territory_revenue_contribution
        
        self.save()
>>>>>>> Stashed changes
