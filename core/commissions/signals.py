from django.db.models.signals import post_save
from django.dispatch import receiver
from opportunities.models import Opportunity
from .utils import calculate_commission
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Opportunity)
def opportunity_commission_signal(sender, instance, created, **kwargs):
    """
    Auto-calculate commission when an Opportunity is marked as Won.
    """
    # Only trigger on update (not create) and when stage is_won
    if not created and instance.stage and instance.stage.is_won:
        # Check if commission already exists for this opportunity and user
        from .models import Commission
        existing = Commission.objects.filter(
            opportunity=instance,
            user=instance.owner
        ).exists()
        
        if not existing:
            commission = calculate_commission(instance)
            if commission:
                commission.tenant = instance.tenant
                commission.save()
                logger.info(f"Created commission {commission.amount} for {instance.owner} on {instance.opportunity_name}")
