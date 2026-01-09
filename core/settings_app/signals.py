from django.db.models.signals import post_save
from django.dispatch import receiver
from leads.models import Lead
from opportunities.models import Opportunity
from cases.models import Case
from .tasks import trigger_webhook

@receiver(post_save, sender=Lead)
def lead_webhook_signal(sender, instance, created, **kwargs):
    """Trigger webhook on Lead creation or update."""
    event_type = 'lead.created' if created else 'lead.updated'
    
    payload = {
        'id': instance.id,
        'first_name': instance.first_name,
        'last_name': instance.last_name,
        'email': instance.email,
        'status': instance.status,
        'source': str(instance.source_ref) if instance.source_ref else None,
        'created_at': instance.lead_acquisition_date.isoformat() if instance.lead_acquisition_date else None,
        'updated_at': instance.updated_at.isoformat() if hasattr(instance, 'updated_at') and instance.updated_at else None
    }
    
    trigger_webhook.delay(event_type, payload, instance.tenant_id)


@receiver(post_save, sender=Opportunity)
def opportunity_webhook_signal(sender, instance, created, **kwargs):
    """Trigger webhook on Opportunity creation or win."""
    if created:
        event_type = 'opportunity.created'
    elif instance.stage.is_won:
        # Check if it was already won to avoid duplicate events?
        # For simplicity, we trigger 'opportunity.won' whenever saved in won stage
        # Ideally we should check if stage changed to won
        event_type = 'opportunity.won'
    else:
        event_type = 'opportunity.updated'
        
    payload = {
        'id': instance.id,
        'name': instance.opportunity_name,
        'amount': float(instance.amount) if instance.amount else 0.0,
        'stage': instance.stage.opportunity_stage_name if instance.stage else None,
        'account': instance.account.account_name if instance.account else None,
        'close_date': str(instance.close_date),
        'created_at': instance.created_at.isoformat() if hasattr(instance, 'created_at') and instance.created_at else None
    }
    
    trigger_webhook.delay(event_type, payload, instance.tenant_id)


@receiver(post_save, sender=Case)
def case_webhook_signal(sender, instance, created, **kwargs):
    """Trigger webhook on Case creation or update."""
    event_type = 'case.created' if created else 'case.updated'
    
    payload = {
        'id': instance.id,
        'subject': instance.subject,
        'status': instance.status,
        'priority': instance.priority,
        'account': instance.account.email if instance.account else None,
        'created_at': instance.created_at.isoformat()
    }
    
    trigger_webhook.delay(event_type, payload, instance.tenant_id)
