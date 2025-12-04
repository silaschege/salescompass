# apps/automation/
# ├── __init__.py
# ├── admin.py
# ├── apps.py
# ├── models.py
# ├── views.py
# ├── forms.py
# ├── engine.py
# ├── tasks.py
# ├── utils.py
# ├── urls.py
# └── templates/automation/
#     ├── list.html
#     ├── detail.html
#     ├── form.html
#     └── trigger_builder.html

from django.db import models
from core.models import TenantModel
from core.models import User

TRIGGER_TYPES = [
    ('account.created', 'Account Created'),
    ('account.health_changed', 'Account Health Changed'),
    ('lead.created', 'Lead Created'),
    ('lead.qualified', 'Lead Qualified'),
    ('opportunity.created', 'Opportunity Created'),
    ('opportunity.stage_changed', 'Opportunity Stage Changed'),
    ('proposal.viewed', 'Proposal Viewed'),
    ('proposal.esg_viewed', 'ESG Section Viewed'),
    ('case.created', 'Case Created'),
    ('case.sla_breached', 'SLA Breached'),
    ('case.csat_submitted', 'CSAT Submitted'),
    ('nps.submitted', 'NPS Submitted'),
    ('nps.detractor_alert', 'NPS Detractor Alert'),
    ('custom_status.changed', 'Custom Status Changed'),
    ('crm_setting.changed', 'CRM Setting Changed'),
    ('team.member_onboarded', 'Team Member Onboarded'),
    ('web_to_lead.submitted', 'Web-to-Lead Submitted'),
]

ACTION_TYPES = [
    ('send_email', 'Send Email'),
    ('create_task', 'Create Task'),
    ('update_field', 'Update Field'),
    ('run_function', 'Run Function'),
    ('create_case', 'Create Case'),
    ('assign_owner', 'Assign Owner'),
    ('send_slack_message', 'Send Slack Message'),
    ('webhook', 'Webhook'),
]

class Automation(TenantModel):
    """
    Automation rule with trigger, conditions, and actions.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)  # Cannot be deleted
    priority = models.IntegerField(default=0)  # Lower = higher priority
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['priority', 'name']
        indexes = [
            models.Index(fields=['trigger_type', 'is_active']),
            models.Index(fields=['tenant_id', 'is_active']),
        ]


class AutomationCondition(TenantModel):
    """
    Condition for an automation rule.
    """
    CONDITION_OPERATORS = [
        ('eq', 'Equals'),
        ('ne', 'Not Equals'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
        ('gte', 'Greater Than or Equal'),
        ('lte', 'Less Than or Equal'),
        ('in', 'In List'),
        ('contains', 'Contains'),
        ('regex', 'Matches Regex'),
    ]
    
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='conditions')
    field_path = models.CharField(max_length=100, help_text="Dot notation path (e.g., 'account.industry')")
    operator = models.CharField(max_length=20, choices=CONDITION_OPERATORS)
    value = models.JSONField(help_text="Value to compare against")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.field_path} {self.operator} {self.value}"


class AutomationAction(TenantModel):
    """
    Action to execute when automation is triggered.
    """
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    config = models.JSONField(help_text="Action configuration (JSON)")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_action_type_display()} for {self.automation.name}"

    class Meta:
        ordering = ['order']


class AutomationExecutionLog(TenantModel):
    """
    Log of automation executions for debugging and monitoring.
    """
    EXECUTION_STATUS_CHOICES = [
        ('triggered', 'Triggered'),
        ('conditions_evaluated', 'Conditions Evaluated'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE)
    trigger_payload = models.JSONField()
    status = models.CharField(max_length=20, choices=EXECUTION_STATUS_CHOICES, default='triggered')
    error_message = models.TextField(blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.automation.name} - {self.status}"


# Workflow Engine Models

class Workflow(TenantModel):
    """
    Workflow model for workflow execution engine.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    builder_data = models.JSONField(default=dict, blank=True, help_text="Raw data from visual builder")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trigger_type', 'is_active']),
            models.Index(fields=['tenant_id', 'is_active']),
        ]


class WorkflowTrigger(TenantModel):
    """
    Trigger configuration for a workflow with conditions.
    """
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='triggers')
    trigger_event = models.CharField(max_length=100, help_text="Event that triggers this workflow")
    conditions = models.JSONField(
        default=dict,
        help_text="Conditions that must be met for the trigger to fire (JSON)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trigger_event} for {self.workflow.name}"

    class Meta:
        ordering = ['created_at']


class WorkflowAction(TenantModel):
    """
    Action to be executed as part of a workflow.
    """
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='workflow_actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    parameters = models.JSONField(
        default=dict,
        help_text="Parameters for the action (JSON)"
    )
    order = models.IntegerField(default=0, help_text="Execution order (lower executes first)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.workflow.name}"

    class Meta:
        ordering = ['order', 'created_at']


class WorkflowExecution(TenantModel):
    """
    Log of workflow executions for monitoring and debugging.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    trigger_payload = models.JSONField(help_text="Data that triggered the workflow")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True, help_text="Execution time in milliseconds")

    def __str__(self):
        return f"{self.workflow.name} - {self.status} ({self.executed_at})"

    class Meta:
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['tenant_id', 'executed_at']),
        ]


class WorkflowTemplate(models.Model):
    """
    Template for creating common workflows.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    builder_data = models.JSONField(help_text="Drawflow JSON structure")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']