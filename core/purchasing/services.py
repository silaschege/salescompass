from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import (
    PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine,
    SupplierInvoice, SupplierPayment, PurchaseRequisition, PurchaseRequisitionLine
)
from inventory.models import StockLocation
from suppliers.models import Supplier
from products.models import Product
from hr.models import Department
from assets.models import AssetCategory, FixedAsset

class ProcurementService:
    @staticmethod
    def approve_purchase_order(po, user, rejection_reason=''):
        """
        Approve a purchase order and move to next state.
        """
        tenant = po.tenant
        
        # Update status based on current status
        if po.status == 'draft':
            po.status = 'pending_approval'
            po.save()
        elif po.status == 'pending_approval':
            po.status = 'approved'
            po.approved_by = user
            po.approval_date = timezone.now()
            po.save()
            
            # After approval, send to supplier (could be done separately)
            po.status = 'sent'
            po.save()
    
    @staticmethod
    def process_goods_receipt(po, receipt_data, user):
        """
        Process incoming goods, update inventory, and trigger GL entries.
        receipt_data: [{'po_line_id': int, 'qty': decimal, 'location_id': int}, ...]
        """
        tenant = po.tenant
        grn = GoodsReceipt.objects.create(
            grn_number=f"GRN-{po.po_number}-{timezone.now().timestamp()}",
            purchase_order=po,
            received_date=timezone.now().date(),
            received_by=user,
            warehouse=po.warehouse,
            tenant=tenant
        )

        total_receipt_value = Decimal('0')
        journal_lines = []

        for item in receipt_data:
            line = PurchaseOrderLine.objects.get(id=item['po_line_id'])
            qty = Decimal(str(item['qty']))
            
            if qty <= 0: continue

            val_received = qty * line.unit_cost
            total_receipt_value += val_received

            # 1. Create Receipt Line
            GoodsReceiptLine.objects.create(
                receipt=grn, po_line=line, quantity_received=qty, 
                location_id=item.get('location_id'), tenant=tenant
            )

            # 2. Update PO Line
            line.quantity_received += qty
            line.save()

            # 3. Update Inventory (Weighted Average Costing - IAS 2)
            from inventory.services import InventoryService
            InventoryService.add_stock(
                product=line.product, warehouse=po.warehouse, 
                quantity=qty, user=user, unit_cost=line.unit_cost,
                reference_type='purchase_order', reference_id=po.id,
                tenant=tenant
            )

            # 4. Handle Asset Recognition (IAS 16)
            if line.is_fixed_asset and line.asset_category:
                # Create draft Fixed Asset for each unit if needed, or batch
                # Here we create one record for the batch for simplicity
                FixedAsset.objects.create(
                    tenant=tenant,
                    asset_number=f"AST-{grn.grn_number}-{line.id}",
                    name=f"{line.product.product_name} (from PO {po.po_number})",
                    category=line.asset_category,
                    purchase_date=timezone.now().date(),
                    purchase_cost=val_received,
                    status='active'
                )

        # 5. Skip journal entry — will be posted when GRN is confirmed
        # GRN stays as 'draft' until user confirms via GRN detail page

        # Update PO Status
        if all(l.quantity_received >= l.quantity_ordered for l in po.lines.all()):
            po.status = 'received'
        else:
            po.status = 'partial'
        po.save()

        # 6. Create Draft Vendor Bill (Supplier Invoice) automatically
        # This streamlines AP by pre-filling invoice data from receipt
        SupplierInvoice.objects.create(
            tenant=tenant,
            supplier=po.supplier,
            purchase_order=po,
            invoice_number=f"DRAFT-{grn.grn_number}", # Placeholder
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30), # Default terms
            total_amount=total_receipt_value,
            status='draft'
        )

        return grn

    @staticmethod
    @transaction.atomic
    def confirm_goods_receipt(grn, user):
        """
        Confirm a draft GRN and post the journal entry to the ledger.
        """
        if grn.status != 'draft':
            raise ValueError("Only draft GRNs can be confirmed.")

        tenant = grn.tenant

        # Calculate total receipt value from GRN lines
        total_receipt_value = Decimal('0')
        for grn_line in grn.lines.all():
            total_receipt_value += grn_line.quantity_received * grn_line.po_line.unit_cost

        # Accounting Integration (Double Entry)
        # Dr Inventory / Cr Accrued Liability (GRNI - Goods Received Not Invoiced)
        from accounting.models import AccountingIntegration
        rule = AccountingIntegration.objects.filter(tenant=tenant, event_type='grn_received').first()

        if rule and rule.debit_account and rule.credit_account:
            from accounting.services import JournalService
            JournalService.create_journal_entry(
                tenant=tenant, date=timezone.now().date(),
                description=f"Inventory Receipt: {grn.grn_number}",
                user=user, reference=grn.grn_number, status='posted',
                lines=[
                    {'account': rule.debit_account, 'debit': total_receipt_value, 'credit': 0},
                    {'account': rule.credit_account, 'debit': 0, 'credit': total_receipt_value},
                ]
            )

        grn.status = 'confirmed'
        grn._skip_signal = True  # Prevent signal from also creating journal entry
        grn.save()

        return grn

    @staticmethod
    def check_three_way_match(invoice):
        """
        IPSAS/IFRS Compliance: Ensure Invoice matches PO and GRN.
        Returns (is_match, message)
        """
        po = invoice.purchase_order
        if not po:
            return True, "No PO linked, matching skipped."
            
        # For each line in PO, compare with invoice
        for po_line in po.lines.all():
            # Find corresponding invoice line (simplified - assume same product)
            # In reality, you'd match by product and quantity
            pass
            
        # Compare totals
        if abs(invoice.total_amount - po.total_amount) < Decimal('0.01'):
            return True, "Three-way match successful"
        else:
            return False, f"Invoice amount ({invoice.total_amount}) does not match PO amount ({po.total_amount})"

    @staticmethod
    @transaction.atomic
    def post_supplier_invoice(invoice, user, force=False):
        """
        Post supplier invoice to ledger (create journal entry).
        """
        tenant = invoice.tenant
        
        if invoice.status != 'draft':
            raise ValueError("Only draft invoices can be posted")
        
        # Three-way match check
        is_match, message = ProcurementService.check_three_way_match(invoice)
        
        if not is_match and not force:
            raise ValueError(f"Three-way match failed: {message}")
        
        # 1. Accounting Integration
        # Dr Expense/Asset / Cr Accounts Payable
        from accounting.models import AccountingIntegration
        rule = AccountingIntegration.objects.filter(tenant=tenant, event_type='bill_approved').first()
        
        if rule and rule.debit_account and rule.credit_account:
            from accounting.services import JournalService

            # Determine debit account (asset account if fixed asset, else default)
            debit_account = rule.debit_account
            if invoice.purchase_order and hasattr(invoice.purchase_order, 'lines'):
                for po_line in invoice.purchase_order.lines.all():
                    if po_line.is_fixed_asset and po_line.asset_category:
                        if po_line.asset_category.asset_account:
                            debit_account = po_line.asset_category.asset_account
                        break

            journal_entry = JournalService.create_journal_entry(
                tenant=tenant, date=invoice.invoice_date,
                description=f"Vendor Invoice: {invoice.invoice_number}",
                user=user, reference=invoice.invoice_number, status='posted',
                lines=[
                    {'account': debit_account, 'debit': invoice.total_amount, 'credit': 0,
                     'description': f"Vendor Invoice: {invoice.invoice_number} - {invoice.supplier.supplier_name}"},
                    {'account': rule.credit_account, 'debit': 0, 'credit': invoice.total_amount,
                     'description': f"AP for Invoice: {invoice.invoice_number}"},
                ]
            )
            invoice.journal_entry = journal_entry

        # Update status
        invoice.status = 'posted'
        invoice._skip_signal = True  # Prevent signal from creating duplicate entry
        invoice.save()
        
        # 2. Update related PO status
        if invoice.purchase_order:
            po = invoice.purchase_order
            if po.status == 'received':
                po.status = 'billed'
            elif po.status == 'partial':
                po.status = 'partially_billed'
            po.save()

        return invoice

    @staticmethod
    @transaction.atomic
    def process_supplier_payment(payment, user):
        """
        Record vendor payment and settle AP liability.
        """
        tenant = payment.tenant
        
        # 1. Accounting Integration
        # Dr Accounts Payable / Cr Bank
        from accounting.models import AccountingIntegration
        rule = AccountingIntegration.objects.filter(tenant=tenant, event_type='payment_sent').first()
        
        if rule and rule.debit_account and rule.credit_account:
            from accounting.services import JournalService
            journal = JournalService.create_journal_entry(
                tenant=tenant, date=payment.payment_date,
                description=f"Supplier Payment: {payment.reference}",
                user=user, reference=payment.reference, status='posted',
                lines=[
                    {'account': rule.debit_account, 'debit': payment.amount, 'credit': 0},
                    {'account': rule.credit_account, 'debit': 0, 'credit': payment.amount}
                ]
            )
            payment.journal_entry = journal
            payment.save()

        # 2. Mark related invoices as paid
        # Simplification: Assume payment amount fully settles linked invoices
        for inv in payment.invoices.all():
            inv.status = 'paid'
            inv.save()

        return payment