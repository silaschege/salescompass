
import os
import django
from django.conf import settings
from decimal import Decimal
from django.utils import timezone

import sys
sys.path.append(os.path.join(os.getcwd(), 'core'))
# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from purchasing.models import SupplierInvoice, PurchaseOrder
from accounting.models import JournalEntry, JournalEntryLine, AccountingIntegration, ChartOfAccount
from tenants.models import Tenant
from suppliers.models import Supplier

def reproduce_issue():
    print("reproducing issue...")
    
    # 1. Create or get a Tenant with ID=24 (or mimic it)
    try:
        tenant = Tenant.objects.get(id=24)
        print(f"Found tenant 24: {tenant}")
    except Tenant.DoesNotExist:
        # Create a dummy tenant
        print("Tenant 24 not found, creating a new tenant...")
        tenant = Tenant.objects.create(name="Test Tenant 24", schema_name="tenant_24")
        # Ensure ID is not 1 (it likely won't be if 1 exists)
        if tenant.id == 1:
            tenant = Tenant.objects.create(name="Test Tenant Another", schema_name="tenant_another")
    
    print(f"Using Tenant: {tenant.id} - {tenant.name}")

    if tenant.id == 1:
        print("WARNING: Using Tenant 1. This might not reproduce the issue if the bug defaults to 1.")
    
    # 2. Setup Accounts and Integration Rules
    # We need a debit and credit account for 'bill_approved'
    
    # Get or create accounts
    debit_acc, _ = ChartOfAccount.objects.get_or_create(
        tenant=tenant, 
        account_code="EXP-001",
        defaults={'account_name': 'Test Expense', 'account_type': 'expense'}
    )
    credit_acc, _ = ChartOfAccount.objects.get_or_create(
        tenant=tenant, 
        account_code="AP-001",
        defaults={'account_name': 'Accounts Payable', 'account_type': 'liability_current'}
    )
    
    # Setup Integration Rule
    AccountingIntegration.objects.update_or_create(
        tenant=tenant,
        event_type='bill_approved',
        defaults={
            'debit_account': debit_acc,
            'credit_account': credit_acc
        }
    )
    
    # 3. Create a Supplier
    supplier, _ = Supplier.objects.get_or_create(
        tenant=tenant,
        supplier_name="Test Supplier",
        defaults={'email': "supplier@test.com"}
    )
    
    # 4. Create a Supplier Invoice
    invoice = SupplierInvoice.objects.create(
        tenant=tenant,
        supplier=supplier,
        invoice_number=f"INV-TEST-{timezone.now().timestamp()}",
        invoice_date=timezone.now().date(),
        due_date=timezone.now().date(),
        total_amount=Decimal("100.00"),
        status='draft'
    )
    
    print(f"Created Invoice: {invoice.id}, Tenant: {invoice.tenant.id}")
    
    # 5. Post the Invoice (Trigger Signal)
    print("Posting invoice...")
    invoice.status = 'posted'
    invoice.save()
    
    # 6. Check created Journal Entry
    je = JournalEntry.objects.filter(reference=invoice.invoice_number).first()
    
    if je:
        print(f"Journal Entry Created: {je.entry_number}")
        print(f"Journal Entry Tenant ID: {je.tenant.id}")
        
        if je.tenant.id != tenant.id:
            print(f"FAILURE: Journal Entry Tenant ID ({je.tenant.id}) does not match Invoice Tenant ID ({tenant.id})")
        else:
            print("SUCCESS: Tenant IDs match.")
    else:
        print("FAILURE: No Journal Entry created.")

if __name__ == "__main__":
    reproduce_issue()
