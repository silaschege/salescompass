from django.db import models
from django.utils import timezone
from core.models import User
from tenants.models import Tenant, TenantAwareModel as TenantModel


class Workflow(TenantModel):
    """Model for managing workflow automations"""
    
    workflow_name = models.CharField(max_length=255, help_text="Name of the workflow")
    workflow_description = models.TextField(blank=True, help_text="Description of what this workflow does")
    workflow_trigger_type = models.CharField(max_length=50, choices=[
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
    ], help_text="What triggers this workflow")
    
    workflow_is_active = models.BooleanField(default=True, help_text="Whether this workflow is currently active")
    workflow_created_at = models.DateTimeField(auto_now_add=True)
    workflow_updated_at = models.DateTimeField(auto_now=True)
    workflow_builder_data = models.JSONField(blank=True, default=dict, help_text="Raw data from visual builder")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='workflows_created')

    class Meta:
        verbose_name = "Workflow"
        verbose_name_plural = "Workflows"
        ordering = ['-workflow_created_at']
    
    def __str__(self):
        return self.workflow_name


class WorkflowAction(TenantModel):
    """Model for defining actions in workflows"""
    ACTION_TYPE_CHOICES = [
        ('send_email', 'Send Email'),
        ('create_task', 'Create Task'),
        ('update_field', 'Update Field'),
        ('run_function', 'Run Function'),
        ('create_case', 'Create Case'),
        ('assign_owner', 'Assign Owner'),
        ('send_slack_message', 'Send Slack Message'),
        ('webhook', 'Webhook'),
        ('create_nba', 'Create Next Best Action'),
        # Enhanced communication actions
        ('send_sms', 'Send SMS'),
        ('send_teams_message', 'Send Microsoft Teams Message'),
        ('send_whatsapp', 'Send WhatsApp Message'),
        # Workflow control actions
        ('approval', 'Request Approval'),
        ('delay', 'Delay Execution'),
        ('loop', 'Loop/Iterate'),
        # Custom actions
        ('custom_code', 'Custom Code Action'),
    ]
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='workflow_actions')
    workflow_action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, help_text="Type of action to perform")
    workflow_action_parameters = models.JSONField(default=dict, help_text="Parameters for the action (JSON)")
    workflow_action_order = models.IntegerField(default=0, help_text="Execution order (lower executes first)")
    workflow_action_is_active = models.BooleanField(default=True, help_text="Whether this action is active")
    workflow_action_created_at = models.DateTimeField(auto_now_add=True)
    workflow_action_updated_at = models.DateTimeField(auto_now=True)
    
    # Branching support
    branch = models.ForeignKey('WorkflowBranch', on_delete=models.CASCADE, null=True, blank=True, related_name='branch_actions')
    branch_value = models.BooleanField(null=True, blank=True, help_text="True if action is in the 'Yes' path, False if in 'No' path")

    class Meta:
        verbose_name = "Workflow Action"
        verbose_name_plural = "Workflow Actions"
        ordering = ['workflow_action_order', 'workflow_action_created_at']
    
    def __str__(self):
        return f"{self.workflow_action_type} for {self.workflow.workflow_name}"


class WorkflowBranch(TenantModel):
    """Model for defining branching logic (if/else) in workflows"""
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='workflow_branches')
    branch_name = models.CharField(max_length=255, help_text="Name of this branching point")
    branch_conditions = models.JSONField(default=dict, help_text="Conditions to evaluate for branching (JSON)")
    branch_order = models.IntegerField(default=0, help_text="Order in which this branch occurs")
    branch_is_active = models.BooleanField(default=True)
    branch_created_at = models.DateTimeField(auto_now_add=True)
    branch_updated_at = models.DateTimeField(auto_now=True)

    # Allow branches to be nested
    parent_branch = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_branches')
    parent_branch_value = models.BooleanField(null=True, blank=True, help_text="True if this branch is in the 'Yes' path of parent")

    class Meta:
        verbose_name = "Workflow Branch"
        verbose_name_plural = "Workflow Branches"
        ordering = ['branch_order', 'branch_created_at']

    def __str__(self):
        return f"Branch {self.branch_name} for {self.workflow.workflow_name}"


