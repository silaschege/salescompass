from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Subscription, Invoice, Payment, Plan
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

 

@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after subscription is saved.
    """
    if created:
        # Send welcome email or perform initial setup
        pass
    
    # If subscription status changed to active
    if instance.status == 'active':
        # Generate first invoice if needed
        from .utils import generate_invoice_for_subscription
        # Check if there are any invoices for this subscription already
        if not instance.invoices.exists():
            generate_invoice_for_subscription(instance)
    
    # If subscription was cancelled
    if instance.status == 'canceled':
        # Handle cancellation processes
        pass



@receiver(post_save, sender=Invoice)
def invoice_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after invoice is saved.
    """
    if created:
        # Send invoice notification
        pass
     
    # If invoice is marked as paid
    if instance.status == 'paid':
        # Update related subscription if needed
        if instance.subscription:
            # Update subscription end date based on payment
            pass


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after payment is saved.
    """
    if created and instance.status == 'succeeded':
        # Update invoice status if payment covers full amount
        if instance.invoice:
            # If payment amount equals or exceeds invoice amount, mark as paid
            if instance.amount >= instance.invoice.amount:
                instance.invoice.status = 'paid'
                instance.invoice.save()
@receiver(post_save, sender=Plan)
def plan_post_save(sender, instance, created, **kwargs):
    """
    Sync module/feature access records whenever a plan is saved.
    """
    from .plan_access_service import PlanAccessService
    PlanAccessService.sync_plan_access(instance)
