from django.db import models
from tenants.models import TenantAwareModel as TenantModel

class CampaignAttribution(TenantModel):
    """
    Links Campaigns to Business Outcomes (Leads, Opportunities) to track ROI.
    """
    ATTRIBUTION_MODEL_CHOICES = [
        ('first_touch', 'First Touch'),
        ('last_touch', 'Last Touch'),
        ('linear', 'Linear'),
        ('time_decay', 'Time Decay'),
        ('u_shaped', 'U-Shaped'),
    ]

    campaign = models.ForeignKey(
        'marketing.Campaign', 
        on_delete=models.CASCADE, 
        related_name='attributions'
    )
    
    # Linked Outcomes (One is required)
    lead = models.ForeignKey(
        'leads.Lead', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='campaign_attributions'
    )
    opportunity = models.ForeignKey(
        'opportunities.Opportunity', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='campaign_attributions'
    )
    
    touchpoint_date = models.DateTimeField(help_text="When the interaction occurred")
    weight = models.FloatField(default=1.0, help_text="Attribution weight (0.0 - 1.0)")
    attribution_model = models.CharField(max_length=50, choices=ATTRIBUTION_MODEL_CHOICES, default='first_touch')
    
    revenue_share = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        default=0.00, 
        help_text="Calculated revenue share based on weight and opportunity value"
    )
    
    attribution_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Campaign Attribution"
        verbose_name_plural = "Campaign Attributions"
        indexes = [
            models.Index(fields=['tenant', 'campaign']),
            models.Index(fields=['tenant', 'lead']),
            models.Index(fields=['tenant', 'opportunity']),
        ]

    def __str__(self):
        outcome = self.opportunity or self.lead
        return f"{self.campaign.campaign_name} -> {outcome} ({self.weight})"
