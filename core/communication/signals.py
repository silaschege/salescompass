from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Email, Call, Meeting
from engagement.models import EngagementEvent

@receiver(post_save, sender=Email)
def log_email_engagement(sender, instance, created, **kwargs):
    if created:
        event_type = 'email_opened' if instance.direction == 'inbound' else 'lead_contacted'
        # If it's an account interaction, use account_followup_completed
        if instance.account:
            event_type = 'account_followup_completed'
            
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            account=instance.account,
            contact=instance.contact,
            created_by=instance.owner,
            event_type=event_type,
            title=f"Email: {instance.subject}",
            description=instance.body[:500],  # Truncate for description
            engagement_score=5.0, # Base score for email
            is_important=False
        )

@receiver(post_save, sender=Call)
def log_call_engagement(sender, instance, created, **kwargs):
    if created:
        event_type = 'lead_contacted'
        if instance.account:
            event_type = 'account_followup_completed'
            
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            account=instance.account,
            contact=instance.contact,
            created_by=instance.owner,
            event_type=event_type,
            title=f"Call: {instance.outcome}",
            description=instance.notes[:500],
            engagement_score=10.0, # Higher score for call
            is_important=instance.outcome == 'connected'
        )

@receiver(post_save, sender=Meeting)
def log_meeting_engagement(sender, instance, created, **kwargs):
    if created:
        event_type = 'demo_completed' if 'demo' in instance.title.lower() else 'account_followup_completed'
        
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            account=instance.account,
            contact=instance.contact,
            created_by=instance.owner,
            event_type=event_type,
            title=f"Meeting: {instance.title}",
            description=instance.agenda[:500],
            engagement_score=20.0, # High score for meeting
            is_important=True
        )