class WorkflowExecution(TenantModel):
    """Model for tracking workflow executions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('waiting_for_approval', 'Waiting for Approval'),
    ]
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    workflow_execution_trigger_payload = models.JSONField(help_text="Data that triggered the workflow")
    workflow_execution_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    workflow_execution_error_message = models.TextField(blank=True)
    workflow_execution_executed_at = models.DateTimeField(auto_now_add=True)
    workflow_execution_completed_at = models.DateTimeField(blank=True, null=True)
    workflow_execution_execution_time_ms = models.IntegerField(blank=True, help_text="Execution time in milliseconds", null=True)
    
    # Stateful execution fields for pausing/resuming
    workflow_execution_current_step_id = models.IntegerField(null=True, blank=True, help_text="ID of the next action to execute")
    workflow_execution_current_branch_id = models.IntegerField(null=True, blank=True, help_text="ID of the current branch")
    workflow_execution_current_branch_value = models.BooleanField(null=True, blank=True)
    workflow_execution_context_data = models.JSONField(default=dict, blank=True, help_text="Saved context for resuming execution")
    
    # Replay tracking fields
    is_replay = models.BooleanField(default=False, help_text="Whether this is a replay of a previous execution")
    original_execution = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replays')
    
    workflow_execution_created_at = models.DateTimeField(auto_now_add=True)
    workflow_execution_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workflow Execution"
        verbose_name_plural = "Workflow Executions"
        ordering = ['-workflow_execution_executed_at']
    
    def __str__(self):
        return f"{self.workflow.workflow_name} - {self.workflow_execution_status}"


class WorkflowTrigger(TenantModel):
    """Model for defining triggers in workflows"""
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='triggers')
    workflow_trigger_event = models.CharField(max_length=100, help_text="Event that triggers this workflow")
    workflow_trigger_conditions = models.JSONField(default=dict, help_text="Conditions that must be met for the trigger to fire (JSON)")
    workflow_trigger_is_active = models.BooleanField(default=True, help_text="Whether this trigger is active")
    workflow_trigger_created_at = models.DateTimeField(auto_now_add=True)
    workflow_trigger_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workflow Trigger"
        verbose_name_plural = "Workflow Triggers"
        ordering = ['workflow_trigger_created_at']
    
    def __str__(self):
        return f"Trigger for {self.workflow.workflow_name}: {self.workflow_trigger_event}"


class WorkflowTemplate(models.Model):
    """Model for workflow templates"""
    
    workflow_template_name = models.CharField(max_length=255, help_text="Name of the workflow template")
    workflow_template_description = models.TextField(blank=True, help_text="Description of what this template does")
    workflow_template_trigger_type = models.CharField(max_length=50, choices=[
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
    ])
    workflow_template_builder_data = models.JSONField(help_text="Drawflow JSON structure")
    workflow_template_is_active = models.BooleanField(default=True, help_text="Whether this template is active")
    workflow_template_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Workflow Template"
        verbose_name_plural = "Workflow Templates"
        ordering = ['workflow_template_name']
    
    def __str__(self):
        return self.workflow_template_name


# Keep the existing models that serve different purposes
class Automation(TenantModel):
    """Model for managing automation workflows"""
    
    automation_name = models.CharField(max_length=255, help_text="Name of the automation")
    automation_description = models.TextField(blank=True, help_text="Description of what this automation does")
    automation_is_active = models.BooleanField(default=True, help_text="Whether this automation is currently active")
    
    trigger_type = models.CharField(max_length=100, choices=[
        ('event_based', 'Event Based'),
        ('time_based', 'Time Based'),
        ('condition_based', 'Condition Based'),
        ('manual', 'Manual Trigger'),
        ('webhook', 'Webhook Trigger'),
        ('api_call', 'API Call'),
    ], help_text="What triggers this automation")
    
    trigger_config = models.JSONField(default=dict, blank=True, help_text="Configuration for the trigger")
    priority = models.IntegerField(default=100, help_text="Priority of the automation (lower numbers execute first)")
    max_executions_per_minute = models.IntegerField(default=60, help_text="Max number of times this can execute per minute")
    execution_timeout_seconds = models.IntegerField(default=30, help_text="Timeout for execution in seconds")
    error_handling = models.JSONField(default=dict, blank=True, help_text="How to handle errors during execution")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='automations_created')
    automation_created_at = models.DateTimeField(auto_now_add=True)
    automation_updated_at = models.DateTimeField(auto_now=True)
    last_executed = models.DateTimeField(null=True, blank=True, help_text="Last time this was executed")
    execution_count = models.IntegerField(default=0, help_text="Number of times this has been executed")
    failure_count = models.IntegerField(default=0, help_text="Number of times this has failed")
    average_execution_time_ms = models.FloatField(default=0.0, help_text="Average execution time in milliseconds")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing automations")
    notes = models.TextField(blank=True, help_text="Internal notes about this automation")
    is_system = models.BooleanField(default=False, help_text="Automation Triggered By System")
    class Meta:
        verbose_name = "Automation"
        verbose_name_plural = "Automations"
        ordering = ['priority', '-automation_created_at']
    
    def __str__(self):
        return f"{self.automation_name} - Priority: {self.priority}"


class AutomationCondition(TenantModel):
    """Model for defining conditions in automations"""
    OPERATOR_CHOICES = [
        ('eq', 'Equals'),
        ('ne', 'Not Equal'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
        ('gte', 'Greater Than or Equal'),
        ('lte', 'Less Than or Equal'),
        ('in', 'In List'),
        ('contains', 'Contains'),
        ('regex', 'Matches Regex'),
    ]
    
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='conditions')
    field_path = models.CharField(max_length=255, help_text="Dot notation path to the field to check (e.g., 'user.profile.status')")
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES, help_text="Comparison operator to use")
    value = models.TextField(help_text="Expected value for comparison")
    automation_condition_is_active = models.BooleanField(default=True, help_text="Whether this condition is active")
    order = models.IntegerField(default=0, help_text="Order to evaluate conditions (lower numbers first)")
    
    automation_condition_created_at = models.DateTimeField(auto_now_add=True)
    automation_condition_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Automation Condition"
        verbose_name_plural = "Automation Conditions"
        ordering = ['automation', 'order']
    
    def __str__(self):
        return f"Condition for {self.automation.automation_name}: {self.field_path} {self.operator} {self.value}"


class AutomationAction(TenantModel):
    """Model for defining actions in automations"""
    ACTION_TYPE_CHOICES = [
        ('send_email', 'Send Email'),
        ('create_task', 'Create Task'),
        ('update_field', 'Update Field'),
        ('run_function', 'Run Function'),
        ('create_case', 'Create Case'),
        ('assign_owner', 'Assign Owner'),
        ('send_slack_message', 'Send Slack Message'),
        ('webhook', 'Webhook Call'),
        ('custom', 'Custom Action'),
        # Enhanced communication actions
        ('send_sms', 'Send SMS'),
        ('send_teams_message', 'Send Microsoft Teams Message'),
        ('send_whatsapp', 'Send WhatsApp Message'),
    ]
    
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, help_text="Type of action to perform")
    automation_action_name = models.CharField(max_length=255, help_text="Name of this action")
    automation_action_description = models.TextField(blank=True, help_text="Description of what this action does")
    config = models.JSONField(default=dict, blank=True, help_text="Configuration parameters for the action")
    automation_action_is_active = models.BooleanField(default=True, help_text="Whether this action is active")
    order = models.IntegerField(default=0, help_text="Order to execute actions (lower numbers first)")
    
    automation_action_created_at = models.DateTimeField(auto_now_add=True)
    automation_action_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Automation Action"
        verbose_name_plural = "Automation Actions"
        ordering = ['automation', 'order']
    
    def __str__(self):
        return f"{self.action_type} - {self.automation_action_name}"


class AutomationExecutionLog(TenantModel):
    """Model for logging automation executions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('conditions_evaluated', 'Conditions Evaluated'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='execution_logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    trigger_payload = models.JSONField(help_text="Payload that triggered the automation")
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='automation_executions')
    execution_time_ms = models.IntegerField(null=True, blank=True, help_text="Time taken to execute in milliseconds")
    error_message = models.TextField(blank=True, help_text="Error message if execution failed")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When execution was completed")
    
    automation_execution_log_created_at = models.DateTimeField(auto_now_add=True)
    automation_execution_log_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Automation Execution Log"
        verbose_name_plural = "Automation Execution Logs"
        ordering = ['-automation_execution_log_created_at']
    
    def __str__(self):
        return f"{self.automation.automation_name} - {self.status} - {self.created_at}"


