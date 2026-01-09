# In signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Q
from .models import Task, TaskComment, TaskAttachment, TaskDependency, TaskTimeEntry, TaskActivity, TaskSharing, TaskTemplate
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum


@receiver(post_save, sender=Task)
def log_task_activity(sender, instance, created, **kwargs):
    if created:
        TaskActivity.objects.create(
            task=instance,
            user=instance.created_by,
            activity_type='created',
            description=f"Task '{instance.title}' was created",
            tenant_id=instance.tenant_id
        )
    else:
        # Log update activity (could be enhanced to track specific field changes)
        TaskActivity.objects.create(
            task=instance,
            user=instance.assigned_to or instance.created_by,  # Use assigned user or creator
            activity_type='updated',
            description=f"Task '{instance.title}' was updated",
            tenant_id=instance.tenant_id
        )


@receiver(post_save, sender=TaskComment)
def log_comment_activity(sender, instance, created, **kwargs):
    if created:
        TaskActivity.objects.create(
            task=instance.task,
            user=instance.author,
            activity_type='commented',
            description=f"{instance.author.email} added a comment",
            metadata={'comment_id': instance.id},
            tenant_id=instance.tenant_id
        )


@receiver(post_save, sender=TaskAttachment)
def log_attachment_activity(sender, instance, created, **kwargs):
    if created:
        TaskActivity.objects.create(
            task=instance.task,
            user=instance.uploaded_by,
            activity_type='attachment_added',
            description=f"{instance.uploaded_by.email} added an attachment: {instance.filename}",
            metadata={'filename': instance.filename},
            tenant_id=instance.tenant_id
        )


@receiver(post_save, sender=TaskDependency)
def log_dependency_activity(sender, instance, created, **kwargs):
    if created:
        TaskActivity.objects.create(
            task=instance.successor,  # Log activity on the dependent task
            user=instance.tenant.created_by if hasattr(instance.tenant, 'created_by') else None,
            activity_type='dependency_added',
            description=f"Dependency added: {instance.predecessor.title} -> {instance.successor.title}",
            metadata={
                'dependency_type': instance.dependency_type,
                'predecessor_id': instance.predecessor.id,
                'successor_id': instance.successor.id
            },
            tenant_id=instance.tenant_id
        )


@receiver(post_save, sender=TaskTimeEntry)
def update_task_actual_hours(sender, instance, created, **kwargs):
    """
    Update the actual hours on the task when a time entry is added or modified.
    """
    task = instance.task
    
    # Calculate total hours from all time entries for this task
    total_hours = TaskTimeEntry.objects.filter(task=task).aggregate(
        total=Sum('hours_spent')
    )['total'] or 0
    
    # Update the task's actual hours
    task.actual_hours = total_hours
    task.save(update_fields=['actual_hours'])


@receiver(post_save, sender=TaskTimeEntry)
def log_time_entry_activity(sender, instance, created, **kwargs):
    """
    Log activity when a time entry is added or updated.
    """
    activity_type = 'updated' if not created else 'updated'  # Time entries are a form of task update
    description = f"{instance.user.email} logged {instance.hours_spent} hours"
    
    if instance.description:
        description += f": {instance.description}"
    
    TaskActivity.objects.create(
        task=instance.task,
        user=instance.user,
        activity_type=activity_type,
        description=description,
        metadata={
            'time_entry_id': instance.id,
            'hours_spent': float(instance.hours_spent),
            'date_logged': instance.date_logged.isoformat() if instance.date_logged else None,
            'is_billable': instance.is_billable
        },
        tenant_id=instance.tenant_id
    )


@receiver(post_save, sender=TaskComment)
def update_task_comment_count(sender, instance, created, **kwargs):
    """
    Update the comment count on the task when a comment is added or deleted.
    """
    if created:
        # Update comment count on the task
        task = instance.task
        task.comment_count = TaskComment.objects.filter(task=task).count()
        task.save(update_fields=['comment_count'])


