# apps/tasks/utils.py

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Count, Sum
from datetime import timedelta, datetime
import logging

from core.models import User
from .models import Task, TaskAttachment, TaskDependency, TaskTimeEntry, TaskComment, TaskActivity, TaskSharing


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
    if task.lead:
        lead = task.lead

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

        # 5. Handle dependencies - unlock dependent tasks
        unlock_dependent_tasks(task)

        # 6. Handle recurring tasks
        create_next_recurring_task(task)

        # 7. Log completion
        log_task_completion(task, completed_by)

        return True

    except Exception as e:
        logger.error(f"Error in task completion workflow: {e}", exc_info=True)
        return False


# ======================================================================
# RECURRING TASKS
# ======================================================================

def create_next_recurring_task(task):
    """
    Create the next instance of a recurring task when the current one is completed
    """
    if not task.is_recurring or not task.recurrence_pattern_ref:
        return

    # Check if recurrence should continue
    if task.recurrence_end_date and timezone.now().date() > task.recurrence_end_date:
        return

    # Map recurrence pattern to timedelta
    recurrence_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30),  # Approximate
        'quarterly': timedelta(days=90),  # Approximate
        'yearly': timedelta(days=365),  # Approximate
    }

    pattern_name = task.recurrence_pattern_ref.pattern_name
    if pattern_name not in recurrence_map:
        return

    # Calculate next due date
    next_due_date = task.due_date + recurrence_map[pattern_name]

    # Create new recurring task
    new_task = Task.objects.create(
        title=task.title,
        task_description=task.task_description,
        assigned_to=task.assigned_to,
        created_by=task.created_by,
        account=task.account,
        opportunity=task.opportunity,
        lead=task.lead,
        case=task.case,
        priority=task.priority,
        priority_ref=task.priority_ref,
        status='todo',  # New task starts as 'To Do'
        status_ref=task.status_ref,
        task_type=task.task_type,
        task_type_ref=task.task_type_ref,
        due_date=next_due_date,
        is_recurring=task.is_recurring,
        recurrence_pattern=task.recurrence_pattern,
        recurrence_pattern_ref=task.recurrence_pattern_ref,
        recurrence_end_date=task.recurrence_end_date,
        parent_task=task.parent_task,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        tenant_id=task.tenant_id,
    )

    # Create dependencies for the new recurring task
    create_dependencies_for_recurring_task(task, new_task)


def create_dependencies_for_recurring_task(original_task, new_task):
    """
    Create dependencies for the new recurring task based on the original
    """
    # Copy predecessor dependencies
    for dep in original_task.predecessor_dependencies.all():
        TaskDependency.objects.create(
            predecessor=dep.predecessor,  # Original predecessor
            successor=new_task,  # New recurring task
            dependency_type=dep.dependency_type,
            lag_time=dep.lag_time,
            tenant_id=new_task.tenant_id,
        )

    # Copy successor dependencies
    for dep in original_task.successor_dependencies.all():
        TaskDependency.objects.create(
            predecessor=new_task,  # New recurring task
            successor=dep.successor,  # Original successor
            dependency_type=dep.dependency_type,
            lag_time=dep.lag_time,
            tenant_id=new_task.tenant_id,
        )


def process_recurring_tasks():
    """
    Process recurring tasks that need to be created based on their patterns
    """
    from django.db.models import Q
    
    recurring_tasks = Task.objects.filter(
        is_recurring=True,
        status='completed',
        recurrence_end_date__isnull=True  # No end date or end date not reached
    ).exclude(
        recurrence_pattern_ref__isnull=True
    )

    created_count = 0
    for task in recurring_tasks:
        create_next_recurring_task(task)
        created_count += 1

    return created_count


# ======================================================================
# TASK DEPENDENCIES
# ======================================================================

