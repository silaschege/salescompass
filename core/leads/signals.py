from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lead
from automation.tasks import evaluate_assignment_rules
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Lead)
def lead_post_save(sender, instance, created, **kwargs):
    """
    Trigger assignment rules when a new lead is created.
    """
    if created and not instance.owner:
        logger.info(f"Triggering assignment rules for new lead {instance.id}")
        # Call async task
        evaluate_assignment_rules.delay('leads', instance.id)