class WebhookEndpoint(TenantModel):
    """Model for managing webhook endpoints"""
 
    webhook_endpoint_name = models.CharField(max_length=255, help_text="Name of the webhook endpoint")
    webhook_endpoint_description = models.TextField(blank=True, help_text="Description of what this webhook does")
    webhook_endpoint_url = models.URLField(max_length=500, help_text="The URL to send webhook payloads to")
    webhook_endpoint_is_active = models.BooleanField(default=True, help_text="Whether this webhook is currently active")
    event_types = models.JSONField(default=list, blank=True, help_text="Types of events that trigger this webhook")
    http_method = models.CharField(max_length=10, choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ], default='POST')
    headers = models.JSONField(default=dict, blank=True, help_text="Headers to send with the webhook request")
    secret = models.CharField(max_length=255, blank=True, help_text="Secret used to sign webhook payloads")
    signature_header = models.CharField(max_length=50, default='X-Signature', help_text="Header name for the signature")
    signature_algorithm = models.CharField(max_length=20, default='sha256', help_text="Algorithm used for signatures")
    timeout_seconds = models.IntegerField(default=30, help_text="Timeout for webhook requests in seconds")
    retry_attempts = models.IntegerField(default=3, help_text="Number of retry attempts on failure")
    retry_delay_seconds = models.IntegerField(default=5, help_text="Delay between retries in seconds")
    rate_limit = models.IntegerField(default=100, help_text="Max requests per time period")
    rate_limit_period_seconds = models.IntegerField(default=3600, help_text="Time period for rate limiting in seconds")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='webhooks_created')
    webhook_endpoint_created_at = models.DateTimeField(auto_now_add=True)
    webhook_endpoint_updated_at = models.DateTimeField(auto_now=True)
    last_called = models.DateTimeField(null=True, blank=True, help_text="Last time this webhook was called")
    last_response_code = models.IntegerField(null=True, blank=True, help_text="Last HTTP response code received")
    last_error = models.TextField(blank=True, help_text="Last error message if any")
    failure_count = models.IntegerField(default=0, help_text="Number of consecutive failures")
    disabled_after_failures = models.IntegerField(default=5, help_text="Disable after this many failures")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing webhooks")
    notes = models.TextField(blank=True, help_text="Internal notes about this webhook")
    
    class Meta:
        verbose_name = "Webhook Endpoint"
        verbose_name_plural = "Webhook Endpoints"
        ordering = ['-webhook_endpoint_created_at']
    
    def __str__(self):
        return f"{self.webhook_endpoint_name} - {self.webhook_endpoint_url}"


