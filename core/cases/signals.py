from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Case, SlaPolicy
from automation.tasks import evaluate_assignment_rules

@receiver(pre_save, sender=Case)
def set_sla_due_date(sender, instance, **kwargs):
    """
    Calculate and set SLA due date based on priority policy.
    Only runs if sla_due is not already set or if priority changes.
    """
    if not instance.sla_due:
        try:
            # Find applicable policy
            policy = SlaPolicy.objects.filter(
                priority=instance.priority,
                tenant_id=instance.tenant_id
            ).first()
            
            # Fallback to default if no specific policy
            hours = 24 # Default
            if policy:
                hours = policy.resolution_hours
            elif instance.priority == 'critical':
                hours = 4
            elif instance.priority == 'high':
                hours = 8
            elif instance.priority == 'medium':
                hours = 24
            else:
                hours = 48
                
            instance.sla_due = timezone.now() + timedelta(hours=hours)
            
        except Exception as e:
            print(f"Error setting SLA: {e}")

@receiver(post_save, sender=Case)
def check_escalation(sender, instance, created, **kwargs):
    """
    Trigger escalation task if high priority case is created.
    """
    if created and instance.priority in ['high', 'critical']:
        instance.create_escalation_task()
        
    # Trigger assignment rules
    if created and not instance.owner:
        evaluate_assignment_rules.delay('cases', instance.id)
