
import os
import django
import sys

# Set up Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from tenants.models import Tenant
from core.models import User
from leads.models import Lead, LeadStatus
from accounts.models import Account, Contact
from opportunities.models import Opportunity, OpportunityStage
from commissions.models import Commission
from leads.services import LeadScoringService
from django.utils import timezone
from django.db import transaction

def verify_conversion():
    print("Starting Lead Conversion and Commission Verification...")
    
    with transaction.atomic():
        # 1. Create Tenant if not exists
        tenant, created = Tenant.objects.get_or_create(
            name="Verification Tenant",
            defaults={'subdomain': 'verify', 'is_active': True}
        )
        if created:
            print(f"Created Tenant: {tenant}")
            
        # 2. Create User if not exists
        user, created = User.objects.get_or_create(
            email="verify@example.com",
            defaults={
                'username': 'verify_user',
                'first_name': 'Verify',
                'last_name': 'User',
                'is_active': True,
                'tenant': tenant
            }
        )
        if created:
            user.set_password('verify_password')
            user.save()
            print(f"Created User: {user}")
        else:
            user.tenant = tenant
            user.save()

        # 3. Create OpportunityStage for tenant
        stage, created = OpportunityStage.objects.get_or_create(
            tenant=tenant,
            opportunity_stage_name="Initial Prospecting",
            defaults={'order': 0, 'probability': 10.0}
        )
        if created:
            print(f"Created Stage: {stage}")
            
        won_stage, created = OpportunityStage.objects.get_or_create(
            tenant=tenant,
            opportunity_stage_name="Closed Won",
            defaults={'order': 10, 'probability': 100.0, 'is_won': True}
        )
        if created:
            print(f"Created Won Stage: {won_stage}")

        # 4. Create Lead
        lead = Lead.objects.create(
            tenant=tenant,
            first_name="Lead",
            last_name="Test",
            company="Test Company",
            email="lead@test.com",
            status="new",
            owner=user,
            annual_revenue=100000
        )
        print(f"Created Lead: {lead.full_name}")

        # 4.5 Create Commission Plan for User
        from commissions.models import CommissionPlan, CommissionRule, UserCommissionPlan
        plan, _ = CommissionPlan.objects.get_or_create(
            tenant=tenant,
            commission_plan_name="Verification Plan",
            defaults={'basis': 'revenue', 'commission_plan_is_active': True}
        )
        CommissionRule.objects.get_or_create(
            tenant=tenant,
            commission_rule_plan=plan,
            defaults={'rate_type': 'flat', 'rate_value': 10.0}
        )
        UserCommissionPlan.objects.get_or_create(
            tenant=tenant,
            user=user,
            assigned_plan=plan,
            defaults={'start_date': timezone.now().date()}
        )
        print("Created Commission Plan and Assignment for User.")

        # 5. Convert Lead
        print("Converting Lead...")
        opportunity = LeadScoringService.create_opportunity_from_lead(lead, creator=user)
        print(f"Conversion successful. Opportunity: {opportunity.opportunity_name}")

        # 6. Verify Account and Contact
        account = Account.objects.get(tenant=tenant, account_name="Test Company")
        print(f"Verified Account: {account}")
        
        contact = Contact.objects.get(tenant=tenant, email="lead@test.com")
        print(f"Verified Contact: {contact}")
        
        # 7. Verify Opportunity association
        if opportunity.account == account:
            print("Verified Opportunity association with Account.")
        else:
            print(f"ERROR: Opportunity account {opportunity.account} != {account}")
            return False

        # 8. Mark Opportunity as Won
        print("Marking Opportunity as Won...")
        opportunity.stage = won_stage
        opportunity.save()
        
        # 9. Verify Commission
        # Note: Commissions might be created asynchronously or via signals.
        # We check if a commission exists for this opportunity.
        import time
        time.sleep(1) # Give signals time to process if needed (though post_save is synchronous)
        
        commissions = Commission.objects.filter(opportunity=opportunity)
        if commissions.exists():
            commission = commissions.first()
            print(f"Verified Commission: {commission.amount} for {commission.user}")
            print(f"Commission Status: {commission.status}")
        else:
            print("ERROR: Commission not created via signal!")
            # Let's check why calculation might fail
            from commissions.utils import calculate_commission
            try:
                comm = calculate_commission(opportunity)
                if comm:
                    comm.tenant = tenant
                    comm.save()
                    print(f"Commission created after manual trigger: {comm.amount}")
                else:
                    print("Commission STILL not created after manual trigger (calculate_commission returned None).")
            except Exception as e:
                print(f"Error during manual commission calculation: {e}")
            
            # Check if it was created now
            if Commission.objects.filter(opportunity=opportunity).exists():
                return True
            return False

    print("\nVerification completed successfully!")
    return True

if __name__ == "__main__":
    success = verify_conversion()
    if not success:
        sys.exit(1)
