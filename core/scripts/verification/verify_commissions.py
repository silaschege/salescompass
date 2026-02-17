import os
import django
import sys
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from tenants.models import Tenant
from core.models import User
from commissions.models import CommissionPlan, CommissionRule, UserCommissionPlan, Commission
from opportunities.models import Opportunity, OpportunityStage

def verify():
    print("Starting Commission Verification...")
    
    try:
        # 1. Setup Data
        tenant, _ = Tenant.objects.get_or_create(
            name="Commission Tenant", 
            defaults={'subdomain': 'comm-test', 'slug': 'comm-test'}
        )
        user, _ = User.objects.get_or_create(
            username="sales_rep_comm", 
            defaults={'tenant': tenant, 'email': 'salesrep@commtest.com'}
        )
        
        # Create Stage
        stage, _ = OpportunityStage.objects.get_or_create(
            opportunity_stage_name="closed_won",
            tenant=tenant,
            defaults={'is_won': True, 'order': 100}
        )
        
        # Create Commission Plan
        plan = CommissionPlan.objects.create(
            commission_plan_name="Standard Plan",
            tenant=tenant,
            basis='revenue',
            period='monthly'
        )
        print(f"Created Plan: {plan.commission_plan_name}")
        
        # Create Commission Rule (10% flat)
        rule = CommissionRule.objects.create(
            commission_rule_plan=plan,
            tenant=tenant,
            rate_type='flat',
            rate_value=Decimal('10.00')
        )
        print(f"Created Rule: {rule.rate_value}%")
        
        # Assign Plan to User
        assignment = UserCommissionPlan.objects.create(
            user=user,
            user_commission_plan=plan,
            tenant=tenant,
            start_date=timezone.now().date() - timedelta(days=30),
        )
        print(f"Assigned Plan to User: {user}")
        
        # Create Opportunity (Not Won Yet)
        opp = Opportunity.objects.create(
            opportunity_name="Big Commission Deal",
            tenant=tenant,
            amount=Decimal('50000.00'),
            close_date=timezone.now().date(),
            account=user,
            owner=user, # The commission earner
            stage=stage, # Already Won - Simulate update later
        )
        print(f"Created Opportunity: {opp.opportunity_name} Amount: {opp.amount}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error setting up data: {e}")
        return

    # 2. Verify Commission Created
    try:
        print("\nVerifying Commission Record...")
        commissions = Commission.objects.filter(opportunity=opp, user=user)
        
        if commissions.exists():
            comm = commissions.first()
            expected = Decimal('5000.00') # 10% of 50000
            if comm.amount == expected:
                print(f"PASS: Commission created correctly. Amount: {comm.amount}")
            else:
                print(f"FAIL: Commission amount incorrect. Expected: {expected}, Got: {comm.amount}")
        else:
            # Manually trigger signal for this test (since it was created directly in Won stage)
            from commissions.signals import opportunity_commission_signal
            from django.db.models.signals import post_save
            post_save.send(sender=Opportunity, instance=opp, created=False)
            
            # Check again
            commissions = Commission.objects.filter(opportunity=opp, user=user)
            if commissions.exists():
                comm = commissions.first()
                print(f"PASS: Commission created after signal trigger. Amount: {comm.amount}")
            else:
                print("FAIL: No commission record created even after signal trigger.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error verifying commission: {e}")

if __name__ == '__main__':
    verify()
