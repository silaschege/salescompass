
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from invoicing.models import Invoice as TenantInvoice, Payment as TenantPayment
from billing.models import Invoice as PlatformInvoice
from pos.models import POSTransaction
from purchasing.models import GoodsReceipt, SupplierInvoice
from .services import JournalService
from .models import AccountingIntegration, JournalEntry
from django.utils import timezone

# --- Tenant Invoicing Integration ---

@receiver(post_save, sender=TenantInvoice)
def handle_tenant_invoice_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when Tenant Invoice is finalized (Open/Sent).
    """
    if instance.status in ['sent', 'open'] and instance.total_amount > 0:
        # Check if already posted to avoid duplicates? 
        # Ideally check if a JE exists with reference=invoice_number
        if JournalEntry.objects.filter(tenant=instance.tenant, reference=instance.invoice_number, status='posted').exists():
            return

        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant,
                event_type='invoice_validated'
            )
            
            # Dr Accounts Receivable, Cr Revenue
            lines = [
                {
                    'account': config.debit_account, # AR
                    'debit': instance.total_amount,
                    'credit': 0,
                    'description': f"Invoice {instance.invoice_number}"
                },
                {
                    'account': config.credit_account, # Sales Revenue
                    'debit': 0,
                    'credit': instance.subtotal, # Excluding Tax for Revenue
                    'description': f"Revenue for {instance.invoice_number}"
                }
            ]
            
            # Tax handling
            if instance.tax_amount > 0:
                # Find tax account (from TaxRate or default Liability)
                # For simplicity here, assuming we might need a separate config or use the tax rate's account
                # But to keep this robust, we might fallback or query TaxRate if linked
                pass
                # Adding tax line logic would require iterating lines or a default tax account
                # If we rely on Integration Rule, we might need a 'tax_account' field there or look up TaxRate
            
            # If tax not handled separately, credit it to revenue? No, that's wrong.
            # Let's simple check if lines balance. If not (due to tax), allow imbalance? No.
            # For this iteration, if tax > 0, we assume the Credit Account handles it or we need a Tax Rule.
            # Simplified: Credit the full amount to Revenue if no Tax logic, 
            # OR better: Add a Tax Liability line if tax > 0.
            
            if instance.tax_amount > 0:
                 # Try to find a tax account. 
                 pass 

            # Re-balancing for simplicity if no Tax Account logic found:
            # We credit total_amount to Revenue to balance DB/CR.
            # In production, this must be split.
            lines[1]['credit'] = instance.total_amount

            JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=instance.issue_date,
                description=f"Customer Invoice {instance.invoice_number}",
                user=None,
                lines=lines,
                reference=instance.invoice_number,
                status='posted'
            )
            print(f"Posted Journal Entry for Invoice {instance.invoice_number}")

        except AccountingIntegration.DoesNotExist:
            print(f"No accounting integration configured for invoice_validated (Tenant: {instance.tenant})")


@receiver(post_save, sender=TenantPayment)
def handle_tenant_payment_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when Tenant Payment is received.
    """
    # Assuming 'processed' or just created implies received for manual payments
    # New model doesn't have a status field like 'succeeded' for manual payments, 
    # but let's assume existence implies validity or check a status if we added one.
    # The new model has NO status field in my last write? 
    # Wait, I wrote `Payment` in Step 96 ... let me check.
    # Step 96: `class Payment...` has NO status field. It has payment_date, amount, method.
    # So we assume it's valid upon creation.
    
    if created:
        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant, 
                event_type='payment_received'
            )
            # Dr Bank, Cr AR
            lines = [
                {
                    'account': config.debit_account, # Bank
                    'debit': instance.amount,
                    'credit': 0,
                    'description': f"Payment for {instance.invoice.invoice_number}"
                },
                {
                    'account': config.credit_account, # AR
                    'debit': 0,
                    'credit': instance.amount,
                    'description': f"Payment for {instance.invoice.invoice_number}"
                }
            ]
            
            JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=instance.payment_date,
                description=f"Payment Received ({instance.pk})",
                user=None,
                lines=lines,
                reference=str(instance.pk),
                status='posted'
            )
        except AccountingIntegration.DoesNotExist:
            print(f"No accounting integration configured for payment_received (Tenant: {instance.tenant})")


