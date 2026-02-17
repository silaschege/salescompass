import os
import django
import sys
import logging
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from tenants.models import Tenant
from core.models import User
from marketing.models import Campaign
from leads.models import Lead
from opportunities.models import Opportunity, OpportunityStage
from marketing.services import AttributionService
from marketing.models_attribution import CampaignAttribution

def verify():
    print("Starting Attribution Verification...")
    
    # 1. Setup Data
    try:
        tenant, _ = Tenant.objects.get_or_create(
            name="Attribution Tenant", 
            defaults={'subdomain': 'attr-test', 'slug': 'attr-test'}
        )
        
        user, _ = User.objects.get_or_create(username="marketer", tenant=tenant)
        
        # Create Stage
        stage, _ = OpportunityStage.objects.get_or_create(
            opportunity_stage_name="closed_won",
            tenant=tenant,
            defaults={'is_won': True, 'order': 100}
        )
        
        # Create Campaign
        campaign = Campaign.objects.create(
            campaign_name="Summer Sale 2025",
            tenant=tenant,
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() + timedelta(days=30),
            budget=1000.00,
            actual_cost=500.00
        )
        print(f"Created Campaign: {campaign.campaign_name}")
        
        # Create Lead linked to Campaign AND same account as Opp
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            tenant=tenant,
            campaign_ref=campaign,
            lead_acquisition_date=timezone.now() - timedelta(days=10),
            account=user, # Link to same account as Opportunity
        )
        print(f"Created Lead: {lead.email} linked to {lead.campaign_ref.campaign_name}")
        
        # Create Opportunity (Closed Won)
        opportunity = Opportunity.objects.create(
            opportunity_name="Big Deal",
            tenant=tenant,
            amount=10000.00,
            close_date=timezone.now() + timedelta(days=30),
            account=user,
            stage=stage,
        )
        
        print(f"Created Opportunity: {opportunity.opportunity_name} Amount: {opportunity.amount}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error setting up data: {e}")
        return

    # 2. Run Attribution
    try:
        print("\nCalculating Attribution (First Touch)...")
        AttributionService.calculate_attribution_for_opportunity(opportunity, model='first_touch', tenant_id=tenant.id)
        
        # Verify
        attributions = CampaignAttribution.objects.filter(opportunity=opportunity)
        if attributions.count() == 1:
            attr = attributions.first()
            if attr.campaign == campaign and attr.revenue_share == 10000.00:
                 print(f"PASS: Attribution created correctly. Revenue Share: {attr.revenue_share}")
            else:
                 print(f"FAIL: Attribution incorrect. Campaign: {attr.campaign}, Revenue: {attr.revenue_share}")
        else:
             print(f"FAIL: No attribution created. Count: {attributions.count()}")
             
    except Exception as e:
        print(f"Error executing attribution: {e}")

    # 3. Test View Logic (Simulation)
    try:
        print("\nVerifying View Logic...")
        # Re-calc campaign stats
        attr_revenue = CampaignAttribution.objects.filter(campaign=campaign).aggregate(django.db.models.Sum('revenue_share'))['revenue_share__sum']
        roi = ((float(attr_revenue or 0) - float(campaign.actual_cost)) / float(campaign.actual_cost)) * 100
        print(f"Calculated ROI: {roi}%")
        
        if roi > 0:
            print("PASS: ROI calculation is positive.")
        else:
            print("FAIL: ROI calculation expected positive.")
            
    except Exception as e:
        print(f"Error verifying view logic: {e}")

if __name__ == '__main__':
    verify()
