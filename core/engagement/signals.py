from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import EngagementEvent
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='tasks.Task')
def log_task_engagement(sender, instance, created, **kwargs):
    """Log engagement when a task is created or completed."""
    if created:
        event_type = 'task_assigned'
        desc = f"New task assigned: {instance.title}"
    elif instance.status == 'completed' and (not instance.pk or sender.objects.get(pk=instance.pk).status != 'completed'):
        event_type = 'user_followup_completed'
        desc = f"Task completed: {instance.title}"
    else:
        return

    EngagementEvent.objects.create(
        tenant_id=instance.tenant_id,
        account=instance.assigned_to if hasattr(instance, 'assigned_to') else None,
        account_company=getattr(instance, 'account_company', None),
        opportunity=instance.opportunity if hasattr(instance, 'opportunity') else None,
        lead=instance.lead if hasattr(instance, 'lead') else None,
        case=instance.case if hasattr(instance, 'case') else None,
        task=instance,
        event_type=event_type,
        description=desc,
        title=instance.title
    )

@receiver(post_save, sender='leads.Lead')
def log_lead_engagement(sender, instance, created, **kwargs):
    """Log engagement when a lead is created or status changes."""
    if created:
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            account=instance.owner,
            lead=instance,
            event_type='lead_created',
            description=f"New lead created: {instance.full_name}",
            title="Lead Created"
        )

@receiver(post_save, sender='communication.ChatMessage')
def log_chat_engagement(sender, instance, created, **kwargs):
    """Log engagement for WhatsApp/SMS messages."""
    if created:
        channel = instance.channel.lower()
        event_type = 'whatsapp_sent' if channel == 'whatsapp' else 'lead_contacted'
        
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            event_type=event_type,
            description=f"{instance.channel.capitalize()} message: {instance.message[:100]}",
            title=f"{instance.channel.capitalize()} Interaction",
            metadata={'message_id': instance.id, 'channel': instance.channel}
        )

@receiver(post_save, sender='communication.SocialMediaPost')
def log_social_engagement(sender, instance, created, **kwargs):
    """Log engagement for LinkedIn InMails."""
    if created and getattr(instance, 'is_inmail', False):
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            lead=instance.lead,
            event_type='linkedin_inmail_tracked',
            description=f"LinkedIn InMail tracked for {instance.url}",
            title="LinkedIn Interaction",
            metadata={'post_id': instance.id}
        )

@receiver(post_save, sender='cases.Case')
def log_case_engagement(sender, instance, created, **kwargs):
    """Log engagement for support cases."""
    if created:
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            account=instance.user if hasattr(instance, 'user') else None,
            account_company=instance.account if hasattr(instance, 'account') else None,
            case=instance,
            event_type='support_ticket',
            description=f"Support ticket created: {instance.subject}",
            title="Support Case Created"
        )

@receiver(post_save, sender='opportunities.Opportunity')
def log_opportunity_engagement(sender, instance, created, **kwargs):
    """Log engagement for opportunity milestones."""
    if created:
        event_type = 'opportunity_created'
        desc = f"New opportunity created: {instance.opportunity_name} (${instance.amount})"
    elif instance.stage.is_won:
        event_type = 'opportunity_won'
        desc = f"Opportunity WON: {instance.opportunity_name} (${instance.amount})"
    elif instance.stage.is_lost:
        event_type = 'opportunity_lost'
        desc = f"Opportunity LOST: {instance.opportunity_name}"
    else:
        return

    EngagementEvent.objects.create(
        tenant_id=instance.tenant_id,
        account=instance.owner,
        account_company=instance.account,
        opportunity=instance,
        event_type=event_type,
        description=desc,
        title=f"Opportunity {instance.opportunity_name}"
    )

@receiver(post_save, sender='sales.Sale')
def log_sale_engagement(sender, instance, created, **kwargs):
    """Log engagement for sales/payments."""
    if created:
        EngagementEvent.objects.create(
            # Sale doesn't have tenant_id directly in the snippet, but let's check
            # Wait, Sale doesn't inherit from TenantAwareModel in the snippet I saw!
            # It inherits from models.Model. I should check if it HAS tenant_id.
            # actually line 6 shows TenantAwareModel as TenantModel, 
            # but Sale (line 66) inherits from models.Model.
            # I'll use getattr(instance, 'tenant_id', None) or get it from account.
            tenant_id=getattr(instance.account, 'tenant_id', None),
            account=instance.account,
            event_type='payment_received',
            description=f"Sale recorded: {instance.product.name} (${instance.amount})",
            title=f"Sale: {instance.product.name}"
        )

@receiver(post_save, sender='learn.Certificate')
def log_learning_engagement(sender, instance, created, **kwargs):
    """Log engagement for course completions."""
    if created:
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            # In learn module, course completion is by a user (the learner).
            # We don't have a direct link to a business account here usually, 
            # but EngagementEvent supports account as a portal user too.
            # If the user is associated with a contact/account (which is common in B2B),
            # we could try to find it. For now, we'll log it for the user.
            event_type='course_completed',
            description=f"Course completed: {instance.course.title}",
            title=f"Learning: {instance.course.title}"
        )
