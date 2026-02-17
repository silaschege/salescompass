import os
import django
import sys
from decimal import Decimal

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from core.purchasing.services import ProcurementService
from core.purchasing.models import PurchaseOrder, PurchaseOrderLine, GoodsReceipt, SupplierInvoice
from suppliers.models import Supplier
from inventory.models import Warehouse, StockLocation
from products.models import Product
from accounting.models import AccountingIntegration, ChartOfAccount, JournalEntry
from django.db import transaction

User = get_user_model()

def run_test():
    print("Setting up test data...")
    # Get or create tenant
    tenant = Tenant.objects.first()
    if not tenant:
        tenant = Tenant.objects.create(name="Test Tenant", schema_name="test")
    
    # Get or create user
    user = User.objects.filter(email='test@example.com').first()
    if not user:
        user = User.objects.create(email='test@example.com', username='testuser', tenant=tenant)
        user.set_password('password')
        user.save()
        
    # Get or create accounts
    assets_acc, _ = ChartOfAccount.objects.get_or_create(
        tenant=tenant, account_code='1000', defaults={'account_name': 'Assets', 'account_type': 'asset'}
    )
    liability_acc, _ = ChartOfAccount.objects.get_or_create(
        tenant=tenant, account_code='2000', defaults={'account_name': 'Liabilities', 'account_type': 'liability_current'}
    )
    
    # Setup Integration Rules
    AccountingIntegration.objects.update_or_create(
        tenant=tenant, event_type='grn_received',
        defaults={'debit_account': assets_acc, 'credit_account': liability_acc}
    )
    AccountingIntegration.objects.update_or_create(
        tenant=tenant, event_type='bill_approved',
        defaults={'debit_account': liability_acc, 'credit_account': liability_acc} # Simplified
    )

    # Setup Product, Supplier, Warehouse
    supplier, _ = Supplier.objects.get_or_create(tenant=tenant, name="Test Supplier")
    warehouse, _ = Warehouse.objects.get_or_create(tenant=tenant, name="Test Warehouse")
    product, _ = Product.objects.get_or_create(tenant=tenant, name="Test Product", defaults={'cost_price': 100})
    
    # 1. Test Goods Receipt Journal
    print("Testing Goods Receipt Journal...")
    po = PurchaseOrder.objects.create(
        tenant=tenant, supplier=supplier, warehouse=warehouse, 
        order_date=timezone.now().date(), status='sent',
        po_number=f"PO-TEST-{timezone.now().timestamp()}"
    )
    PurchaseOrderLine.objects.create(
        tenant=tenant, purchase_order=po, product=product,
        quantity_ordered=10, unit_cost=100
    )
    
    receipt_data = [{'po_line_id': po.lines.first().id, 'qty': 5}]
    grn = ProcurementService.process_goods_receipt(po, receipt_data, user)
    
    # Check for Journal Entry
    # The service creates a journal based on 'grn_received' event
    # We can check JournalEntry objects with correct reference
    je = JournalEntry.objects.filter(reference=grn.grn_number).first()
    
    if je:
        print(f"Journal Entry found: {je.entry_number}")
        print(f"Status: {je.status}")
        print(f"Created By: {je.created_by.username if je.created_by else 'None'}")
        print(f"Posted By: {je.posted_by.username if je.posted_by else 'None'}")
        
        if je.status == 'posted' and je.posted_by == user:
            print("SUCCESS: GRN Journal Entry is posted and linked to user.")
        else:
            print("FAILURE: GRN Journal Entry status or user incorrect.")
    else:
        print("FAILURE: No Journal Entry created for GRN.")

    # 2. Test Invoice Posting
    print("\nTesting Invoice Posting...")
    invoice = SupplierInvoice.objects.create(
        tenant=tenant, supplier=supplier, invoice_number=f"INV-TEST-{timezone.now().timestamp()}",
        invoice_date=timezone.now().date(), due_date=timezone.now().date(),
        total_amount=500, status='draft'
    )
    # Mock matching
    # invoice.purchase_order = po # simplified
    
    try:
        updated_invoice = ProcurementService.post_supplier_invoice(invoice, user, force=True)
        je_inv = updated_invoice.journal_entry
        
        if je_inv:
            print(f"Invoice Journal Entry found: {je_inv.entry_number}")
            print(f"Status: {je_inv.status}")
            print(f"Created By: {je_inv.created_by.username if je_inv.created_by else 'None'}")
            print(f"Posted By: {je_inv.posted_by.username if je_inv.posted_by else 'None'}")
            
            if je_inv.status == 'posted' and je_inv.posted_by == user:
                print("SUCCESS: Invoice Journal Entry is posted and linked to user.")
            else:
                 print("FAILURE: Invoice Journal Entry status or user incorrect.")
        else:
            print("FAILURE: No Journal Entry created for Invoice.")
            
    except Exception as e:
        print(f"Error processing invoice: {e}")

if __name__ == "__main__":
    try:
        # Using atomic to rollback changes after test (optional, but good for cleanliness)
        # But for reproduction, we might want to see the data. 
        # Since I'm raising exception Rollback, it will clean up.
        with transaction.atomic():
             run_test()
             raise Exception("Rollback")
    except Exception as e:
        if str(e) != "Rollback":
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
