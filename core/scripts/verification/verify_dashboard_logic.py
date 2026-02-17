import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass')
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.test import RequestFactory
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from opportunities.models import Opportunity, ForecastSnapshot, OpportunityStage
from opportunities.views import RevenueForecastView

def verify_dashboard():
    print("Setting up Dashboard Verification Data...")
    
    # 1. Setup Tenant/User
    tenant, _ = Tenant.objects.get_or_create(name="Dashboard Test Tenant", subdomain="dashtest")
    user, _ = User.objects.get_or_create(username="dash_user", email="dash@example.com", tenant=tenant)
    
    # 2. Create Historical Snapshot (30 days ago) for Accuracy
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    ForecastSnapshot.objects.create(
        tenant=tenant,
        date=thirty_days_ago,
        total_pipeline_value=Decimal('10000.00'),
        weighted_forecast=Decimal('5000.00') # Forecast was $5000
    )
    
    # 3. Create Recent Snapshot (Yesterday) for Alert (Dropdown)
    yesterday = timezone.now().date() - timedelta(days=1)
    ForecastSnapshot.objects.create(
        tenant=tenant,
        date=yesterday,
        total_pipeline_value=Decimal('10000.00'),
        weighted_forecast=Decimal('8000.00') # Yesterday was high
    )
    
    # 4. Create Current Opportunities (Low value -> Trigger Alert)
    # Today's forecast will be low compared to yesterday's 8000
    stage, _ = OpportunityStage.objects.get_or_create(
        opportunity_stage_name="Dash Open", 
        tenant=tenant,
        defaults={'is_won': False, 'probability': 0.5}
    )
    
    Opportunity.objects.create(
        opportunity_name="Low Value Deal",
        amount=Decimal('1000.00'), # Weighted = 500
        owner=user,
        stage=stage,
        tenant=tenant,
        close_date=timezone.now().date(),
        account=user
    )
    
    # 5. Create "Actual" Revenue (Won Deal) for Accuracy
    # Forecast was 5000. Let's make Actual 4000 (80% accuracy roughly)
    won_stage, _ = OpportunityStage.objects.get_or_create(
        opportunity_stage_name="Dash Won", 
        tenant=tenant,
        defaults={'is_won': True}
    )
    
    Opportunity.objects.create(
        opportunity_name="Won Deal Actual",
        amount=Decimal('4000.00'),
        owner=user,
        stage=won_stage,
        tenant=tenant,
        close_date=timezone.now().date(),
        account=user
    )

    print("Data Setup Complete. Running View...")
    
    factory = RequestFactory()
    request = factory.get('/opportunities/forecast/')
    request.user = user
    
    view = RevenueForecastView()
    view.setup(request)
    
    context = view.get_context_data()
    
    # Check Accuracy
    acc = context['accuracy_metrics']
    print(f"Accuracy Metrics: {acc}")
    # Forecast: 5000, Actual: 4000. Error: 1000. Error%: 0.25. Accuracy: 75%
    assert acc['accuracy_percentage'] == 75.0, f"Expected 75.0% accuracy, got {acc['accuracy_percentage']}%"
    
    # Check Alerts
    # Yesterday: 8000. Today: 500. Drop: (500-8000)/8000 = -93%
    alerts = context['forecast_alerts']
    print(f"Alerts: {alerts}")
    assert len(alerts) > 0, "Expected alerts due to drop"
    assert "dropped" in alerts[0], "Expected impact alert"
    
    print("Dashboard Verification SUCCESS!")

if __name__ == "__main__":
    try:
        verify_dashboard()
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
