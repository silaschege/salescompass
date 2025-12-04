# apps/tasks/utils.py

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Count
from datetime import timedelta
import logging

from core.models import User
from .models import Task, TaskAttachment


logger = logging.getLogger(__name__)


# ======================================================================
# SAFE HELPERS
# ======================================================================

def safe_name(obj, *fields, default="Unknown"):
    """
    Safely resolve a display name from any object.
    Tries each field in order and falls back to default.
    """
    if not obj:
        return default

    for field in fields:
        value = getattr(obj, field, None)
        if callable(value):
            value = value()
        if value:
            return str(value)

    return default


def get_account_for_task(task):
    from accounts.models import Account

    # 1. Direct account on task
    if task.account:
        return task.account

    # 2. Lead account or auto-create
    if task.related_lead:
        lead = task.related_lead

        if lead.account:
            return lead.account

        # Auto-create account for the lead
        account, _ = Account.objects.get_or_create(
            name=lead.company,
            defaults={
                "industry": lead.industry,
                "owner": lead.owner,
                "tenant_id": lead.tenant_id,
            }
        )
        return account

    # 3. Opportunity
    if task.opportunity and task.opportunity.account:
        return task.opportunity.account

    # 4. Case
    if task.case and task.case.account:
        return task.case.account

    return None



# ======================================================================
# MAIN: Task Completion Workflow
# ======================================================================

def trigger_task_completion_workflows(task, completed_by=None):
    """
    Main workflow executed whenever a task is completed.
    """

    try:
        # 1. Notify creator
        if task.created_by and task.created_by != completed_by:
            send_task_completion_notification(task, completed_by)

        # 2. Update related objects
        handle_related_object_updates(task)

        # 3. Auto follow-up tasks
        create_follow_up_tasks(task)

        # 4. Engagement Hub Events
        create_engagement_hub_events(task, completed_by)

        # 5. Log completion
        log_task_completion(task, completed_by)

        return True

    except Exception as e:
        logger.error(f"Error in task completion workflow: {e}", exc_info=True)
        return False


# ======================================================================
# NOTIFICATIONS
# ======================================================================

