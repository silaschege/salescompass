from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sale
from loyalty.services import LoyaltyService

@receiver(post_save, sender=Sale)
def handle_sale_accounting_and_loyalty(sender, instance, created, **kwargs):
    """
    Automates IFRS 15 revenue deferral and loyalty point awarding.
    """
    if created:
        # 1. Loyalty Points
        LoyaltyService.award_points(
            customer=instance.account,
            points=int(instance.amount),
            description=f"Points earned for Sale #{instance.id}",
            sale_amount=instance.amount,
            reference=f"SALE-{instance.id}"
        )
        
        # 2. IFRS 15 Revenue Deferral
        from .services_revenue import RevenueRecognitionService
        try:
            RevenueRecognitionService.defer_on_sale(instance)
        except Exception as e:
            # In production, log this error
            pass


# ============================================================================
# REVENUE RECOGNITION ACCOUNTING INTEGRATION (IFRS 15)
# ============================================================================

from accounting.services import JournalService
from accounting.models import AccountingIntegration

@receiver(post_save, sender=Sale)
def handle_revenue_recognition_save(sender, instance, **kwargs):
    """
    Trigger journal entry when revenue is recognized.
    
    Accounting Entry:
    Dr: Accounts Receivable or Cash
    Cr: Revenue Account
    """
    if not instance.is_recognized:
        return
    
    # Check if journal entry already created
    if hasattr(instance, 'journal_entry') and instance.journal_entry:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='revenue_recognition'
        )
        
        lines = [
            {
                'account': config.debit_account,  # AR or Cash
                'debit': instance.amount,
                'credit': 0,
                'description': f"Revenue from Sale: {instance.product.product_name}"
            },
            {
                'account': config.credit_account,  # Revenue
                'debit': 0,
                'credit': instance.amount,
                'description': f"Sale to {instance.account.account_name}"
            }
        ]
        
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.closing_date,
            description=f"Revenue Recognition: Sale #{instance.pk}",
            user=instance.sales_rep.user if instance.sales_rep else None,
            lines=lines,
            reference=f"SALE-{instance.pk}",
            status='posted'
        )
        
        if hasattr(instance, 'journal_entry'):
            instance.journal_entry = journal_entry
            instance._skip_signal = True
            instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for revenue_recognition (Tenant: {instance.tenant})")

