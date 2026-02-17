import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

sys.path.append(os.path.join(os.getcwd(), 'core'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from expenses.models import CorporateCard, CardTransaction, ExpenseLine, ExpenseReport, ExpenseCategory
from expenses.services import CardImportService, AnalyticsService
from tenants.models import Tenant

User = get_user_model()

def run_phase2_verify():
    print("Starting Expenses Phase 2 Verification...")
    
    tenant = Tenant.objects.first()
    if not tenant:
        print("No tenant. Creating test tenant.")
        tenant = Tenant.objects.create(name="Test Tenant", schema_name="test2", domain_url="test2.local")
        
    user = User.objects.first()
    if not user.tenant:
        user.tenant = tenant
        user.save()

    # 1. Test Corporate Card Creation
    print("\n1. Testing Corporate Card Creation...")
    card, _ = CorporateCard.objects.get_or_create(
        tenant=tenant,
        name="Amex Platinum",
        defaults={'last_4_digits': '1234', 'assigned_employee': user}
    )
    print(f"Created Card: {card}")

    # 2. Test CSV Import & Matching
    print("\n2. Testing Import & Matching...")
    
    # Create an Expense Line expecting a match
    import random
    report_num = f"CHK-{random.randint(1000,9999)}"
    report = ExpenseReport.objects.create(tenant=tenant, employee=user, title="Business Trip", report_number=report_num)
    cat = ExpenseCategory.objects.first() or ExpenseCategory.objects.create(tenant=tenant, name="Travel")
    
    line = ExpenseLine.objects.create(
        tenant=tenant, report=report, category=cat, 
        date=timezone.now().date(), amount=Decimal('150.00'), description="Uber Ride"
    )
    
    # Mock CSV Content
    csv_content = f"Date,Merchant,Amount,Currency\n{timezone.now().date()},Ober Cabs,150.00,KES"
    
    import io
    csv_file = io.StringIO(csv_content)
    
    count = CardImportService.import_transactions_csv(csv_file, card)
    print(f"Imported {count} transactions.")
    
    matches = CardImportService.auto_match_transactions(tenant)
    print(f"Auto-matched {matches} transactions.")
    
    line.refresh_from_db()
    if line.matched_transaction:
        print("SUCCESS: Expense Line matched to transaction.")
    else:
        print("FAILURE: Expense Line NOT matched.")
        
    # 3. Test Analytics
    print("\n3. Testing Analytics...")
    data = AnalyticsService.get_spend_by_category(tenant, timezone.now().date(), timezone.now().date())
    print(f"Analytics Data: {list(data)}")
    if data:
        print("SUCCESS: Analytics returned data.")
    else:
        print("WARNING: Analytics returned empty (might be expected if no approved reports).")

if __name__ == "__main__":
    try:
        run_phase2_verify()
    except Exception as e:
        print(f"ERROR: {e}")