def send_task_completion_notification(task, completed_by=None):
    if not (task.created_by and task.created_by.email):
        return

    completed_by_name = completed_by.email if completed_by else "System"

    subject = f"Task Completed: {task.title}"
    message = f"""
    Hi {safe_name(task.created_by, 'first_name', 'email')},

    The task "{task.title}" has been completed by {completed_by_name}.

    Task Details:
    - Priority: {task.get_priority_display()}
    - Type: {task.get_task_type_display()}
    - Due Date: {task.due_date}
    - Completed: {timezone.now()}
    - Description: {task.description}

    View task: {settings.SITE_URL}/tasks/{task.id}/

    Best regards,
    SalesCompass Team
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [task.created_by.email],
        fail_silently=True,
    )


# ======================================================================
# RELATED OBJECT UPDATES
# ======================================================================

def handle_related_object_updates(task):
    """
    Update CRM objects based on task type.
    """

    if task.task_type == "lead_qualify" and task.related_lead:
        lead = task.related_lead
        if getattr(lead, "status", None) != "qualified":
            lead.status = "qualified"
            lead.save(update_fields=["status"])

    elif task.task_type == "opportunity_demo" and task.opportunity:
        opp = task.opportunity
        if getattr(opp, "stage", None) == "qualification":
            opp.stage = "proposal"
            opp.save(update_fields=["stage"])

    elif task.task_type == "case_escalation" and task.case:
        case = task.case
        if case.status == "open":
            case.status = "in_progress"
            case.save(update_fields=["status"])


# ======================================================================
# FOLLOW-UP TASKS
# ======================================================================

FOLLOWUP_MAP = {
    "lead_qualify": {
        "task_type": "opportunity_demo",
        "priority": "high",
        "days_offset": 1,
        "title": lambda task: f"Schedule demo for {safe_name(task.related_lead, 'full_name', 'email')}",
    },
    "opportunity_demo": {
        "task_type": "proposal_followup",
        "priority": "high",
        "days_offset": 2,
        "title": lambda task: f"Send proposal for {safe_name(task.opportunity, 'name')}",
    },
    "proposal_followup": {
        "task_type": "account_followup",
        "priority": "medium",
        "days_offset": 3,
        "title": lambda task: f"Follow up on proposal for {safe_name(task.opportunity, 'name')}",
    }
}


def create_follow_up_tasks(task):
    config = FOLLOWUP_MAP.get(task.task_type)
    if not config or not task.assigned_to:
        return

    Task.objects.create(
        title=config["title"](task),
        description=f"Auto follow-up created from completed task: {task.title}",
        assigned_to=task.assigned_to,
        created_by=task.created_by,
        account=task.account,
        opportunity=task.opportunity,
        related_lead=task.related_lead,
        case=task.case,
        priority=config["priority"],
        task_type=config["task_type"],
        due_date=timezone.now() + timedelta(days=config["days_offset"]),
        tenant_id=task.tenant_id,
    )


# ======================================================================
# ENGAGEMENT EVENTS (FULLY NULL-SAFE)
# ======================================================================

def create_engagement_hub_events(task, completed_by=None):
    """
    Create EngagementEvent safely for tasks.
    """
    try:
        from engagement.models import EngagementEvent

        account = get_account_for_task(task)

        if not account:
            logger.warning(
                f"[ENGAGEMENT] Cannot create event for task {task.id}: no account found."
            )
            return

        # ----- Determine Event Metadata -----

        task_type = task.task_type
        actor = completed_by.email if completed_by else "System"

        title = f"Task Completed: {task.title}"
        description = f'Task "{task.title}" completed by {actor}'
        priority = "low"
        score = 40.0

        if task_type == "lead_contact":
            title = f"Lead Contacted: {safe_name(task.related_lead, 'full_name', 'email')}"
            description = f"Lead contacted by {actor}"
            priority = "medium"
            score = 60.0

        elif task_type == "account_followup":
            title = f"Account Follow-up: {safe_name(account, 'name')}"
            description = f"Follow-up completed for account {safe_name(account, 'name')}"
            priority = "medium"
            score = 50.0

        elif task_type == "opportunity_demo":
            title = f"Demo Completed: {safe_name(task.opportunity, 'name')}"
            description = (
                f"Demo completed for {safe_name(task.opportunity, 'name')} at "
                f"{safe_name(account, 'name')}"
            )
            priority = "high"
            score = 75.0

        elif task_type == "case_escalation":
            title = f"Case Escalation: {safe_name(task.case, 'subject')}"
            description = f"Escalated case handled for {safe_name(account, 'name')}"
            priority = "high"
            score = 70.0

        # ---- Create Event ----

        event = EngagementEvent.objects.create(
            account=account,
            opportunity=task.opportunity,
            case=task.case,
            nps_response=task.nps_response,
            contact=getattr(task.related_lead, "contact", None),
            event_type=f"task_{task.task_type}_completed",
            title=title,
            description=description,
            created_by=completed_by,
            tenant_id=task.tenant_id,
            priority=priority,
            is_important=True,
            engagement_score=score,
            metadata={
                "task_id": task.id,
                "task_type": task.task_type,
                "completed_by": actor,
            },
        )

        create_next_best_action_from_engagement(event, task, completed_by)

    except Exception as e:
        logger.error(f"Error creating Engagement Hub event: {e}", exc_info=True)


# ======================================================================
# NEXT BEST ACTION
# ======================================================================

NBA_MAP = {
    "task_lead_contact_completed": ("send_proposal", "Send proposal to lead", 2),
    "task_account_followup_completed": ("check_in", "Check-in after follow-up", 7),
    "task_opportunity_demo_completed": ("send_proposal", "Send proposal post-demo", 1),
    "task_case_escalation_completed": ("check_in", "Follow up after case resolution", 3),
}


def create_next_best_action_from_engagement(event, task, completed_by):
    try:
        from engagement.models import NextBestAction

        if event.event_type not in NBA_MAP:
            return

        action_type, desc, offset = NBA_MAP[event.event_type]

        NextBestAction.objects.create(
            account=event.account,
            contact=event.contact,
            action_type=action_type,
            description=desc,
            due_date=timezone.now() + timedelta(days=offset),
            assigned_to=task.assigned_to,
            priority="high" if offset <= 3 else "medium",
            status="open",
            engagement_event=event,
            tenant_id=task.tenant_id,
        )

    except Exception as e:
        logger.error(f"Error creating Next Best Action: {e}", exc_info=True)


# ======================================================================
# LOG COMPLETION
# ======================================================================

def log_task_completion(task, completed_by=None):
    if not task.completed_at:
        task.completed_at = timezone.now()
    task.save(update_fields=["completed_at"])


# ======================================================================
# STATS / REPORTING
# ======================================================================

def get_user_task_statistics(user, tenant_id=None):
    if tenant_id is None:
        tenant_id = getattr(user, "tenant_id", None)

    tasks = Task.objects.filter(assigned_to=user, tenant_id=tenant_id)

    total = tasks.count()
    completed = tasks.filter(status="completed").count()
    overdue = tasks.filter(
        status__in=["todo", "in_progress"],
        due_date__lt=timezone.now(),
    ).count()

    completion_rate = round((completed / total * 100) if total else 0, 2)

    completed_tasks = tasks.filter(
        completed_at__isnull=False, created_at__isnull=False, status="completed"
    )

    avg_time = None
    if completed_tasks.exists():
        total_seconds = sum(
            (t.completed_at - t.created_at).total_seconds() for t in completed_tasks
        )
        avg_seconds = total_seconds / completed_tasks.count()
        avg_time = str(timedelta(seconds=avg_seconds))

    priority_breakdown = dict(
        tasks.values("priority").annotate(count=Count("priority")).values_list("priority", "count")
    )

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "overdue_tasks": overdue,
        "completion_rate": completion_rate,
        "avg_completion_time": avg_time,
        "priority_breakdown": priority_breakdown,
    }


# ======================================================================
# REMINDERS
# ======================================================================

def get_task_reminder_recipients():
    reminder_time = timezone.now() + timedelta(minutes=30)

    return Task.objects.filter(
        reminder_enabled=True,
        reminder_sent=False,
        due_date__lte=reminder_time,
        status__in=["todo", "in_progress"],
    )


def send_task_reminder_email(task):
    if not (task.assigned_to and task.assigned_to.email):
        return

    subject = f"Task Reminder: {task.title}"
    message = f"""
    Hi {safe_name(task.assigned_to, 'first_name', 'email')},

    Reminder: Your task "{task.title}" is due on {task.due_date}.

    Priority: {task.get_priority_display()}
    Type: {task.get_task_type_display()}

    Best regards,
    SalesCompass Team
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [task.assigned_to.email],
        fail_silently=True,
    )