class AutomationRule(models.Model):
    """Model for defining automation rules"""
    
    automation_rule_name = models.CharField(max_length=255, help_text="Name of the automation rule")
    automation_rule_description = models.TextField(blank=True, help_text="Description of what this rule does")
    automation_rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is currently active")
    trigger_type = models.CharField(max_length=100, choices=[
        ('event_based', 'Event Based'),
        ('time_based', 'Time Based'),
        ('condition_based', 'Condition Based'),
        ('manual', 'Manual Trigger'),
        ('webhook', 'Webhook Trigger'),
        ('api_call', 'API Call'),
    ])
    trigger_config = models.JSONField(default=dict, blank=True, help_text="Configuration for the trigger")
    conditions = models.JSONField(default=list, blank=True, help_text="Conditions that must be met for the rule to execute")
    actions = models.JSONField(default=list, blank=True, help_text="Actions to perform when the rule executes")
    priority = models.IntegerField(default=100, help_text="Priority of the rule (lower numbers execute first)")
    max_executions_per_minute = models.IntegerField(default=60, help_text="Max number of times this rule can execute per minute")
    execution_timeout_seconds = models.IntegerField(default=30, help_text="Timeout for rule execution in seconds")
    error_handling = models.JSONField(default=dict, blank=True, help_text="How to handle errors during execution")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='automation_rules')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='automation_rules_created')
    automation_rule_created_at = models.DateTimeField(auto_now_add=True)
    automation_rule_updated_at = models.DateTimeField(auto_now=True)
    last_executed = models.DateTimeField(null=True, blank=True, help_text="Last time this rule was executed")
    execution_count = models.IntegerField(default=0, help_text="Number of times this rule has been executed")
    failure_count = models.IntegerField(default=0, help_text="Number of times this rule has failed")
    average_execution_time_ms = models.FloatField(default=0.0, help_text="Average execution time in milliseconds")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing automation rules")
    notes = models.TextField(blank=True, help_text="Internal notes about this rule")
    
    class Meta:
        verbose_name = "Automation Rule"
        verbose_name_plural = "Automation Rules"
        ordering = ['priority', '-automation_rule_created_at']
    
    def __str__(self):
        return f"{self.automation_rule_name} - Priority: {self.priority}"


