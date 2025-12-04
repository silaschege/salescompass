from django.db import models
from django.utils import timezone
from core.models import TenantModel
from core.models import User


# Legacy choices - kept for backward compatibility during migration
TASK_PRIORITIES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

TASK_STATUSES = [
    ('todo', 'To Do'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('overdue', 'Overdue'),
]

TASK_TYPES = [
    ('lead_review', 'Lead Review'),
    ('lead_contact', 'Lead Contact'),
    ('lead_qualify', 'Lead Qualification'),
    ('account_followup', 'Account Follow-up'),
    ('opportunity_demo', 'Opportunity Demo'),
    ('proposal_followup', 'Proposal Follow-up'),
    ('renewal_reminder', 'Renewal Reminder'),
    ('csat_followup', 'CSAT Follow-up'),
    ('case_escalation', 'Case Escalation'),
    ('nps_detractor', 'NPS Detractor Follow-up'),
    ('esg_engagement', 'ESG Engagement'),
    ('custom', 'Custom Task'),
]

RECURRENCE_CHOICES = [
    ('none', 'None'),
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('yearly', 'Yearly'),
]


class TaskPriority(TenantModel):
    """
    Dynamic task priority levels - allows tenant-specific customization.
    """
    name = models.CharField(max_length=50, db_index=True)  # e.g., 'low', 'high'
    label = models.CharField(max_length=100)  # e.g., 'Low Priority', 'High Priority'
    order = models.IntegerField(default=0, help_text="Sort order (lower = higher priority)")
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, help_text="System priorities cannot be deleted")
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = [('tenant_id', 'name')]
        verbose_name_plural = 'Task Priorities'
    
    def __str__(self):
        return self.label


class TaskStatus(TenantModel):
    """
    Dynamic task status values - allows tenant-specific workflows.
    """
    name = models.CharField(max_length=50, db_index=True)  # e.g., 'todo', 'in_progress'
    label = models.CharField(max_length=100)  # e.g., 'To Do', 'In Progress'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False, help_text="Indicates task is complete/cancelled")
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = [('tenant_id', 'name')]
        verbose_name_plural = 'Task Statuses'
    
    def __str__(self):
        return self.label


