from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q, F
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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


class TaskPriority(TenantModel, TimeStampedModel):
    """
    Dynamic task priority values - allows tenant-specific priority tracking.
    """
    priority_name = models.CharField(max_length=10, db_index=True, help_text="e.g., 'low', 'high'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Low', 'High'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    priority_is_active = models.BooleanField(default=True, help_text="Whether this priority is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'priority_name']
        unique_together = [('tenant_id', 'priority_name')]
        verbose_name_plural = 'Task Priorities'
    
    def __str__(self):
        return self.label


class TaskStatus(TenantModel, TimeStampedModel):
    """
    Dynamic task status values - allows tenant-specific status tracking.
    """
    status_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'todo', 'completed'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'To Do', 'Completed'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    status_is_active = models.BooleanField(default=True, help_text="Whether this status is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'status_name']
        unique_together = [('tenant_id', 'status_name')]
        verbose_name_plural = 'Task Statuses'
    
    def __str__(self):
        return self.label


class TaskType(TenantModel, TimeStampedModel):
    """
    Dynamic task type values - allows tenant-specific type tracking.
    """
    type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'lead_review', 'custom'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Lead Review', 'Custom Task'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'type_name']
        unique_together = [('tenant_id', 'type_name')]
        verbose_name_plural = 'Task Types'
    
    def __str__(self):
        return self.label


class RecurrencePattern(TenantModel, TimeStampedModel):
    """
    Dynamic recurrence pattern values - allows tenant-specific pattern tracking.
    """
    pattern_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'daily', 'weekly'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Daily', 'Weekly'
    order = models.IntegerField(default=0)
    pattern_is_active = models.BooleanField(default=True, help_text="Whether this pattern is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'pattern_name']
        unique_together = [('tenant_id', 'pattern_name')]
        verbose_name_plural = 'Recurrence Patterns'
    
    def __str__(self):
        return self.label


class Task(TenantModel, TimeStampedModel):
    title = models.CharField(max_length=255)
    task_description = models.TextField(blank=True, help_text="Description of the task")  # Renamed from 'description' to avoid conflict with base class
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks')
    account = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    opportunity = models.ForeignKey('opportunities.Opportunity', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    case = models.ForeignKey('cases.Case', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    priority = models.CharField(max_length=10, choices=TASK_PRIORITIES, default='medium')
    # New dynamic field
    priority_ref = models.ForeignKey(
        TaskPriority,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Dynamic priority (replaces priority field)"
    )
    status = models.CharField(max_length=20, choices=TASK_STATUSES, default='todo')
    # New dynamic field
    status_ref = models.ForeignKey(
        TaskStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Dynamic status (replaces status field)"
    )
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    # New dynamic field
    task_type_ref = models.ForeignKey(
        TaskType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Dynamic task type (replaces task_type field)"
    )
    due_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='none')
    # New dynamic field
    recurrence_pattern_ref = models.ForeignKey(
        RecurrencePattern,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Dynamic recurrence pattern (replaces recurrence_pattern field)"
    )
    recurrence_end_date = models.DateField(null=True, blank=True)
    
    # Generic Relations - Enable linking to any system object
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subtasks')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # Removed task_created_at and task_updated_at since TimeStampedModel provides these
    # In Task model
    comment_count = models.PositiveIntegerField(default=0, editable=False)
    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status != 'completed' and self.due_date < timezone.now():
            return True
        return False

    @property
    def days_until_due(self):
        from django.utils import timezone
        from datetime import timedelta
        if self.due_date:
            diff = self.due_date - timezone.now()
            return diff.days
        return None

    def save(self, *args, **kwargs):
        # Auto-populate generic fields from specific foreign keys for backward compatibility
        if not self.content_type and not self.object_id:
            if self.account:
                self.content_object = self.account
            elif self.opportunity:
                self.content_object = self.opportunity
            elif self.lead:
                self.content_object = self.lead
            elif self.case:
                self.content_object = self.case
        super().save(*args, **kwargs)


class TaskTemplate(TenantModel, TimeStampedModel):
    template_name = models.CharField(max_length=255, help_text="Name of the task template")  # Renamed from 'name' to avoid conflict
    template_description = models.TextField(blank=True, help_text="Description of the template")  # Renamed from 'description' to avoid conflict with base class
    title_template = models.CharField(max_length=255, help_text="Template for task title with placeholders")
    description_template = models.TextField(help_text="Template for task description with placeholders")
    priority = models.CharField(max_length=10, choices=TASK_PRIORITIES, default='medium')
    # New dynamic field
    priority_ref = models.ForeignKey(
        TaskPriority,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='task_templates',
        help_text="Dynamic priority (replaces priority field)"
    )
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    # New dynamic field
    task_type_ref = models.ForeignKey(
        TaskType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='task_templates',
        help_text="Dynamic task type (replaces task_type field)"
    )
    due_date_offset_days = models.IntegerField(default=0, help_text="Number of days from creation to due date")
    template_is_active = models.BooleanField(default=True, help_text="Whether this template is active")  # Renamed from 'is_active' to avoid conflict with base class
    # Removed template_created_at and template_updated_at since TimeStampedModel provides these

    def __str__(self):
        return self.template_name

# In models.py
class TaskDependency(TenantModel, TimeStampedModel):
    """
    Represents dependencies between tasks (e.g., Task A must be completed before Task B)
    """
    PRED = 'pred'  # Predecessor dependency
    SUCC = 'succ'  # Successor dependency
    
    DEPENDENCY_TYPES = [
        ('finish_start', 'Finish-Start'),
        ('start_start', 'Start-Start'),
        ('finish_finish', 'Finish-Finish'),
        ('start_finish', 'Start-Finish'),
    ]
    
    predecessor = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='successor_dependencies',
        help_text="The task that must be completed first"
    )
    successor = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='predecessor_dependencies',
        help_text="The task that depends on the predecessor"
    )
    dependency_type = models.CharField(
        max_length=20, 
        choices=DEPENDENCY_TYPES, 
        default='finish_start',
        help_text="Type of dependency relationship"
    )
    lag_time = models.DurationField(
        null=True, 
        blank=True,
        help_text="Time delay between predecessor completion and successor start"
    )
    
# ... existing code ...

    class Meta:
        unique_together = ('predecessor', 'successor')

    
    def clean(self):
        if self.predecessor == self.successor:
            raise ValidationError("A task cannot depend on itself")
        
        # Check that both tasks belong to the same tenant
        if self.predecessor.tenant_id != self.successor.tenant_id:
            raise ValidationError("Both tasks must belong to the same tenant")

# In models.py
class TaskTimeEntry(TenantModel, TimeStampedModel):
    """
    Track time spent on tasks
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='time_entries'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="User who logged the time"
    )
    date_logged = models.DateField(default=timezone.now)
    hours_spent = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Hours spent on the task"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of work done"
    )
    is_billable = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.email} - {self.hours_spent}h on {self.task.title}"

# In models.py
class TaskComment(TenantModel, TimeStampedModel):
    """
    Comments on tasks with mention functionality
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='task_comments'
    )
    content = models.TextField()
    # Using TimeStampedModel's created_at and updated_at instead of local fields
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    mentioned_users = models.ManyToManyField(
        User, 
        blank=True,
        related_name='mentioned_in_task_comments',
        help_text="Users mentioned in this comment"
    )
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.email} on {self.task.title}"

