
import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salescompass.settings")
django.setup()

from tenants.models import Tenant
from core.models import User
from invoicing.models import Invoice, Payment
from billing.models import Subscription, Plan

def verify_invoicing():
    print("Verifying Invoicing App...")
    
    # Get or create necessary objects for foreign keys
    tenant, _ = Tenant.objects.get_or_create(name="Test Tenant", slug="test-tenant")
    user, _ = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})
    plan, _ = Plan.objects.get_or_create(name="Test Plan", price=100)
    subscription, _ = Subscription.objects.get_or_create(
        tenant=tenant,
        user=user,
        subscription_plan=plan
    )

    # 1. Create Invoice
    print("Creating Invoice...")
    invoice = Invoice.objects.create(
        tenant=tenant,
        subscription=subscription,
        amount=Decimal("100.00"),
        due_date=date.today(),
        invoice_number="INV-TEST-001"
    )
    print(f"Invoice created: {invoice}")

    # 2. Retrieve Invoice
    print("Retrieving Invoice...")
    retrieved_invoice = Invoice.objects.get(invoice_number="INV-TEST-001")
    assert retrieved_invoice == invoice
    print(f"Invoice retrieved: {retrieved_invoice}")

    # 3. Create Payment (if Payment model is ready)
    print("Creating Payment setup not strictly required for this test, skipping detailed payment flow for now to focus on basic model access.")
    
    # 4. Clean up
    print("Cleaning up...")
    invoice.delete()
    # Not deleting tenant/user/plan to avoid affecting other tests or data if running against real DB (though this should be test DB ideally, user environment seems development)

    print("Invoicing Verification Successful!")

if __name__ == "__main__":
    try:
        verify_invoicing()
    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
