from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import EngagementEvent
import logging

logger = logging.getLogger(__name__)

def get_sender_model(label):
    from django.apps import apps
    try:
        return apps.get_model(label)
    except LookupError:
        return None

@receiver(post_save, sender='tasks.Task')
def log_task_engagement(sender, instance, created, **kwargs):
    """Log engagement when a task is created or completed."""
    if created:
        event_type = 'task_assigned'
        desc = f"New task assigned: {instance.title}"
        score = 2.0
    elif instance.status == 'completed' and (not instance.pk or sender.objects.get(pk=instance.pk).status != 'completed'):
        event_type = 'user_followup_completed'
        desc = f"Task completed: {instance.title}"
        score = 5.0
    else:
        return

    # Inherit account_company from related entities if missing
    account_company = instance.account if hasattr(instance, 'account') else None
    lead = instance.lead if hasattr(instance, 'lead') else None
    opportunity = instance.opportunity if hasattr(instance, 'opportunity') else None
    case = instance.case if hasattr(instance, 'case') else None
    contact = getattr(instance, 'contact', None)
    
    if not account_company:
        if case and hasattr(case, 'account'):
            account_company = case.account
        elif lead and hasattr(lead, 'account'):
            account_company = lead.account
        elif opportunity and hasattr(opportunity, 'account'):
            account_company = opportunity.account

    if not contact:
        if case and hasattr(case, 'contact'):
            contact = case.contact
        elif lead and hasattr(lead, 'contact'):
            pass
        elif opportunity and hasattr(opportunity, 'contact'):
            contact = opportunity.contact

    EngagementEvent.objects.create(
        tenant_id=instance.tenant_id,
        account=instance.assigned_to if hasattr(instance, 'assigned_to') else None,
        account_company=account_company,
        opportunity=opportunity,
        lead=lead,
        case=case,
        contact=contact,
        task=instance,
        event_type=event_type,
        description=desc,
        title=instance.title,
        engagement_score=score
    )

@receiver(post_save, sender='leads.Lead')
def log_lead_engagement(sender, instance, created, **kwargs):
    """Log engagement when a lead is created."""
    if created:
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            account=instance.owner,
            lead=instance,
            event_type='lead_created',
            description=f"New lead created: {instance.full_name}",
            title="Lead Created",
            engagement_score=10.0
        )

@receiver(post_save, sender='communication.ChatMessage')
def log_chat_engagement(sender, instance, created, **kwargs):
    """Log engagement for WhatsApp/SMS messages."""
    if created:
        channel = instance.channel.lower()
        if channel == 'whatsapp':
            event_type = 'whatsapp_sent'
            score = 3.0
        else:
            event_type = 'lead_contacted'
            score = 2.0
        
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            event_type=event_type,
            description=f"{instance.channel.capitalize()} message: {instance.message[:100]}",
            title=f"{instance.channel.capitalize()} Interaction",
            metadata={'message_id': instance.id, 'channel': instance.channel},
            engagement_score=score
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
            metadata={'post_id': instance.id},
            engagement_score=4.0
        )

@receiver(post_save, sender='cases.Case')
def log_case_engagement(sender, instance, created, **kwargs):
    """Log engagement for support cases."""
    if created:
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            account=instance.owner if hasattr(instance, 'owner') else None,
            account_company=instance.account if hasattr(instance, 'account') else None,
            case=instance,
            contact=instance.contact if hasattr(instance, 'contact') else None,
            event_type='support_ticket',
            description=f"Support ticket created: {instance.subject}",
            title="Support Case Created",
            engagement_score=5.0
        )

@receiver(post_save, sender='opportunities.Opportunity')
def log_opportunity_engagement(sender, instance, created, **kwargs):
    """Log engagement for opportunity milestones."""
    score = 0.0
    event_type = ''
    desc = ''

    if created:
        event_type = 'opportunity_created'
        desc = f"New opportunity created: {instance.opportunity_name} (${instance.amount})"
        score = 10.0
    elif hasattr(instance, 'stage') and hasattr(instance.stage, 'is_won') and instance.stage.is_won:
        event_type = 'opportunity_won'
        desc = f"Opportunity WON: {instance.opportunity_name} (${instance.amount})"
        score = 50.0  # High score for winning
    elif hasattr(instance, 'stage') and hasattr(instance.stage, 'is_lost') and instance.stage.is_lost:
        event_type = 'opportunity_lost'
        desc = f"Opportunity LOST: {instance.opportunity_name}"
        score = 1.0
    elif hasattr(instance, 'stage'):
         # Generic stage change logic could go here if tracking every move is desired
         # For now, avoiding noise unless requested
         return
    else:
        return

    # Check for duplicates (e.g., if manually logged in view)
    # Using a small time window or key could help, but for now we rely on distinct triggers
    
    EngagementEvent.objects.create(
        tenant_id=instance.tenant_id,
        account=instance.owner,
        account_company=instance.account,
        opportunity=instance,
        contact=instance.contact if hasattr(instance, 'contact') else None,
        event_type=event_type,
        description=desc,
        title=f"Opportunity {instance.opportunity_name}",
        engagement_score=score
    )

@receiver(post_save, sender='sales.Sale')
def log_sale_engagement(sender, instance, created, **kwargs):
    """Log engagement for sales/payments."""
    if created:
        EngagementEvent.objects.create(
            tenant_id=getattr(instance.account, 'tenant_id', None),
            account=instance.account,
            event_type='payment_received',
            description=f"Sale recorded: {instance.product.name} (${instance.amount})",
            title=f"Sale: {instance.product.name}",
            engagement_score=20.0
        )

@receiver(post_save, sender='learn.Certificate')
def log_learning_engagement(sender, instance, created, **kwargs):
    """Log engagement for course completions."""
    if created:
        EngagementEvent.objects.create(
            tenant_id=instance.tenant_id,
            event_type='course_completed',
            description=f"Course completed: {instance.course.title}",
            title=f"Learning: {instance.course.title}",
            engagement_score=15.0
        )