def unlock_dependent_tasks(completed_task):
    """
    Unlock tasks that depend on the completed task
    """
    # Find all tasks that depend on this completed task as a predecessor
    dependent_tasks = TaskDependency.objects.filter(
        predecessor=completed_task
    ).select_related('successor')

    for dependency in dependent_tasks:
        successor_task = dependency.successor
        
        # Check if all predecessors of the successor are completed
        if are_all_predecessors_completed(successor_task):
            # Change status to 'todo' or 'in_progress' based on dependency type
            if successor_task.status_ref:
                # Try to find a 'To Do' status for the tenant
                todo_status = TaskStatus.objects.filter(
                    tenant_id=successor_task.tenant_id,
                    status_name='todo'
                ).first()
                
                if todo_status:
                    successor_task.status_ref = todo_status
                    successor_task.status = 'todo'
                else:
                    # Fallback to first available status
                    first_status = TaskStatus.objects.filter(
                        tenant_id=successor_task.tenant_id
                    ).first()
                    if first_status:
                        successor_task.status_ref = first_status
                        successor_task.status = first_status.status_name
            else:
                # Legacy field
                successor_task.status = 'todo'
            
            successor_task.save(update_fields=['status', 'status_ref'])
            
            # Log activity
            TaskActivity.objects.create(
                task=successor_task,
                user=completed_task.created_by or completed_task.assigned_to,
                activity_type='updated',
                description=f'Task unlocked after dependency {completed_task.title} was completed',
                tenant_id=successor_task.tenant_id,
            )


def are_all_predecessors_completed(task):
    """
    Check if all predecessors of a task are completed
    """
    dependencies = TaskDependency.objects.filter(successor=task).select_related('predecessor')
    
    for dep in dependencies:
        if dep.predecessor.status != 'completed' and dep.predecessor.status_ref.status_name != 'completed':
            return False
    
    return True


def validate_task_dependency(predecessor, successor):
    """
    Validate if a dependency can be created without creating circular dependencies
    """
    if predecessor == successor:
        return False, "A task cannot depend on itself"
    
    # Check for direct circular dependency
    if successor_has_predecessor(successor, predecessor):
        return False, "Creating this dependency would cause a circular dependency"
    
    # Check for indirect circular dependencies
    if would_create_circular_dependency(predecessor, successor):
        return False, "Creating this dependency would cause a circular dependency"
    
    return True, "Valid dependency"


def successor_has_predecessor(successor_task, potential_predecessor):
    """
    Check if a task already has another task as a predecessor (direct check)
    """
    return TaskDependency.objects.filter(
        successor=successor_task,
        predecessor=potential_predecessor
    ).exists()


def would_create_circular_dependency(predecessor, successor):
    """
    Check if creating a dependency would create a circular dependency
    """
    # This is a simplified check - in a real implementation, you might want to do
    # a more thorough graph traversal to detect all possible circular dependencies
    visited = set()
    
    def has_path(from_task, to_task):
        if from_task == to_task:
            return True
        
        if from_task.id in visited:
            return False
        
        visited.add(from_task.id)
        
        # Find all tasks that depend on from_task (successors)
        dependencies = TaskDependency.objects.filter(
            predecessor=from_task
        ).select_related('successor')
        
        for dep in dependencies:
            if has_path(dep.successor, to_task):
                return True
        
        return False
    
    # Check if there's already a path from successor to predecessor
    # If so, adding a dependency from predecessor to successor would create a cycle
    return has_path(successor, predecessor)


# ======================================================================
# SUBTASKS/CHECKLISTS
# ======================================================================

