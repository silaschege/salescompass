from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from engagement.models import EngagementEvent
from .models import Lead

@receiver(post_save, sender=Lead)
def track_lead_created(sender, instance, created, **kwargs):
    """Track new lead creation"""
    if created:
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            lead=instance,
            account=instance.owner if instance.owner else None,
            event_type='lead_created',
            title=f"New Lead: {instance.full_name}",
            description=f"Lead created for {instance.company}",
            engagement_score=10,
            priority='medium'
        )

@receiver(pre_save, sender=Lead)
def track_lead_status_change(sender, instance, **kwargs):
    """Track lead status changes"""
    if instance.pk:
        try:
            old_instance = Lead.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                instance._status_changed = True
                instance._old_status = old_instance.status
        except Lead.DoesNotExist:
            pass

@receiver(post_save, sender=Lead)
def create_lead_status_event(sender, instance, created, **kwargs):
    """Create engagement event for status change"""
    if not created and getattr(instance, '_status_changed', False):
        event_type_map = {
            'contacted': 'lead_contacted',
            'qualified': 'lead_qualified',
            'unqualified': 'lead_unqualified',
            'converted': 'lead_converted'
        }
        event_type = event_type_map.get(instance.status, 'lead_status_changed')
        score_map = {
            'contacted': 15,
            'qualified': 25,
            'unqualified': -5,
            'converted': 50
        }
        
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            lead=instance,
            account=instance.owner if instance.owner else None,
            event_type=event_type,
            title=f"Lead {instance.status.title()}: {instance.full_name}",
            description=f"Lead status changed from {instance._old_status} to {instance.status}",
            engagement_score=score_map.get(instance.status, 10),
            priority='medium'
        )

@receiver(pre_save, sender=Lead)
def track_lead_score_change(sender, instance, **kwargs):
    """Track significant lead score changes"""
    if instance.pk:
        try:
            old_instance = Lead.objects.get(pk=instance.pk)
            score_diff = abs(instance.lead_score - old_instance.lead_score)
            if score_diff >= 20:  # Significant change threshold
                instance._score_changed = True
                instance._old_score = old_instance.lead_score
        except Lead.DoesNotExist:
            pass

@receiver(post_save, sender=Lead)
def create_lead_score_event(sender, instance, created, **kwargs):
    """Create engagement event for significant score change"""
    if not created and getattr(instance, '_score_changed', False):
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            lead=instance,
            account=instance.owner if instance.owner else None,
            event_type='lead_score_changed',
            title=f"Lead Score Updated: {instance.full_name}",
            description=f"Score changed from {instance._old_score} to {instance.lead_score}",
            engagement_score=5,
            priority='low'
        )
