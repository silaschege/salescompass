import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass')
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.utils import timezone
from opportunities.models import Opportunity, OpportunityStage
from tenants.models import Tenant
from core.models import User
from accounts.models import Account

def run_verification():
    print("Setting up revenue verification data...")
    
    # 1. Setup Tenant and User
    tenant, _ = Tenant.objects.get_or_create(name="Revenue Test Tenant", subdomain="revtest")
    user, _ = User.objects.get_or_create(username="rev_forecast_user", email="rev@example.com", tenant=tenant)
    
    # 2. Setup Stages
    # Open Stage
    open_stage, _ = OpportunityStage.objects.get_or_create(
        opportunity_stage_name="Revenue Negotiation", 
        tenant=tenant, 
        defaults={'is_won': False, 'is_lost': False, 'probability': 0.60}
    )
    
    # Won Stage (should be excluded)
    won_stage, _ = OpportunityStage.objects.get_or_create(
        opportunity_stage_name="Revenue Won", 
        tenant=tenant, 
        defaults={'is_won': True}
    )
    
    # 3. Create Opportunities
    # Open Opp 1: $1000 @ 50% (Explicit probability)
    Opportunity.objects.create(
        opportunity_name="Open Deal 1",
        amount=Decimal('1000.00'),
        owner=user,
        stage=open_stage,
        close_date=timezone.now().date(),
        tenant=tenant,
        probability=Decimal('0.50'),
        account=user
    )
    
    # Open Opp 2: $2000 @ 60% (Implicit/Default probability from stage? No, model defaults 0.0, we set 0.8)
    Opportunity.objects.create(
        opportunity_name="Open Deal 2",
        amount=Decimal('2000.00'),
        owner=user,
        stage=open_stage,
        close_date=timezone.now().date(),
        tenant=tenant,
        probability=Decimal('0.80'),
        account=user
    )
    
    # Won Opp: $5000 (Should be excluded)
    Opportunity.objects.create(
        opportunity_name="Won Deal",
        amount=Decimal('5000.00'),
        owner=user,
        stage=won_stage,
        close_date=timezone.now().date(),
        tenant=tenant,
        probability=Decimal('1.00'),
        account=user
    )

    print("Data setup complete. Calling calculate_weighted_forecast...")
    
    from opportunities.utils import calculate_weighted_forecast
    
    # Filter by tenant to isolate our test data
    result = calculate_weighted_forecast(tenant_id=tenant.id)
    print(f"Result: {result}")
    
    # Expected: 
    # Pipeline: 1000 + 2000 = 3000
    # Weighted: (1000 * 0.5) + (2000 * 0.8) = 500 + 1600 = 2100
    
    expected_pipeline = Decimal('3000.00')
    expected_weighted = Decimal('2100.00')
    
    assert result['total_pipeline'] == expected_pipeline, f"Expected pipeline {expected_pipeline}, got {result['total_pipeline']}"
    assert result['weighted_forecast'] == expected_weighted, f"Expected weighted {expected_weighted}, got {result['weighted_forecast']}"
    
    print("Revenue Forecast Verification SUCCESS!")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