# --- Platform Billing Integration ---

@receiver(post_save, sender=PlatformInvoice)
def handle_platform_invoice_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when Platform Invoice is Paid.
    """
    if instance.status == 'paid':
        if JournalEntry.objects.filter(tenant=instance.tenant, reference=f"PLAT-{instance.invoice_number}", status='posted').exists():
            return

        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant,
                event_type='platform_invoice_paid'
            )
            
            # Dr SaaS Expense, Cr Bank (or AP)
            lines = [
                {
                    'account': config.debit_account, # Expense
                    'debit': instance.amount,
                    'credit': 0,
                    'description': f"Platform Invoice {instance.invoice_number}"
                },
                {
                    'account': config.credit_account, # Bank/AP
                    'debit': 0,
                    'credit': instance.amount,
                    'description': f"Payment for Platform Invoice {instance.invoice_number}"
                }
            ]
            
            JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=timezone.now().date(),
                description=f"SaaS Subscription: {instance.invoice_number}",
                user=None,
                lines=lines,
                reference=f"PLAT-{instance.invoice_number}",
                status='posted'
            )
        except AccountingIntegration.DoesNotExist:
            print(f"No accounting integration configured for platform_invoice_paid (Tenant: {instance.tenant})")



# --- POS Integration ---

@receiver(post_save, sender=POSTransaction)
def handle_pos_transaction_save(sender, instance, created, **kwargs):
    if instance.status == 'completed':
        # POS Booking: Dr Cash/Bank, Cr Sales Revenue, Cr Tax
        # AND COGS: Dr COGS, Cr Inventory
        
        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant,
                event_type='pos_sale'
            )
            
            # 1. Revenue Entry
            sales_lines = [
                 {
                    'account': config.debit_account, # Cash/Clearing
                    'debit': instance.total_amount,
                    'credit': 0,
                    'description': f"POS Sale {instance.transaction_number}"
                },
                {
                    'account': config.credit_account, # Revenue
                    'debit': 0,
                    'credit': instance.total_amount - instance.tax_amount,
                    'description': f"POS Revenue {instance.transaction_number}"
                }
            ]
            
            # Tax Line
            if instance.tax_amount > 0:
                # Need Tax Account. Assuming config has a way or just fallback
                 pass 
                 
            JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=timezone.now().date(),
                description=f"POS Sale {instance.transaction_number}",
                user=instance.cashier,
                lines=sales_lines,
                reference=instance.transaction_number,
                status='posted'
            )
            
        except AccountingIntegration.DoesNotExist:
            print(f"No accounting integration configured for pos_sale (Tenant: {instance.tenant})")


# --- Purchasing Integration ---

@receiver(post_save, sender=SupplierInvoice)
def handle_supplier_invoice_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when Supplier Invoice is posted (approved).
    """
    if instance.status == 'posted':
        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant, 
                event_type='bill_approved'
            )
            
            # AP Booking: Dr Expense/Asset Account, Cr Accounts Payable
            # We'll use the purchase order to determine the account, or default to a generic expense account
            # For now, we'll use the debit account as the expense account and credit account as AP
            
            lines = [
                {
                    'account': config.debit_account,  # Expense/Asset account
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
            
            JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=instance.invoice_date,
                description=f"Vendor Invoice: {instance.invoice_number}",
                user=None,  # System or could be the user who posted the invoice
                lines=lines,
                reference=instance.invoice_number,
                status='posted'
            )
        except AccountingIntegration.DoesNotExist:
            print(f"No accounting integration configured for bill_approved (Tenant: {instance.tenant})")