from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import emit_event

@receiver(post_save, sender='leads.Lead')
def lead_post_save(sender, instance, created, **kwargs):
    trigger_type = 'lead.created' if created else 'lead.updated'
    payload = {
        'lead_id': instance.id,
        'lead_score': instance.lead_score,
        'status': instance.status,
        'source': instance.source_ref.source_name if instance.source_ref else instance.lead_source,
        'tenant_id': instance.tenant_id,
    }
    emit_event(trigger_type, payload)

@receiver(post_save, sender='opportunities.Opportunity')
def opportunity_post_save(sender, instance, created, **kwargs):
    trigger_type = 'opportunity.created' if created else 'opportunity.updated'
    payload = {
        'opportunity_id': instance.id,
        'amount': float(instance.amount) if instance.amount else 0.0,
        'stage': instance.stage.opportunity_stage_name if instance.stage else None,
        'tenant_id': instance.tenant_id,
    }
    emit_event(trigger_type, payload)

@receiver(post_save, sender='cases.Case')
def case_post_save(sender, instance, created, **kwargs):
    trigger_type = 'case.created' if created else 'case.updated'
    payload = {
        'case_id': instance.id,
        'priority': instance.priority,
        'status': instance.status,
        'tenant_id': instance.tenant_id,
    }
    emit_event(trigger_type, payload)

@receiver(post_save, sender='tasks.Task')
def task_post_save(sender, instance, created, **kwargs):
    trigger_type = 'task.created' if created else 'task.updated'
    payload = {
        'task_id': instance.id,
        'priority': instance.priority,
        'status': instance.status,
        'tenant_id': instance.tenant_id,
    }
    emit_event(trigger_type, payload)




@receiver(post_save, sender='engagement.EngagementEvent')
def engagement_event_post_save(sender, instance, created, **kwargs):
    if created:
        trigger_type = 'engagement.event_logged'
        payload = {
            'event_id': instance.id,
            'event_type': instance.event_type,
            'account_id': instance.account_id,
            'engagement_score': instance.engagement_score,
            'tenant_id': instance.tenant_id,
        }
        emit_event(trigger_type, payload)




