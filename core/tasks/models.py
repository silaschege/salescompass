from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
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


class TaskStatus(TenantModel):
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


class TaskType(TenantModel):
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


class RecurrencePattern(TenantModel):
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


class Task(TenantModel):
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
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subtasks')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    task_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    task_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

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


class TaskTemplate(TenantModel):
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
    template_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    template_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.template_name