class WebhookDeliveryLog(models.Model):
    """Model for tracking webhook deliveries"""
    
    webhook_endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='delivery_logs')
    event_type = models.CharField(max_length=100, help_text="Type of event that triggered the webhook")
    payload = models.TextField(help_text="The payload sent to the webhook")
    headers = models.JSONField(default=dict, blank=True, help_text="Headers sent with the request")
    webhook_delivery_url = models.URLField(max_length=500, help_text="URL the webhook was sent to")
    http_method = models.CharField(max_length=10, help_text="HTTP method used")
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
        ('timeout', 'Timeout'),
        ('rate_limited', 'Rate Limited'),
    ], default='sent')
    response_status_code = models.IntegerField(null=True, blank=True, help_text="HTTP status code of the response")
    response_headers = models.JSONField(default=dict, blank=True, help_text="Headers received in the response")
    response_body = models.TextField(blank=True, help_text="Body of the response")
    execution_time_ms = models.FloatField(null=True, blank=True, help_text="Time taken to execute the request in milliseconds")
    error_message = models.TextField(blank=True, help_text="Error message if the request failed")
    retry_count = models.IntegerField(default=0, help_text="Number of retries attempted")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='webhook_delivery_logs')
    webhook_delivery_created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When the delivery was completed (success or failure)")
    signature = models.CharField(max_length=255, blank=True, help_text="Signature that was sent with the webhook")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing delivery logs")
    notes = models.TextField(blank=True, help_text="Internal notes about this delivery")
    
    class Meta:
        verbose_name = "Webhook Delivery Log"
        verbose_name_plural = "Webhook Delivery Logs"
        ordering = ['-webhook_delivery_created_at']
    
    def __str__(self):
        return f"{self.webhook_endpoint.webhook_endpoint_name} - {self.status} - {self.event_type}"