def send_batch_task_reminders():
    tasks = get_task_reminder_recipients()
    for task in tasks:
        send_task_reminder_email(task)
        task.reminder_sent = True
        task.save(update_fields=["reminder_sent"])
    return tasks.count()


# ======================================================================
# REASSIGNMENT
# ======================================================================

def assign_task_to_user(task_id, new_user_id, assigned_by=None):
    try:
        task = Task.objects.get(id=task_id)
        new_user = User.objects.get(id=new_user_id)
        old_user = task.assigned_to

        task.assigned_to = new_user
        task.save(update_fields=["assigned_to"])

        send_task_reassignment_notification(task, old_user, new_user, assigned_by)
        return True

    except (Task.DoesNotExist, User.DoesNotExist):
        return False


def send_task_reassignment_notification(task, old_user, new_user, assigned_by):
    assigned_by_name = safe_name(assigned_by, "email")

    if new_user and new_user.email:
        send_mail(
            f"Task Assigned: {task.title}",
            f"You have been assigned task '{task.title}' by {assigned_by_name}.",
            settings.DEFAULT_FROM_EMAIL,
            [new_user.email],
            fail_silently=True,
        )

    if old_user and old_user != new_user and old_user.email:
        send_mail(
            f"Task Reassigned: {task.title}",
            f"The task '{task.title}' has been reassigned to {safe_name(new_user, 'email')}.",
            settings.DEFAULT_FROM_EMAIL,
            [old_user.email],
            fail_silently=True,
        )


# ======================================================================
# ATTACHMENTS CLEANUP
# ======================================================================

def cleanup_old_task_attachments(days=30):
    cutoff = timezone.now() - timedelta(days=days)
    old = TaskAttachment.objects.filter(created_at__lt=cutoff)
    count = old.count()
    old.delete()
    return count

