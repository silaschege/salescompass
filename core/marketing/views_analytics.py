from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, F
from .models import Campaign
from .models_attribution import CampaignAttribution

class CampaignPerformanceView(LoginRequiredMixin, TemplateView):
    template_name = 'marketing/campaign_performance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Date filtering (default 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get active campaigns
        campaigns = Campaign.objects.filter(tenant=tenant)
        
        performance_data = []
        labels = []
        revenue_data = []
        cost_data = []
        roi_data = []
        
        for campaign in campaigns:
            # 1. Cost
            cost = campaign.calculate_total_marketing_spend(start_date, end_date, tenant.id)
            
            # 2. Revenue (from Attribution)
            # Find attributions created in this period, OR linked to opps closed in this period?
            # Usually we track revenue when it happens (touchpoint might be older)
            # But let's look at attributions created (or opp closed date)
            
            attributed_revenue = CampaignAttribution.objects.filter(
                campaign=campaign,
                opportunity__created_at__gte=start_date, # Or close date?
                opportunity__created_at__lte=end_date
            ).aggregate(total=Sum('revenue_share'))['total'] or 0.0
            
            attributed_revenue = float(attributed_revenue)
            cost = float(cost)
            
            # 3. ROI
            roi = 0.0
            if cost > 0:
                roi = ((attributed_revenue - cost) / cost) * 100
                
            performance_data.append({
                'name': campaign.campaign_name,
                'cost': cost,
                'revenue': attributed_revenue,
                'roi': roi,
                'leads': campaign.leads.count(), # Uses the new related_name
                'conversions': campaign.attributions.filter(opportunity__isnull=False).count()
            })
            
            labels.append(campaign.campaign_name)
            revenue_data.append(attributed_revenue)
            cost_data.append(cost)
            roi_data.append(roi)
            
        context['performance_data'] = performance_data
        context['chart_labels'] = labels
        context['chart_revenue'] = revenue_data
        context['chart_roi'] = roi_data
        
        return context
