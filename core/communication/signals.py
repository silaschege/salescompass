from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Email, CallLog, SMS, Meeting
from engagement.models import EngagementEvent

@receiver(post_save, sender=Email)
def log_email_engagement(sender, instance, created, **kwargs):
    if created:
        event_type = 'email_opened' if instance.direction == 'inbound' else 'lead_contacted'
        # If it's an account interaction, use account_followup_completed
        if instance.account:
            event_type = 'account_followup_completed'
            
        EngagementEvent.objects.create(
            tenant_id=str(instance.tenant.id) if instance.tenant else None,
            # EngagementEvent.account seems to point to User model based on core/engagement/models.py
            # but usually it should be the CRM Account. I'll map it to the sender for now
            # as per previous implementation, but also supply account and contact if available.
            account=instance.sender, 
            contact=instance.contact,
            created_by=instance.sender,
            event_type=event_type,
            title=f"Email: {instance.subject}",
            engagement_event_description=instance.content_text[:500] if instance.content_text else "",
            engagement_score=5.0, # Base score for email
            is_important=False
        )

@receiver(post_save, sender=CallLog)
def log_call_engagement(sender, instance, created, **kwargs):
    if created:
        event_type = 'lead_contacted'
        if instance.account:
            event_type = 'account_followup_completed'
            
        EngagementEvent.objects.create(
            tenant_id=str(instance.tenant.id) if instance.tenant else None,
            account=instance.user,
            contact=instance.contact,
            created_by=instance.user,
            event_type=event_type,
            title=f"Call: {instance.outcome}",
            engagement_event_description=instance.notes[:500] if instance.notes else "",
            engagement_score=10.0, # Higher score for call
            is_important=instance.outcome == 'answered'
        )

@receiver(post_save, sender=SMS)
def log_sms_engagement(sender, instance, created, **kwargs):
    if created:
        event_type = 'lead_contacted'
        
        EngagementEvent.objects.create(
            tenant_id=str(instance.tenant.id) if instance.tenant else None,
            account=instance.sender,
            contact=instance.contact,
            created_by=instance.sender,
            event_type=event_type,
            title=f"SMS: {instance.recipient_phone}",
            engagement_event_description=instance.message[:500],
            engagement_score=3.0,
            is_important=False
        )

@receiver(post_save, sender=Meeting)
def log_meeting_engagement(sender, instance, created, **kwargs):
    if created:
        event_type = 'demo_completed' if 'demo' in instance.meeting_name.lower() else 'account_followup_completed'
        
        EngagementEvent.objects.create(
            tenant_id=str(instance.tenant.id) if instance.tenant else None,
            account=instance.organizer,
            contact=instance.contact,
            created_by=instance.organizer,
            event_type=event_type,
            title=f"Meeting: {instance.meeting_name}",
            engagement_event_description=instance.meeting_description[:500] if instance.meeting_description else "",
            engagement_score=20.0, # High score for meeting
            is_important=True
        )