def create_subtask(parent_task, title, description="", assigned_to=None, due_date=None, priority_ref=None):
    """
    Create a subtask for a parent task
    """
    # If no assigned_to is provided, assign to the same person as the parent
    if not assigned_to:
        assigned_to = parent_task.assigned_to
    
    # If no due date is provided, use parent's due date
    if not due_date:
        due_date = parent_task.due_date
    
    # If no priority is provided, use parent's priority
    if not priority_ref:
        priority_ref = parent_task.priority_ref
    
    subtask = Task.objects.create(
        title=title,
        task_description=description,
        assigned_to=assigned_to,
        created_by=parent_task.created_by,
        account=parent_task.account,
        opportunity=parent_task.opportunity,
        lead=parent_task.lead,
        case=parent_task.case,
        priority=parent_task.priority,
        priority_ref=priority_ref,
        status='todo',
        status_ref=parent_task.status_ref,
        task_type='custom',
        task_type_ref=parent_task.task_type_ref,
        due_date=due_date,
        parent_task=parent_task,
        tenant_id=parent_task.tenant_id,
    )
    
    # Log activity
    TaskActivity.objects.create(
        task=parent_task,
        user=parent_task.created_by,
        activity_type='updated',
        description=f'Subtask "{subtask.title}" created',
        tenant_id=parent_task.tenant_id,
    )
    
    return subtask


def get_subtasks(parent_task):
    """
    Get all subtasks for a parent task
    """
    return Task.objects.filter(parent_task=parent_task)


def are_all_subtasks_completed(parent_task):
    """
    Check if all subtasks of a parent task are completed
    """
    subtasks = get_subtasks(parent_task)
    incomplete_subtasks = subtasks.exclude(status='completed').exclude(status_ref__status_name='completed')
    
    return incomplete_subtasks.count() == 0


# ======================================================================
# TIME TRACKING
# ======================================================================

def add_time_entry(task, user, hours_spent, description="", date_logged=None, is_billable=False):
    """
    Add a time entry for a task
    """
    if not date_logged:
        date_logged = timezone.now().date()
    
    time_entry = TaskTimeEntry.objects.create(
        task=task,
        user=user,
        date_logged=date_logged,
        hours_spent=hours_spent,
        description=description,
        is_billable=is_billable,
        tenant_id=task.tenant_id,
    )
    
    # Update actual hours on the task
    update_task_actual_hours(task)
    
    return time_entry


def update_task_actual_hours(task):
    """
    Update the actual hours on a task based on time entries
    """
    total_hours = TaskTimeEntry.objects.filter(task=task).aggregate(
        total=Sum('hours_spent')
    )['total'] or 0
    
    task.actual_hours = total_hours
    task.save(update_fields=['actual_hours'])


def get_task_time_summary(task):
    """
    Get time tracking summary for a task
    """
    time_entries = TaskTimeEntry.objects.filter(task=task)
    
    total_hours = time_entries.aggregate(total=Sum('hours_spent'))['total'] or 0
    billable_hours = time_entries.filter(is_billable=True).aggregate(
        total=Sum('hours_spent')
    )['total'] or 0
    
    return {
        'total_hours': total_hours,
        'billable_hours': billable_hours,
        'non_billable_hours': total_hours - billable_hours,
        'entry_count': time_entries.count()
    }