# In models.py
def get_task_attachment_path(instance, filename):
    """
    Generate upload path for task attachments
    Format: tenant_id/task_id/filename
    """
    return f"tasks/{instance.tenant_id}/{instance.task.id}/{filename}"
class TaskAttachment(TenantModel, TimeStampedModel):
    """
    File attachments for tasks
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='attachments'
    )
    file = models.FileField(upload_to=get_task_attachment_path)
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE
    )
    # Using TimeStampedModel's uploaded_at instead of local field
    file_size = models.PositiveIntegerField()  # in bytes
    mime_type = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.filename} for {self.task.title}"



# In models.py
class TaskActivity(TenantModel, TimeStampedModel):
    """
    Activity stream for tasks
    """
    ACTIVITY_TYPES = [
        ('created', 'Task Created'),
        ('updated', 'Task Updated'),
        ('completed', 'Task Completed'),
        ('assigned', 'Task Assigned'),
        ('commented', 'Comment Added'),
        ('attachment_added', 'Attachment Added'),
        ('dependency_added', 'Dependency Added'),
    ]
    
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='activities'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='task_activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # Additional data about the activity
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} on {self.task.title}"

# In models.py

class TaskSharing(TenantModel, TimeStampedModel):
    """
    Share tasks with other users/teams within the same tenant
    """
    SHARE_LEVELS = [
        ('view', 'View Only'),
        ('comment', 'View and Comment'),
        ('edit', 'View, Comment and Edit'),
    ]
    
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='shared_with'
    )
    shared_with_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Specific user to share with"
    )
    shared_with_team = models.ForeignKey(
        'tenants.TenantMember',  # Using TenantMember instead of OrganizationMember
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Team member to share with"
    )
    shared_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='tasks_shared'
    )
    share_level = models.CharField(max_length=10, choices=SHARE_LEVELS, default='view')
    expires_at = models.DateTimeField(null=True, blank=True)
    can_reassign = models.BooleanField(default=False)
    
    class Meta:
        unique_together = [
            ('task', 'shared_with_user'),
            ('task', 'shared_with_team')
        ]
    
    def __str__(self):
        if self.shared_with_user:
            return f"{self.task.title} shared with {self.shared_with_user.email}"
        elif self.shared_with_team:
            return f"{self.task.title} shared with {self.shared_with_team.user.email}"  # Using user.email instead of team.name
        return f"{self.task.title} shared"
