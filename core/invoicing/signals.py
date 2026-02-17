from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice, Payment
from .services import AccountingIntegrationService

@receiver(post_save, sender=Invoice)
def handle_invoice_posting(sender, instance, created, **kwargs):
    """
    Automatically post to GL when an invoice is moved out of 'draft' status.
    """
    if instance.status != 'draft' and not hasattr(instance, '_gl_posted'):
        AccountingIntegrationService.post_invoice_to_gl(instance)
        # Mark as posted to avoid double posting in the same thread if needed
        instance._gl_posted = True

@receiver(post_save, sender=Payment)
def handle_payment_posting(sender, instance, created, **kwargs):
    """
    Automatically post to GL when a payment is marked as 'completed'.
    """
    if instance.status == 'completed' and not hasattr(instance, '_gl_posted'):
        AccountingIntegrationService.post_payment_to_gl(instance)
        instance._gl_posted = True