def get_user_time_entries(user, start_date=None, end_date=None):
    """
    Get time entries for a user, optionally filtered by date range
    """
    queryset = TaskTimeEntry.objects.filter(user=user)
    
    if start_date:
        queryset = queryset.filter(date_logged__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(date_logged__lte=end_date)
    
    return queryset


def get_task_time_entries(task):
    """
    Get all time entries for a specific task
    """
    return TaskTimeEntry.objects.filter(task=task).order_by('-date_logged')


# ======================================================================
# TASK SHARING
# ======================================================================

def share_task_with_user(task, shared_with_user, shared_by, share_level='view', expires_at=None, can_reassign=False):
    """
    Share a task with another user
    """
    task_share = TaskSharing.objects.create(
        task=task,
        shared_with_user=shared_with_user,
        shared_by=shared_by,
        share_level=share_level,
        expires_at=expires_at,
        can_reassign=can_reassign,
        tenant_id=task.tenant_id,
    )
    
    return task_share


def share_task_with_team(task, shared_with_team, shared_by, share_level='view', expires_at=None, can_reassign=False):
    """
    Share a task with a team
    """
    task_share = TaskSharing.objects.create(
        task=task,
        shared_with_team=shared_with_team,
        shared_by=shared_by,
        share_level=share_level,
        expires_at=expires_at,
        can_reassign=can_reassign,
        tenant_id=task.tenant_id,
    )
    
    return task_share


def get_shared_users_and_teams(task):
    """
    Get all users and teams a task is shared with
    """
    shared_with = {
        'users': task.shared_with.filter(shared_with_user__isnull=False).select_related('shared_with_user'),
        'teams': task.shared_with.filter(shared_with_team__isnull=False).select_related('shared_with_team')
    }
    
    return shared_with


def user_can_access_shared_task(user, task):
    """
    Check if a user has access to a shared task
    """
    # Direct assignment
    if task.assigned_to == user or task.created_by == user:
        return True
    
    # Check if task is shared with user
    if TaskSharing.objects.filter(task=task, shared_with_user=user).exists():
        return True
    
    # Check if task is shared with user's team
    # This would require checking if user belongs to any shared teams
    # Implementation would depend on the team model structure
    
    return False


# ======================================================================
# TASK COMMENTS AND MENTIONS
# ======================================================================

def add_task_comment(task, author, content, parent_comment=None, mentioned_users=None):
    """
    Add a comment to a task with optional parent comment and mentioned users
    """
    comment = TaskComment.objects.create(
        task=task,
        author=author,
        content=content,
        parent_comment=parent_comment,
        tenant_id=task.tenant_id,
    )
    
    # Add mentioned users if provided
    if mentioned_users:
        comment.mentioned_users.set(mentioned_users)
    
    # Update comment count on task
    task.comment_count = TaskComment.objects.filter(task=task).count()
    task.save(update_fields=['comment_count'])
    
    # Log activity
    TaskActivity.objects.create(
        task=task,
        user=author,
        activity_type='commented',
        description=f'Comment added: {content[:50]}...',
        tenant_id=task.tenant_id,
    )
    
    return comment


def get_task_comments(task):
    """
    Get all comments for a task
    """
    return TaskComment.objects.filter(task=task, parent_comment__isnull=True).select_related(
        'author'
    ).prefetch_related('replies__author')


def notify_mentioned_users(comment):
    """
    Send notifications to users mentioned in a comment
    """
    mentioned_users = comment.mentioned_users.all()
    
    for user in mentioned_users:
        if user.email:
            send_mail(
                f"You've been mentioned in a task comment",
                f"You were mentioned in a comment on task '{comment.task.title}':\n\n{comment.content}\n\n"
                f"View task: {settings.SITE_URL}/tasks/{comment.task.id}/",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )


# ======================================================================
# BULK OPERATIONS
# ======================================================================

def bulk_update_tasks(task_ids, update_data, user):
    """
    Bulk update multiple tasks
    """
    tasks = Task.objects.filter(id__in=task_ids)
    updated_count = 0
    
    for task in tasks:
        # Update fields based on update_data
        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        task.save()
        updated_count += 1
        
        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=user,
            activity_type='updated',
            description=f'Task updated in bulk operation',
            tenant_id=task.tenant_id,
        )
    
    return updated_count


def bulk_delete_tasks(task_ids, user):
    """
    Bulk delete multiple tasks
    """
    tasks = Task.objects.filter(id__in=task_ids)
    deleted_count = tasks.count()
    
    # Log deletion activities before deletion
    for task in tasks:
        TaskActivity.objects.create(
            task=task,
            user=user,
            activity_type='updated',
            description=f'Task deleted in bulk operation',
            tenant_id=task.tenant_id,
        )
    
    tasks.delete()
    
    return deleted_count


def bulk_assign_tasks(task_ids, assigned_to_user, assigned_by_user):
    """
    Bulk assign multiple tasks to a user
    """
    tasks = Task.objects.filter(id__in=task_ids)
    assigned_count = 0
    
    for task in tasks:
        old_assignee = task.assigned_to
        task.assigned_to = assigned_to_user
        task.save(update_fields=['assigned_to'])
        assigned_count += 1
        
        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=assigned_by_user,
            activity_type='assigned',
            description=f'Task reassigned from {old_assignee.email if old_assignee else "Unassigned"} to {assigned_to_user.email}',
            tenant_id=task.tenant_id,
        )
        
        # Send reassignment notification
        send_task_reassignment_notification(task, old_assignee, assigned_to_user, assigned_by_user)
    
    return assigned_count


