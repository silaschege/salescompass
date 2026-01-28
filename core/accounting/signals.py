from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from billing.models import Invoice, Payment
from pos.models import POSTransaction
from purchasing.models import GoodsReceipt, SupplierInvoice
from .services import JournalService
from .models import AccountingIntegration

# --- Billing Integration ---

@receiver(post_save, sender=Invoice)
def handle_invoice_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when Invoice is finalized (Open) or Paid.
    """
    if instance.status == 'open' and instance.invoice_is_active:
        # AR Booking: Dr Accounts Receivable, Cr Revenue, Cr Tax
        # ... check if already booked to avoid dupes? 
        # For now, simplistic implementation assuming status transition logic handles idempotency or we check existance
        pass 

@receiver(post_save, sender=Payment)
def handle_payment_save(sender, instance, created, **kwargs):
    if instance.status == 'succeeded':
        # Payment Booking: Dr Bank, Cr Accounts Receivable
        # Use AccountingIntegration to find accounts
        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant, 
                event_type='payment_received'
            )
            # Create Journal
            lines = [
                {
                    'account': config.debit_account, # e.g. Bank
                    'debit': instance.amount,
                    'credit': 0,
                    'description': f"Payment for {instance.invoice.invoice_number}"
                },
                {
                    'account': config.credit_account, # e.g. AR
                    'debit': 0,
                    'credit': instance.amount,
                    'description': f"Payment for {instance.invoice.invoice_number}"
                }
            ]
            
            JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=instance.processed_at.date() if instance.processed_at else timezone.now().date(),
                description=f"Payment Received ({instance.pk})",
                user=None, # System
                lines=lines,
                reference=str(instance.pk),
                status='posted'
            )
        except AccountingIntegration.DoesNotExist:
            print(f"No accounting integration configured for payment_received (Tenant: {instance.tenant})")


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
