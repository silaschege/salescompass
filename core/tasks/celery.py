from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Task
from .utils import send_batch_task_reminders, cleanup_old_task_attachments

@shared_task
def schedule_task_reminder(task_id):
    """
    Celery task to send task reminders.
    This should be scheduled to run at the appropriate time before the task due date.
    """
    try:
        task = Task.objects.get(id=task_id)
        
        if task.reminder_sent or task.status in ['completed', 'cancelled']:
            return "Task reminder already sent or task completed"
            
        # Calculate reminder time
        from datetime import timedelta
        reminder_time = task.due_date - timedelta(minutes=task.reminder_time)
        
        if timezone.now() >= reminder_time:
            # Send reminder now
            send_task_reminder_email(task)
            task.reminder_sent = True
            task.save(update_fields=['reminder_sent'])
            return f"Task reminder sent for task {task_id}"
        else:
            # Schedule the reminder for the correct time
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            import json
            
            # Create interval schedule (runs once at the reminder time)
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=(reminder_time - timezone.now()).total_seconds(),
                period=IntervalSchedule.SECONDS,
            )
            
            PeriodicTask.objects.create(
                interval=schedule,
                name=f'task_reminder_{task_id}',
                task='tasks.tasks.send_task_reminder_email_task',
                args=json.dumps([task_id]),
                one_off=True,
            )
            
        return f"Task reminder scheduled for task {task_id}"
        
    except Task.DoesNotExist:
        return f"Task {task_id} does not exist"
    except Exception as e:
        return f"Error scheduling task reminder: {str(e)}"


@shared_task
def send_task_reminder_email_task(task_id):
    """
    Celery task to send task reminder email.
    """
    try:
        task = Task.objects.get(id=task_id)
        send_task_reminder_email(task)
        task.reminder_sent = True
        task.save(update_fields=['reminder_sent'])
        return f"Task reminder email sent for task {task_id}"
    except Task.DoesNotExist:
        return f"Task {task_id} does not exist"
    except Exception as e:
        return f"Error sending task reminder email: {str(e)}"


def send_task_reminder_email(task):
    """
    Send email reminder for a task.
    """
    if not task.assigned_to or not task.assigned_to.email:
        return
        
    subject = f"Task Reminder: {task.title}"
    message = f"""
    Hi {task.assigned_to.first_name or task.assigned_to.email},

    This is a reminder that your task "{task.title}" is due on {task.due_date.strftime('%Y-%m-%d %H:%M')}.

    Task Details:
    - Priority: {task.get_priority_display()}
    - Type: {task.get_task_type_display()}
    - Description: {task.description}

    Please complete this task as soon as possible.

    Best regards,
    SalesCompass Team
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[task.assigned_to.email],
        fail_silently=True
    )


@shared_task
def create_recurring_tasks():
    """
    Celery task that runs daily to create recurring tasks.
    """
    from datetime import date, timedelta
    
    today = date.today()
    
    # Get all active recurring tasks that need to be created for today
    recurring_tasks = Task.objects.filter(
        is_recurring=True,
        status='completed',
        recurrence_end_date__gte=today
    )
    
    for task in recurring_tasks:
        # Check if we need to create a new instance based on recurrence pattern
        if should_create_recurring_task(task, today):
            create_new_recurring_task_instance(task, today)
            
    return f"Processed {recurring_tasks.count()} recurring tasks"


def should_create_recurring_task(task, today):
    """
    Determine if a new recurring task instance should be created.
    """
    from datetime import timedelta
    
    # Get the last completed instance of this recurring task
    last_instance = Task.objects.filter(
        title=task.title,
        task_type=task.task_type,
        is_recurring=True
    ).exclude(id=task.id).order_by('-completed_at').first()
    
    if not last_instance:
        return True
        
    if task.recurrence_pattern == 'daily':
        return (today - last_instance.completed_at.date()).days >= 1
    elif task.recurrence_pattern == 'weekly':
        return (today - last_instance.completed_at.date()).days >= 7
    elif task.recurrence_pattern == 'monthly':
        return (today.year > last_instance.completed_at.year or 
                (today.year == last_instance.completed_at.year and 
                 today.month > last_instance.completed_at.month))
    elif task.recurrence_pattern == 'quarterly':
        last_quarter = (last_instance.completed_at.month - 1) // 3 + 1
        current_quarter = (today.month - 1) // 3 + 1
        return (today.year > last_instance.completed_at.year or 
                (today.year == last_instance.completed_at.year and 
                 current_quarter > last_quarter))
    elif task.recurrence_pattern == 'yearly':
        return today.year > last_instance.completed_at.year
        
    return False


def create_new_recurring_task_instance(task, today):
    """
    Create a new instance of a recurring task.
    """
    from datetime import timedelta
    
    # Calculate new due date based on recurrence pattern
    if task.recurrence_pattern == 'daily':
        new_due_date = timezone.now() + timedelta(days=1)
    elif task.recurrence_pattern == 'weekly':
        new_due_date = timezone.now() + timedelta(weeks=1)
    elif task.recurrence_pattern == 'monthly':
        # Add one month (approximately)
        new_due_date = timezone.now() + timedelta(days=30)
    elif task.recurrence_pattern == 'quarterly':
        new_due_date = timezone.now() + timedelta(days=90)
    elif task.recurrence_pattern == 'yearly':
        new_due_date = timezone.now() + timedelta(days=365)
    else:
        new_due_date = timezone.now() + timedelta(days=1)
    
    new_task = Task.objects.create(
        title=task.title,
        description=task.description,
        assigned_to=task.assigned_to,
        created_by=task.created_by,
        account=task.account,
        opportunity=task.opportunity,
        related_lead=task.related_lead,
        case=task.case,
        nps_response=task.nps_response,
        engagement_event=task.engagement_event,
        priority=task.priority,
        status='todo',
        task_type=task.task_type,
        due_date=new_due_date,
        is_recurring=task.is_recurring,
        recurrence_pattern=task.recurrence_pattern,
        recurrence_end_date=task.recurrence_end_date,
        reminder_enabled=task.reminder_enabled,
        reminder_time=task.reminder_time,
        estimated_hours=task.estimated_hours,
        tags=task.tags,
        custom_fields=task.custom_fields,
        tenant_id=task.tenant_id
    )
    
    return new_task


@shared_task
def send_daily_task_reminders():
    """Send task reminders daily."""
    return send_batch_task_reminders()

@shared_task
def cleanup_task_attachments():
    """Cleanup old task attachments weekly."""
    return cleanup_old_task_attachments()