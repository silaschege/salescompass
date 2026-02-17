
import os
import django
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.test import Client
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from purchasing.models import SupplierInvoice, PurchaseOrder
from accounting.models import JournalEntry, AccountingIntegration, ChartOfAccount
from suppliers.models import Supplier

def run_test():
    print("Setting up test data...")
    # Get or create tenant
    tenant = Tenant.objects.first()
    if not tenant:
        tenant = Tenant.objects.create(name="Test Tenant", schema_name="test")
        
    user, _ = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com', 'tenant': tenant})
        
    # Setup Accounts
    def get_or_create_account(code, name, type_):
        acc, _ = ChartOfAccount.objects.get_or_create(
            tenant=tenant, account_code=code, 
            defaults={'account_name': name, 'account_type': type_}
        )
        return acc

    acc_payable = get_or_create_account('2000', 'Accounts Payable', 'liability_current')
    acc_expense = get_or_create_account('5000', 'General Expense', 'expense')
    
    # Setup Rule
    AccountingIntegration.objects.update_or_create(
        tenant=tenant, event_type='bill_approved',
        defaults={'debit_account': acc_expense, 'credit_account': acc_payable}
    )
    
    # Create Supplier
    supplier, _ = Supplier.objects.get_or_create(
        tenant=tenant, supplier_name="Test Supplier Ltd", 
        defaults={'email': 'supplier@example.com'}
    )
    
    # Create Invoice
    inv_num = f"INV-TEST-{timezone.now().timestamp()}"
    print(f"Creating Draft Invoice: {inv_num}")
    invoice = SupplierInvoice.objects.create(
        tenant=tenant,
        supplier=supplier,
        invoice_number=inv_num,
        invoice_date=timezone.now().date(),
        due_date=timezone.now().date(),
        total_amount=100.00,
        status='draft'
    )
    
    # Verify NO Journal yet
    ct = JournalEntry.objects.filter(tenant=tenant, reference=inv_num).count()
    if ct > 0:
        print("FAIL: Journal exists for draft invoice!")
        return
        
    # POST the invoice via save (simulating simple update)
    print("Updating Invoice status to 'posted' via save()...")
    invoice.status = 'posted'
    invoice.save()
    
    # Verify Journal Created
    journal = JournalEntry.objects.filter(tenant=tenant, reference=inv_num).first()
    if journal:
        print(f"SUCCESS: Journal Entry created! {journal}")
        print(f"Lines: {journal.lines.count()}")
        for line in journal.lines.all():
            print(f" - {line.account.account_name}: {line.debit} Dr / {line.credit} Cr")
    else:
        print("FAIL: No Journal Entry created after save!")
        
    # Test Duplicate Prevention
    print("Saving invoice again as posted...")
    invoice.save()
    cnt = JournalEntry.objects.filter(tenant=tenant, reference=inv_num).count()
    if cnt == 1:
        print("SUCCESS: No duplicate journal created.")
    else:
        print(f"FAIL: Found {cnt} journals (Duplicates created!)")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