# ======================================================================
# SMART DUE DATE SUGGESTIONS
# ======================================================================

def suggest_due_date(task_title, assigned_user=None, task_type=None):
    """
    Suggest a due date based on task characteristics and historical data
    """
    from datetime import timedelta
    
    # Base suggestions based on task type
    base_suggestions = {
        'lead_contact': 1,  # 1 day
        'opportunity_demo': 3,  # 3 days
        'proposal_followup': 5,  # 5 days
        'account_followup': 7,  # 7 days
        'lead_review': 2,  # 2 days
        'custom': 3,  # 3 days default
    }
    
    # Get base suggestion
    days = base_suggestions.get(task_type or 'custom', 3)
    
    # Adjust based on user's workload
    if assigned_user:
        recent_tasks = Task.objects.filter(
            assigned_to=assigned_user,
            due_date__gte=timezone.now(),
            tenant_id=assigned_user.tenant_id
        ).count()
        
        # If user has many tasks, extend the due date
        if recent_tasks > 10:
            days = min(days * 2, 30)  # Don't exceed 30 days
        elif recent_tasks > 5:
            days = min(days * 1.5, 21)  # Don't exceed 21 days
    
    # Avoid weekends if possible
    suggested_date = timezone.now() + timedelta(days=days)
    
    # If the suggested date falls on a weekend, adjust to Monday
    if suggested_date.weekday() >= 5:  # Saturday or Sunday
        days_ahead = 7 - suggested_date.weekday()
        suggested_date += timedelta(days=days_ahead)
    
    return suggested_date


def get_user_productivity_stats(user, tenant_id):
    """
    Calculate user's average task completion time for better suggestions
    """
    completed_tasks = Task.objects.filter(
        assigned_to=user,
        status='completed',
        tenant_id=tenant_id
    ).exclude(completed_at__isnull=True)
    
    if not completed_tasks.exists():
        return {'avg_completion_days': 3, 'reliability_score': 0.7}
    
    total_days = 0
    completed_count = 0
    for task in completed_tasks:
        if task.task_created_at and task.completed_at:
            days = (task.completed_at - task.task_created_at).days
            if days >= 0:  # Only count valid positive durations
                total_days += days
                completed_count += 1
    
    avg_days = total_days / completed_count if completed_count > 0 else 3
    reliability_score = min(1.0, 3.0 / max(avg_days, 1))  # Higher for faster completion
    
    return {
        'avg_completion_days': avg_days,
        'reliability_score': reliability_score,
        'completed_task_count': completed_count
    }


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
    - Description: {task.task_description}

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

    if task.task_type == "lead_qualify" and task.lead:
        lead = task.lead
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
        "title": lambda task: f"Schedule demo for {safe_name(task.lead, 'full_name', 'email')}",
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
        task_description=f"Auto follow-up created from completed task: {task.title}",
        assigned_to=task.assigned_to,
        created_by=task.created_by,
        account=task.account,
        opportunity=task.opportunity,
        lead=task.lead,
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
            title = f"Lead Contacted: {safe_name(task.lead, 'full_name', 'email')}"
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
            # Note: nps_response might not exist in current model
            contact=getattr(task.lead, "contact", None),
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
        completed_at__isnull=False, task_created_at__isnull=False, status="completed"
    )

    avg_time = None
    if completed_tasks.exists():
        total_seconds = 0
        count = 0
        for t in completed_tasks:
            if t.task_created_at and t.completed_at:
                duration = t.completed_at - t.task_created_at
                total_seconds += duration.total_seconds()
                count += 1
        if count > 0:
            avg_seconds = total_seconds / count
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