class QualityCheckSchedule(models.Model):
    """Model for scheduling data quality checks"""
    
    quality_check_schedule_name = models.CharField(max_length=255, help_text="Name of the quality check schedule")
    quality_check_schedule_description = models.TextField(blank=True, help_text="Description of what the quality check validates")
    quality_check_schedule_is_active = models.BooleanField(default=True, help_text="Whether this schedule is currently active")
    quality_check_schedule_check_type = models.CharField(max_length=100, choices=[
        ('data_completeness', 'Data Completeness'),
        ('data_accuracy', 'Data Accuracy'),
        ('data_consistency', 'Data Consistency'),
        ('data_uniqueness', 'Data Uniqueness'),
        ('data_timeliness', 'Data Timeliness'),
        ('data_validity', 'Data Validity'),
        ('data_integrity', 'Data Integrity'),
        ('duplicate_detection', 'Duplicate Detection'),
        ('schema_validation', 'Schema Validation'),
        ('referential_integrity', 'Referential Integrity'),
    ])
    quality_check_schedule_target_resource = models.CharField(max_length=255, help_text="Resource to check (e.g., table name, API endpoint)")
    quality_check_schedule_check_config = models.JSONField(default=dict, blank=True, help_text="Configuration for the quality check")
    quality_check_schedule_schedule_type = models.CharField(max_length=50, choices=[
        ('once', 'Once'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ], default='daily')
    quality_check_schedule_schedule_config = models.JSONField(default=dict, blank=True, help_text="Configuration for the schedule")
    quality_check_schedule_next_run = models.DateTimeField(help_text="When the next check is scheduled to run")
    quality_check_schedule_last_run = models.DateTimeField(null=True, blank=True, help_text="When the check was last run")
    quality_check_schedule_last_run_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    quality_check_schedule_last_run_result = models.JSONField(default=dict, blank=True, help_text="Result of the last run")
    quality_check_schedule_pass_threshold_percent = models.FloatField(default=95.0, help_text="Percentage of data that must pass to consider the check passed")
    quality_check_schedule_fail_on_error = models.BooleanField(default=True, help_text="Whether to fail the check if any errors occur")
    quality_check_schedule_notification_emails = models.JSONField(default=list, blank=True, help_text="Email addresses to notify on failure")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='quality_check_schedules')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_check_schedules_created')
    quality_check_schedule_created_at = models.DateTimeField(auto_now_add=True)
    quality_check_schedule_updated_at = models.DateTimeField(auto_now=True)
    quality_check_schedule_last_pass = models.DateTimeField(null=True, blank=True, help_text="Last time the check passed")
    quality_check_schedule_last_fail = models.DateTimeField(null=True, blank=True, help_text="Last time the check failed")
    quality_check_schedule_failure_count = models.IntegerField(default=0, help_text="Number of consecutive failures")
    quality_check_schedule_success_count = models.IntegerField(default=0, help_text="Number of successful runs")
    quality_check_schedule_tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing quality check schedules")
    quality_check_schedule_notes = models.TextField(blank=True, help_text="Internal notes about this quality check schedule")
    
    class Meta:
        verbose_name = "Quality Check Schedule"
        verbose_name_plural = "Quality Check Schedules"
        ordering = ['quality_check_schedule_name']
    
    def __str__(self):
        return f"{self.quality_check_schedule_name} - {self.quality_check_schedule_check_type}"

class AutomationAlert(TenantModel):
    """Model for tracking critical automation failures that need attention"""
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    # Can refer to either the old Automation or new Workflow models
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    
    # Link to the specific execution that failed
    execution_log = models.ForeignKey(AutomationExecutionLog, on_delete=models.SET_NULL, null=True, blank=True)
    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.SET_NULL, null=True, blank=True)
    
    alert_title = models.CharField(max_length=255)
    alert_message = models.TextField()
    alert_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    alert_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    alert_acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='automation_alerts_acknowledged')
    alert_acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    alert_created_at = models.DateTimeField(auto_now_add=True)
    alert_updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Alert: {self.alert_title} ({self.alert_severity})"


class AutomationNotificationPreference(TenantModel):
    """User preferences for receiving automation alerts"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='automation_notification_preferences')
    
    notify_on_all_failures = models.BooleanField(default=False)
    notify_on_critical_only = models.BooleanField(default=True)
    
    enable_email_notifications = models.BooleanField(default=True)
    enable_sms_notifications = models.BooleanField(default=False)
    enable_in_app_notifications = models.BooleanField(default=True)
    
    notification_frequency = models.CharField(max_length=20, choices=[
        ('immediate', 'Immediate'),
        ('daily_digest', 'Daily Digest'),
        ('weekly_summary', 'Weekly Summary'),
    ], default='immediate')
    
    alert_created_at = models.DateTimeField(auto_now_add=True)
    alert_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'tenant')
        verbose_name = "Automation Notification Preference"
        verbose_name_plural = "Automation Notification Preferences"

class WorkflowApproval(TenantModel):
    """Model for managing explicit approval steps in a workflow"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='approvals')
    workflow_action = models.ForeignKey('WorkflowAction', on_delete=models.CASCADE)
    
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approval_requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approvals_requested')
    requested_approvers = models.ManyToManyField(User, related_name='pending_approvals', blank=True)
    
    approval_comments = models.TextField(blank=True)
    approval_responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approvals_responded')
    approval_responded_at = models.DateTimeField(null=True, blank=True)
    
    approval_created_at = models.DateTimeField(auto_now_add=True)
    approval_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workflow Approval"
        verbose_name_plural = "Workflow Approvals"
        ordering = ['-approval_created_at']

    def __str__(self):
        return f"Approval for {self.workflow_execution} - {self.approval_status}"


