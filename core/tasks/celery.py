from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Task, TaskDependency, TaskTimeEntry, TaskComment, TaskSharing, TaskActivity
from .utils import send_batch_task_reminders, cleanup_old_task_attachments, process_recurring_tasks

@shared_task
def schedule_task_reminder(task_id):
    """
    Celery task to send task reminders.
    This should be scheduled to run at the appropriate time before the task due date.
    """
    try:
        task = Task.objects.get(id=task_id)
        
        # Check if task has reminder_enabled and has not been sent
        if hasattr(task, 'reminder_enabled') and task.reminder_enabled and not task.reminder_sent:
            # Calculate reminder time (assuming there's a reminder_time field or default to 24 hours before)
            from datetime import timedelta
            reminder_time = task.due_date - timedelta(hours=24)  # Default to 24 hours before
            
            # If reminder_time field exists in model, use that instead
            if hasattr(task, 'reminder_time'):
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
                    every=int((reminder_time - timezone.now()).total_seconds()),
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
    - Priority: {task.priority_ref.label if task.priority_ref else task.get_priority_display()}
    - Type: {task.task_type_ref.label if task.task_type_ref else task.get_task_type_display()}
    - Description: {task.task_description}

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
    
    # Use the utility function to process recurring tasks
    created_count = process_recurring_tasks()
    
    return f"Processed {created_count} recurring tasks"


@shared_task
def process_task_dependencies():
    """
    Celery task to check and update task dependencies.
    """
    from django.db.models import Q
    
    # Find all tasks that are completed and may unlock dependent tasks
    completed_tasks = Task.objects.filter(status='completed').select_related(
        'status_ref'
    ).filter(
        Q(status_ref__status_name='completed') | Q(status_ref__isnull=True)
    )
    
    processed_count = 0
    for task in completed_tasks:
        # This will trigger the workflow to unlock dependent tasks
        from .utils import unlock_dependent_tasks
        unlock_dependent_tasks(task)
        processed_count += 1
    
    return f"Processed dependencies for {processed_count} completed tasks"


@shared_task
def send_daily_task_reminders():
    """Send task reminders daily."""
    return send_batch_task_reminders()


@shared_task
def cleanup_task_attachments():
    """Cleanup old task attachments weekly."""
    return cleanup_old_task_attachments()


@shared_task
def check_overdue_tasks():
    """
    Celery task to check for overdue tasks and update their status.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Get all tasks that are not completed and are past due
    overdue_tasks = Task.objects.filter(
        status__in=['todo', 'in_progress'],
        due_date__lt=timezone.now(),
        tenant_id__isnull=False
    ).select_related('status_ref')
    
    updated_count = 0
    for task in overdue_tasks:
        # Check if the status is already 'overdue' to avoid unnecessary updates
        if task.status != 'overdue':
            if not task.status_ref or task.status_ref.status_name != 'overdue':
                task.status = 'overdue'
                
                # Find the 'overdue' status for this tenant
                overdue_status = task.tenant.taskstatus_set.filter(status_name='overdue').first()
                if overdue_status:
                    task.status_ref = overdue_status
                    task.status = 'overdue'
                
                task.save(update_fields=['status', 'status_ref'])
                
                # Log activity
                TaskActivity.objects.create(
                    task=task,
                    user=task.assigned_to or task.created_by,
                    activity_type='updated',
                    description='Task marked as overdue',
                    tenant_id=task.tenant_id
                )
                updated_count += 1
    
    return f"Updated {updated_count} overdue tasks"


@shared_task
def calculate_task_time_tracking():
    """
    Celery task to recalculate actual hours on tasks based on time entries.
    """
    from django.db.models import Sum, Q
    
    # Get all tasks that have time entries
    tasks_with_time = Task.objects.annotate(
        total_time=Sum('time_entries__hours_spent')
    ).filter(total_time__isnull=False)
    
    updated_count = 0
    for task in tasks_with_time:
        total_hours = TaskTimeEntry.objects.filter(task=task).aggregate(
            total=Sum('hours_spent')
        )['total'] or 0
        
        if task.actual_hours != total_hours:
            task.actual_hours = total_hours
            task.save(update_fields=['actual_hours'])
            updated_count += 1
    
    return f"Updated actual hours for {updated_count} tasks"


@shared_task
def send_task_sharing_notifications():
    """
    Celery task to send notifications for task sharing that is about to expire.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Find task shares that will expire in the next 24 hours
    tomorrow = timezone.now() + timedelta(days=1)
    expiring_shares = TaskSharing.objects.filter(
        expires_at__isnull=False,
        expires_at__gte=timezone.now(),
        expires_at__lte=tomorrow
    )
    
    notified_count = 0
    for share in expiring_shares:
        if share.shared_with_user and share.shared_with_user.email:
            subject = f"Task sharing access expiring soon: {share.task.title}"
            message = f"""
            Hi {share.shared_with_user.first_name or share.shared_with_user.email},
            
            Your access to task "{share.task.title}" will expire on {share.expires_at.strftime('%Y-%m-%d %H:%M')}.
            
            If you need continued access, please contact the person who shared this task with you.
            
            Best regards,
            SalesCompass Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[share.shared_with_user.email],
                fail_silently=True
            )
            notified_count += 1
    
    return f"Sent {notified_count} sharing expiration notifications"


@shared_task
def cleanup_expired_task_shares():
    """
    Celery task to remove expired task shares.
    """
    from django.utils import timezone
    
    # Find task shares that have expired
    expired_shares = TaskSharing.objects.filter(
        expires_at__isnull=False,
        expires_at__lt=timezone.now()
    )
    
    deleted_count = expired_shares.count()
    expired_shares.delete()
    
    return f"Removed {deleted_count} expired task shares"