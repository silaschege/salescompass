import os
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salescompass.settings")
django.setup()

from django.contrib.auth import get_user_model
from commissions.models import CommissionPlan, CommissionRule, UserCommissionPlan, Commission, CommissionPayment
from opportunities.models import Opportunity, OpportunityStage
from commissions.utils import calculate_commission, calculate_forecast, generate_payment_records
from tenants.models import Tenant

User = get_user_model()

def run_verification():
    print("Setting up verification data...")
    
    # 1. Setup User and Tenant
    tenant, _ = Tenant.objects.get_or_create(name="Test Tenant", subdomain="test")
    user, _ = User.objects.get_or_create(email="commission_test@example.com", defaults={'username': 'comm_test', 'tenant': tenant})
    
    # 2. Setup Commission Plan
    plan, _ = CommissionPlan.objects.get_or_create(
        commission_plan_name="Standard Plan",
        tenant=tenant,
        defaults={'basis': 'revenue', 'period': 'monthly'}
    )
    
    # 3. Setup Rules (10% flat)
    rule, _ = CommissionRule.objects.get_or_create(
        commission_rule_plan=plan,
        rate_type='flat',
        defaults={'rate_value': 10.00, 'tenant': tenant}
    )
    
    # Simple cleanup
    from opportunities.models import Opportunity
    Opportunity.objects.all().delete()
    User.objects.filter(username='test_sales_rep').delete()

    # 4. Assign Plan
    UserCommissionPlan.objects.get_or_create(
        user=user,
        assigned_plan=plan,
        defaults={'start_date': timezone.now().date(), 'tenant': tenant}
    )
    
    # 5. Create Opportunities
    # Create Account (not used by Opportunity currently due to model definition, but kept for future)
    from accounts.models import Account
    # account, _ = Account.objects.get_or_create(account_name="Test Account", tenant=tenant, defaults={'owner': user})

    # Won Opportunity (for commission generation)
    won_stage, _ = OpportunityStage.objects.get_or_create(opportunity_stage_name="Closed Won", tenant=tenant, defaults={'is_won': True})
    
    opp_won = Opportunity.objects.create(
        opportunity_name="Won Deal",
        amount=Decimal('1000.00'),
        owner=user,
        stage=won_stage,
        close_date=timezone.now().date(),
        tenant=tenant,
        account=user # Using user as account due to legacy model definition
    )
    
    # Open Opportunity (for forecast)
    open_stage, _ = OpportunityStage.objects.get_or_create(opportunity_stage_name="Negotiation", tenant=tenant, defaults={'is_won': False})
    
    opp_open = Opportunity.objects.create(
        opportunity_name="Open Deal",
        amount=Decimal('5000.00'),
        owner=user,
        stage=open_stage,
        close_date=timezone.now().date() + timezone.timedelta(days=5),
        tenant=tenant,
        probability=Decimal('0.50'),
        account=user # Using user as account due to legacy model definition
    )
    
    print("Data setup complete.")
    
    # 6. Verify Forecast
    print("\nVerifying Forecast...")
    forecast = calculate_forecast(user)
    print(f"Forecast Result: {forecast}")
    
    assert forecast['forecast_amount'] == Decimal('500.00'), f"Expected 500.00, got {forecast['forecast_amount']}"
    assert forecast['weighted_forecast_amount'] == Decimal('250.00'), f"Expected 250.00, got {forecast['weighted_forecast_amount']}"
    print("Forecast verified successfully.")
    
    # 7. Verify Payment Generation
    print("\nVerifying Payment Generation...")
    # Ensure commission exists for the won deal
    # (Signal should have created it, but let's manually trigger just in case or check)
    comm = Commission.objects.filter(opportunity=opp_won).first()
    if not comm:
        print("Commission not auto-created by signal, creating manually...")
        comm = calculate_commission(opp_won)
        comm.tenant = tenant
        comm.save()
    
    # Approve it
    comm.status = 'approved'
    comm.save()
    
    # Generate Payment
    payment = generate_payment_records(user, timezone.now().date())
    
    if payment:
        print(f"Payment generated: {payment}")
        print(f"Linked commissions: {payment.commissions.count()}")
        assert payment.total_amount == Decimal('100.00'), f"Expected 100.00, got {payment.total_amount}"
        assert payment.commissions.count() == 1, "Expected 1 commission linked"
        print("Payment generation verified successfully.")
    else:
        print("No payment generated!")
        exit(1)

if __name__ == '__main__':
    run_verification()