class WorkflowScheduledExecution(TenantModel):
    """Model for tracking delayed/scheduled workflow actions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='scheduled_actions')
    action = models.ForeignKey(WorkflowAction, on_delete=models.CASCADE)
    scheduled_for = models.DateTimeField(help_text="When this action should be executed")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    context_data = models.JSONField(default=dict, blank=True, help_text="Saved context for execution")
    executed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workflow Scheduled Execution"
        verbose_name_plural = "Workflow Scheduled Executions"
        ordering = ['scheduled_for']
    
    def __str__(self):
        return f"Scheduled {self.action} for {self.scheduled_for}"


class WorkflowVersion(TenantModel):
    """Model for tracking workflow version history"""
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(help_text="Sequential version number")
    workflow_data_snapshot = models.JSONField(help_text="Full workflow configuration at this version")
    change_summary = models.TextField(blank=True, help_text="Description of changes in this version")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Workflow Version"
        verbose_name_plural = "Workflow Versions"
        ordering = ['-version_number']
        unique_together = ['workflow', 'version_number']
    
    def __str__(self):
        return f"{self.workflow.workflow_name} v{self.version_number}"


class WorkflowAnalyticsSnapshot(TenantModel):
    """Model for caching workflow analytics data"""
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, null=True, blank=True, related_name='analytics_snapshots')
    snapshot_date = models.DateField(help_text="Date this snapshot covers")
    
    # Execution metrics
    total_executions = models.IntegerField(default=0)
    successful_executions = models.IntegerField(default=0)
    failed_executions = models.IntegerField(default=0)
    
    # Performance metrics
    avg_execution_time_ms = models.FloatField(default=0.0)
    min_execution_time_ms = models.IntegerField(default=0)
    max_execution_time_ms = models.IntegerField(default=0)
    
    # Action breakdown
    action_stats = models.JSONField(default=dict, blank=True, help_text="Stats per action type")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workflow Analytics Snapshot"
        verbose_name_plural = "Workflow Analytics Snapshots"
        ordering = ['-snapshot_date']
        unique_together = ['workflow', 'snapshot_date', 'tenant']
    
    def __str__(self):
        workflow_name = self.workflow.workflow_name if self.workflow else "All Workflows"
        return f"Analytics for {workflow_name} on {self.snapshot_date}"


class CustomCodeSnippet(TenantModel):
    """Model for storing custom code snippets that can be executed in workflows"""
    
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
    ]
    
    name = models.CharField(max_length=255, help_text="Name of the custom code snippet")
    description = models.TextField(blank=True, help_text="Description of what this code does")
    code_content = models.TextField(help_text="The actual Python code to execute")
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default='python')
    parameters_schema = models.JSONField(default=dict, blank=True, help_text="JSON schema for expected parameters")
    is_active = models.BooleanField(default=True, help_text="Whether this code snippet is active")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Custom Code Snippet"
        verbose_name_plural = "Custom Code Snippets"
        ordering = ['-created_at']

    def __str__(self):
        return f"Custom Code: {self.name}"


class CustomCodeExecutionLog(TenantModel):
    """Model for logging custom code executions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
        ('security_violation', 'Security Violation'),
    ]
    
    custom_code_snippet = models.ForeignKey(CustomCodeSnippet, on_delete=models.CASCADE, related_name='execution_logs')
    workflow_execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='custom_code_logs')
    execution_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    input_parameters = models.JSONField(default=dict, blank=True, help_text="Input parameters passed to the code")
    output_result = models.JSONField(default=dict, blank=True, help_text="Output result from the code execution")
    error_message = models.TextField(blank=True, help_text="Error message if execution failed")
    execution_time_ms = models.IntegerField(null=True, blank=True, help_text="Time taken to execute in milliseconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Custom Code Execution Log"
        verbose_name_plural = "Custom Code Execution Logs"
        ordering = ['-created_at']

    def __str__(self):
        return f"Execution of {self.custom_code_snippet.name} - {self.execution_status}"
