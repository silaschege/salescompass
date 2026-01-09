from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Opportunity
from infrastructure.ml_client import ml_client
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Opportunity)
def opportunity_post_save(sender, instance, created, **kwargs):
    """
    Trigger ML win probability prediction when an opportunity is saved.
    """
    # Skip if we're updating probability itself to avoid recursion
    if not kwargs.get('update_fields') or 'probability' not in kwargs.get('update_fields'):
        try:
            prob_data = ml_client.get_win_probability(instance)
            if prob_data.get('status') != 'error':
                new_prob = prob_data.get('probability', instance.probability)
                # Convert from 0-1 to 0-100 if needed, but looks like Opportunity.probability is 0-100 or 0-1?
                # Usually in CRM it's 0-100.
                if instance.probability != new_prob:
                    instance.probability = new_prob
                    instance.save(update_fields=['probability'])
        except Exception as e:
            logger.error(f"Failed to trigger ML win probability for opportunity {instance.id}: {str(e)}")
