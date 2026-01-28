import os
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine, SupplierInvoice
from inventory.models import StockLevel, StockMovement
from accounting.services import JournalService
from assets.models import FixedAsset

class ProcurementService:
    """
    Main service for handling complex procurement workflows, 
    IFRS compliance, and cross-module integrations.
    """

    @staticmethod
    @transaction.atomic
    def approve_purchase_order(po, user):
        """Approve PO and handle commitment tracking."""
        if po.status != 'draft':
            raise ValueError("Only draft orders can be approved.")
            
        po.status = 'sent'
        po.approved_by = user
        po.approval_date = timezone.now()
        po.save()
        
        # Optional: IPSAS Commitment Accounting entry could be triggered here
        return po

    @staticmethod
    @transaction.atomic
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

        # 5. Accounting Integration (Double Entry)
        # Dr Inventory / Cr Accrued Liability (GRNI - Goods Received Not Invoiced)
        # We search for the integration rules for 'grn_received'
        from accounting.models import AccountingIntegration
        rule = AccountingIntegration.objects.filter(tenant=tenant, event_type='grn_received').first()
        
        if rule and rule.debit_account and rule.credit_account:
            JournalService.create_journal_entry(
                tenant=tenant, date=timezone.now().date(),
                description=f"Inventory Receipt: {grn.grn_number}",
                user=user, reference=grn.grn_number, status='posted',
                lines=[
                    {'account': rule.debit_account, 'debit': total_receipt_value, 'credit': 0},
                    {'account': rule.credit_account, 'debit': 0, 'credit': total_receipt_value},
                ]
            )

        # Update PO Status
        if all(l.quantity_received >= l.quantity_ordered for l in po.lines.all()):
            po.status = 'received'
        else:
            po.status = 'partial'
        po.save()

        return grn

    @staticmethod
    @transaction.atomic
    def post_supplier_invoice(invoice, user):
        """
        Finalize a vendor bill and record the liability (AP).
        (IAS 32 / IFRS 9)
        """
        if invoice.status != 'draft':
            return invoice

        tenant = invoice.tenant
        
        # 1. Update Status
        invoice.status = 'posted'
        invoice.save()

        # 2. Accounting Integration
        # Dr Accrued Liability (GRNI) / Cr Accounts Payable
        from accounting.models import AccountingIntegration
        rule = AccountingIntegration.objects.filter(tenant=tenant, event_type='bill_approved').first()
        
        if rule and rule.debit_account and rule.credit_account:
            JournalService.create_journal_entry(
                tenant=tenant, date=invoice.invoice_date,
                description=f"Vendor Bill Posted: {invoice.invoice_number}",
                user=user, reference=invoice.invoice_number, status='posted',
                lines=[
                    {'account': rule.debit_account, 'debit': invoice.total_amount, 'credit': 0},
                    {'account': rule.credit_account, 'debit': 0, 'credit': invoice.total_amount}
                ]
            )
            
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
