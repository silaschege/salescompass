from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from .models import SupplierInvoice, SupplierPayment, GoodsReceipt
from accounting.services import JournalService
from accounting.models import AccountingIntegration
from django.utils import timezone


# ============================================================================
# SUPPLIER INVOICE INTEGRATION
# ============================================================================

@receiver(post_save, sender=SupplierInvoice)
def handle_supplier_invoice_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when Supplier Invoice is posted (approved).
    
    Accounting Entry:
    Dr: Expense/Asset Account (from config.debit_account)
    Cr: Accounts Payable (from config.credit_account)
    """
    # Skip if the service already handled journal creation
    if getattr(instance, '_skip_signal', False):
        return

    # Only process when status changes to 'posted'
    if instance.status != 'posted':
        return
    
    # Prevent duplicate entries
    if instance.journal_entry is not None:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant, 
            event_type='bill_approved'
        )
        
        # Determine the appropriate expense/asset account
        # If linked to a PO with asset category, use asset account
        # Otherwise use the default expense account from config
        debit_account = config.debit_account
        
        if instance.purchase_order and hasattr(instance.purchase_order, 'lines'):
            # Check if any PO line is for a fixed asset
            for po_line in instance.purchase_order.lines.all():
                if po_line.is_fixed_asset and po_line.asset_category:
                    if po_line.asset_category.asset_account:
                        debit_account = po_line.asset_category.asset_account
                    break
        
        # Build journal entry lines
        lines = [
            {
                'account': debit_account,
                'debit': instance.total_amount,
                'credit': 0,
                'description': f"Vendor Invoice: {instance.invoice_number} - {instance.supplier.supplier_name}"
            },
            {
                'account': config.credit_account,  # Accounts Payable
                'debit': 0,
                'credit': instance.total_amount,
                'description': f"AP for Invoice: {instance.invoice_number}"
            }
        ]
        
        # Create journal entry
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.invoice_date,
            description=f"Vendor Invoice: {instance.invoice_number}",
            user=None,  # System-generated
            lines=lines,
            reference=instance.invoice_number,
            status='posted'
        )
        
        # Link journal entry to invoice
        instance.journal_entry = journal_entry
        instance._skip_signal = True  # Prevent re-triggering signal
        instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for bill_approved (Tenant: {instance.tenant})")


# ============================================================================
# SUPPLIER PAYMENT INTEGRATION
# ============================================================================

@receiver(post_save, sender=SupplierPayment)
def handle_supplier_payment_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when payment is made to supplier.
    
    Accounting Entry:
    Dr: Accounts Payable (from config.debit_account)
    Cr: Cash/Bank Account (from config.credit_account)
    """
    # Only process new payments
    if not created:
        return
    
    # Prevent duplicate entries
    if instance.journal_entry is not None:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='payment_sent'
        )
        
        # Build journal entry lines
        lines = [
            {
                'account': config.debit_account,  # Accounts Payable
                'debit': instance.amount,
                'credit': 0,
                'description': f"Payment to {instance.supplier.supplier_name}"
            },
            {
                'account': config.credit_account,  # Cash/Bank
                'debit': 0,
                'credit': instance.amount,
                'description': f"Payment via {instance.get_method_display()}: {instance.reference}"
            }
        ]
        
        # Create journal entry
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.payment_date,
            description=f"Vendor Payment: {instance.supplier.supplier_name}",
            user=None,  # System-generated
            lines=lines,
            reference=instance.reference or f"PAY-{instance.pk}",
            status='posted'
        )
        
        # Link journal entry to payment
        instance.journal_entry = journal_entry
        instance._skip_signal = True  # Prevent re-triggering signal
        instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for payment_sent (Tenant: {instance.tenant})")


# ============================================================================
# GOODS RECEIPT (GRN) INTEGRATION
# ============================================================================

@receiver(post_save, sender=GoodsReceipt)
def handle_goods_receipt_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when goods receipt is CONFIRMED (not on initial save).
    
    Draft GRNs should not post to the ledger. Only confirmed GRNs create entries.
    The confirm_goods_receipt service method handles the primary journal entry
    creation, so this signal acts as a safety net / fallback.
    
    Accounting Entry:
    Dr: Inventory Account (from config.debit_account)
    Cr: GRN Clearing/AP Account (from config.credit_account)
    """
    # Skip if the service already handled journal creation
    if getattr(instance, '_skip_signal', False):
        return

    # Only post journal entries for confirmed GRNs
    if instance.status != 'confirmed':
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='grn_received'
        )
        
        # Calculate total value of goods received
        total_value = 0
        for line in instance.lines.all():
            # Use the PO line's unit cost
            line_value = line.quantity_received * line.po_line.unit_cost
            total_value += line_value
        
        # Skip if no value
        if total_value == 0:
            return
        
        # Build journal entry lines
        lines = [
            {
                'account': config.debit_account,  # Inventory
                'debit': total_value,
                'credit': 0,
                'description': f"Goods Receipt: {instance.grn_number}"
            },
            {
                'account': config.credit_account,  # GRN Clearing or AP
                'debit': 0,
                'credit': total_value,
                'description': f"GRN Clearing: PO {instance.purchase_order.po_number}"
            }
        ]
        
        # Create journal entry
        JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.received_date,
            description=f"Goods Receipt: {instance.grn_number}",
            user=instance.received_by,
            lines=lines,
            reference=instance.grn_number,
            status='posted'
        )
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for grn_received (Tenant: {instance.tenant})")