class Task(TenantModel):
    """
    Comprehensive task management for all SalesCompass modules.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks')
    
    # Related objects (only one should be populated based on task type)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    opportunity = models.ForeignKey('opportunities.Opportunity', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    related_lead = models.ForeignKey('leads.Lead', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    nps_response = models.ForeignKey('nps.NpsResponse', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    engagement_event = models.ForeignKey('engagement.EngagementEvent', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    
    # Task properties
    # Legacy choice fields (deprecated - use _ref fields instead)
    priority = models.CharField(max_length=10, choices=TASK_PRIORITIES, default='medium')
    status = models.CharField(max_length=20, choices=TASK_STATUSES, default='todo')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    
    # New dynamic configuration fields
    priority_ref = models.ForeignKey(
        TaskPriority,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Dynamic task priority (replaces priority field)"
    )
    status_ref = models.ForeignKey(
        TaskStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Dynamic task status (replaces status field)"
    )
    
    # Timing
    due_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='none')
    recurrence_end_date = models.DateField(null=True, blank=True)
    
    # Reminders
    reminder_enabled = models.BooleanField(default=True)
    reminder_time = models.IntegerField(default=30)  # Minutes before due date
    reminder_sent = models.BooleanField(default=False)
    
    # Additional properties
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True)  # Comma-separated tags
    custom_fields = models.JSONField(default=dict, blank=True)  # For extensibility
    
    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def is_overdue(self):
        """Check if task is overdue."""
        return self.status not in ['completed', 'cancelled'] and self.due_date < timezone.now()


    # apps/tasks/models.py - Keep only ONE mark_completed method
    def mark_completed(self, completed_by=None):
        """Mark task as completed and trigger workflows."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if completed_by:
            self.assigned_to = completed_by
            self.save(update_fields=['status', 'completed_at', 'assigned_to'])
    
        # Trigger completion workflows
        from .utils import trigger_task_completion_workflows
        trigger_task_completion_workflows(self, completed_by)
   

    

    def get_related_object(self):
        """Get the related object for this task."""
        if self.account:
            return self.account
        elif self.opportunity:
            return self.opportunity
        elif self.related_lead:
            return self.related_lead
        elif self.case:
            return self.case
        elif self.nps_response:
            return self.nps_response
        elif self.engagement_event:
            return self.engagement_event
        return None

    def get_related_object_url(self):
        """Get URL to the related object detail page."""
        obj = self.get_related_object()
        if not obj:
            return None
            
        if self.account:
            return f"/accounts/{obj.pk}/"
        elif self.opportunity:
            return f"/opportunities/{obj.pk}/"
        elif self.related_lead:
            return f"/leads/{obj.pk}/"
        elif self.case:
            return f"/cases/{obj.pk}/"
        elif self.nps_response:
            return f"/engagement/nps/responses/{obj.pk}/"
        return None
    
    def get_display_name(self):
        """Get a safe display name for the task that handles None values."""
        if self.task_type == 'lead_contact' and self.related_lead:
            return f"Lead Contact: {self.related_lead.full_name}"
        elif self.task_type == 'account_followup' and self.account:
            return f"Account Follow-up: {self.account.name}"
        elif self.task_type == 'opportunity_demo' and self.opportunity:
            return f"Opportunity Demo: {self.opportunity.name}"
        elif self.task_type == 'case_escalation' and self.case:
            return f"Case Escalation: {self.case.subject}"
        else:
            return self.title

    def save(self, *args, **kwargs):
        """Override save to handle status updates and validation."""
        is_new = self.pk is None
        old_status = 'todo'
        
        if not is_new:
            try:
                old_instance = Task.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Task.DoesNotExist:
                pass

            # Ensure task has required related object for its type
        required_relations = {
        'lead_contact': 'related_lead',
        'lead_qualify': 'related_lead', 
        'account_followup': 'account',
        'opportunity_demo': 'opportunity',
        'case_escalation': 'case',
        'nps_detractor': 'nps_response',
        }
    
        required_field = required_relations.get(self.task_type)
        if required_field and not getattr(self, required_field):
            raise ValueError(f"Task type '{self.task_type}' requires {required_field}")
    
        super().save(*args, **kwargs)
        
        # Ensure only one related object is set
        related_objects = [
            self.account, self.opportunity, self.related_lead, 
            self.case, self.nps_response, self.engagement_event
        ]
        related_count = sum(1 for obj in related_objects if obj is not None)
        
        if related_count > 1:
            raise ValueError("Task can only be associated with one related object")
        
        # Set created_by if new task
        if is_new and not self.created_by:
            from django.utils import timezone
            self.created_at = timezone.now()
        
        # Remove force_insert if present to avoid IntegrityError on second save
        if 'force_insert' in kwargs:
            kwargs.pop('force_insert')
            
        super().save(*args, **kwargs)
        
        if is_new:
            # Schedule reminder if enabled
            if self.reminder_enabled:
                try:
                    from .celery import schedule_task_reminder
                    schedule_task_reminder(self.pk)
                except ImportError:
                    # Celery not available, log warning but don't fail
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("Celery not available, task reminders disabled")
            
            # Emit creation event
            from automation.utils import emit_event
            emit_event('tasks.created', {
                'task_id': self.id,
                'title': self.title,
                'priority': self.priority,
                'status': self.status,
                'assigned_to_id': self.assigned_to_id,
                'tenant_id': self.tenant_id
            })
            
        # Check for completion
        if self.status == 'completed' and old_status != 'completed':
            from automation.utils import emit_event
            emit_event('tasks.completed', {
                'task_id': self.id,
                'title': self.title,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'tenant_id': self.tenant_id
            })


class TaskComment(TenantModel):
    """
    Comments on tasks for collaboration.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.task.title} by {self.author.email if self.author else 'Anonymous'}"


class TaskAttachment(TenantModel):
    """
    File attachments for tasks.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.task.title}: {self.file.name}"


class TaskTemplate(TenantModel):
    """
    Reusable task templates for common workflows.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    priority = models.CharField(max_length=10, choices=TASK_PRIORITIES, default='medium')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    default_due_offset = models.IntegerField(default=1)  # Days from creation
    is_active = models.BooleanField(default=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

    def create_task_from_template(self, **kwargs):
        """Create a new task from this template."""
        task = Task(
            title=kwargs.get('title', self.name),
            description=kwargs.get('description', self.description),
            task_type=self.task_type,
            priority=self.priority,
            estimated_hours=self.estimated_hours,
            due_date=kwargs.get('due_date', timezone.now() + timezone.timedelta(days=self.default_due_offset)),
            tenant_id=kwargs.get('tenant_id'),
            **{k: v for k, v in kwargs.items() if k not in ['title', 'description', 'due_date', 'tenant_id']}
        )
        task.save()
        return task