@receiver(post_delete, sender=TaskComment)
def update_task_comment_count_on_delete(sender, instance, **kwargs):
    """
    Update the comment count on the task when a comment is deleted.
    """
    task = instance.task
    task.comment_count = TaskComment.objects.filter(task=task).count()
    task.save(update_fields=['comment_count'])


@receiver(post_save, sender=Task)
def handle_task_status_change(sender, instance, created, **kwargs):
    """
    Handle task status changes, particularly for triggering workflows when a task is completed.
    """
    # Check if the status is being changed to 'completed'
    if not created:
        # Get the old instance from the database to compare status
        old_instance = Task.objects.filter(id=instance.id).first()
        if old_instance and old_instance.status != 'completed' and instance.status == 'completed':
            # Trigger completion workflows
            from .utils import trigger_task_completion_workflows
            trigger_task_completion_workflows(instance, completed_by=instance.assigned_to)


@receiver(post_save, sender=TaskSharing)
def send_task_sharing_notification(sender, instance, created, **kwargs):
    """
    Send notification when a task is shared with a user or team.
    """
    if created and (instance.shared_with_user or instance.shared_with_team):
        # Determine the recipient for notification
        recipient_email = None
        recipient_name = None
        
        if instance.shared_with_user:
            recipient_email = instance.shared_with_user.email
            recipient_name = instance.shared_with_user.first_name or instance.shared_with_user.email
        
        # For team sharing, we might want to notify team members
        # For now, we'll skip team notifications to avoid spam
        
        if recipient_email:
            subject = f"Task shared with you: {instance.task.title}"
            message = f"""
            Hi {recipient_name},
            
            The task "{instance.task.title}" has been shared with you by {instance.shared_by.email}.
            
            Share level: {instance.get_share_level_display()}
            Shared at: {instance.shared_at}
            Expires at: {instance.expires_at if instance.expires_at else 'Never'}
            
            You can view the task at: {settings.SITE_URL}/tasks/{instance.task.id}/
            
            Best regards,
            SalesCompass Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=True
            )


@receiver(post_save, sender=Task)
def check_task_overdue_status(sender, instance, created, **kwargs):
    """
    Check if a task has become overdue and update its status accordingly.
    """
    from django.utils import timezone
    
    # Only check for non-completed tasks
    if instance.status not in ['completed', 'cancelled', 'overdue']:
        if instance.due_date and instance.due_date < timezone.now():
            # Update to overdue status if the due date has passed
            overdue_status = instance.tenant.taskstatus_set.filter(
                Q(status_name='overdue') | Q(label='Overdue')
            ).first()
            
            if overdue_status:
                instance.status_ref = overdue_status
                instance.status = 'overdue'
                instance.save(update_fields=['status', 'status_ref'])
                
                # Log the overdue activity
                TaskActivity.objects.create(
                    task=instance,
                    user=instance.assigned_to or instance.created_by,
                    activity_type='updated',
                    description='Task marked as overdue',
                    tenant_id=instance.tenant_id
                )


@receiver(post_save, sender=TaskComment)
def notify_mentioned_users(sender, instance, created, **kwargs):
    """
    Notify users mentioned in a task comment.
    """
    if created and instance.mentioned_users.exists():
        from .utils import notify_mentioned_users as notify_utility
        
        # Use the utility function to notify mentioned users
        notify_utility(instance)


@receiver(post_save, sender=Task)
def handle_recurring_task_completion(sender, instance, created, **kwargs):
    """
    Handle recurring task completion - create next instance if needed.
    """
    if not created and instance.status == 'completed' and instance.is_recurring:
        from .utils import create_next_recurring_task
        create_next_recurring_task(instance)


@receiver(post_save, sender=Task)
def handle_task_dependency_unlock(sender, instance, created, **kwargs):
    """
    Handle unlocking dependent tasks when a task is completed.
    """
    if not created and instance.status == 'completed':
        from .utils import unlock_dependent_tasks
        unlock_dependent_tasks(instance)


@receiver(post_save, sender=TaskComment)
def process_comment_mentions(sender, instance, created, **kwargs):
    """
    Process mentions in comments and add mentioned users to the mentioned_users field.
    """
    if created:
        import re
        from core.models import User
        
        # Extract email mentions from the comment content
        mentioned_emails = re.findall(r'@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', instance.content)
        
        for email in mentioned_emails:
            try:
                user = User.objects.get(email=email, tenant_id=instance.tenant_id)
                instance.mentioned_users.add(user)
            except User.DoesNotExist:
                continue


@receiver(post_save, sender=Task)
def update_subtask_parent_status(sender, instance, created, **kwargs):
    """
    Update parent task status when subtask is completed.
    """
    if not created and instance.parent_task:
        # If all subtasks are completed, update parent status
        from .utils import are_all_subtasks_completed
        
        if are_all_subtasks_completed(instance.parent_task):
            # Update parent task status to completed if all subtasks are done
            completed_status = instance.parent_task.tenant.taskstatus_set.filter(
                Q(status_name='completed') | Q(label='Completed')
            ).first()
            
            if completed_status:
                instance.parent_task.status_ref = completed_status
                instance.parent_task.status = 'completed'
                instance.parent_task.save(update_fields=['status', 'status_ref'])
                
                # Log activity
                TaskActivity.objects.create(
                    task=instance.parent_task,
                    user=instance.assigned_to or instance.created_by,
                    activity_type='updated',
                    description='Parent task marked as completed as all subtasks are done',
                    tenant_id=instance.parent_task.tenant_id
                )


@receiver(post_save, sender=TaskTimeEntry)
def update_task_time_tracking(sender, instance, created, **kwargs):
    """
    Update task time tracking statistics when a time entry is added/modified.
    """
    # Already handled in update_task_actual_hours, but can add additional logic here if needed
    pass


@receiver(post_delete, sender=TaskTimeEntry)
def update_task_actual_hours_on_delete(sender, instance, **kwargs):
    """
    Update the actual hours on the task when a time entry is deleted.
    """
    task = instance.task
    
    # Calculate total hours from all remaining time entries for this task
    total_hours = TaskTimeEntry.objects.filter(task=task).aggregate(
        total=Sum('hours_spent')
    )['total'] or 0
    
    # Update the task's actual hours
    task.actual_hours = total_hours
    task.save(update_fields=['actual_hours'])


@receiver(post_delete, sender=TaskAttachment)
def log_attachment_deletion_activity(sender, instance, **kwargs):
    """
    Log activity when an attachment is deleted.
    """
    TaskActivity.objects.create(
        task=instance.task,
        user=instance.uploaded_by,  # Assuming we can access the original uploader
        activity_type='updated',
        description=f"Attachment '{instance.filename}' was deleted",
        metadata={'filename': instance.filename, 'file_size': instance.file_size},
        tenant_id=instance.tenant_id
    )


@receiver(post_save, sender=Task)
def handle_subtask_creation(sender, instance, created, **kwargs):
    """
    Handle logic when a subtask is created or updated.
    """
    if created and instance.parent_task:
        # Log activity on parent task
        TaskActivity.objects.create(
            task=instance.parent_task,
            user=instance.created_by,
            activity_type='updated',
            description=f'Subtask "{instance.title}" was created',
            metadata={'subtask_id': instance.id},
            tenant_id=instance.parent_task.tenant_id
        )


@receiver(post_delete, sender=Task)
def log_task_deletion_activity(sender, instance, **kwargs):
    """
    Log activity when a task is deleted.
    """
    TaskActivity.objects.create(
        task=instance,
        user=instance.created_by,
        activity_type='updated',
        description=f'Task "{instance.title}" was deleted',
        tenant_id=instance.tenant_id
    )