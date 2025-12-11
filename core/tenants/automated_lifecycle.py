from django.db import models
from django.utils import timezone
from core.models import User
from .models import Tenant


class AutomatedTenantLifecycleRule(models.Model):
    """Model for defining automated tenant lifecycle management rules"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the lifecycle rule")
    description = models.TextField(blank=True, help_text="Description of the lifecycle rule")
    is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    
    # Condition fields
    condition_type = models.CharField(max_length=50, choices=[
        ('usage_based', 'Usage Based'),
        ('time_based', 'Time Based'),
        ('billing_based', 'Billing Based'),
        ('activity_based', 'Activity Based'),
        ('custom', 'Custom Logic'),
    ])
    condition_field = models.CharField(max_length=100, help_text="Field to check for the condition")
    condition_operator = models.CharField(max_length=20, choices=[
        ('equals', 'Equals'),
        ('not_equals', 'Not Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('greater_equal', 'Greater Than or Equal'),
        ('less_equal', 'Less Than or Equal'),
        ('contains', 'Contains'),
        ('not_contains', 'Not Contains'),
    ])
    condition_value = models.CharField(max_length=255, help_text="Value to compare against")
    
    # Action to perform
    action_type = models.CharField(max_length=50, choices=[
        ('suspend', 'Suspend Tenant'),
        ('terminate', 'Terminate Tenant'),
        ('archive', 'Archive Tenant'),
        ('reactivate', 'Reactivate Tenant'),
        ('send_notification', 'Send Notification'),
        ('update_plan', 'Update Plan'),
        ('custom', 'Custom Action'),
    ])
    
    # Action parameters
    action_parameters = models.JSONField(default=dict, blank=True, help_text="Parameters for the action")
    
    # Scheduling and timing
    evaluation_frequency = models.CharField(max_length=20, choices=[
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='daily')
    last_evaluated = models.DateTimeField(null=True, blank=True, help_text="When the rule was last evaluated")
    next_evaluation = models.DateTimeField(default=timezone.now, help_text="When to next evaluate the rule")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifecycle_rules_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Automated Tenant Lifecycle Rule"
        verbose_name_plural = "Automated Tenant Lifecycle Rules"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.action_type}"


class AutomatedTenantLifecycleEvent(models.Model):
    """Model for tracking automated lifecycle events"""
    id = models.AutoField(primary_key=True)
    rule = models.ForeignKey(AutomatedTenantLifecycleRule, on_delete=models.CASCADE, related_name='events')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='automated_lifecycle_events')
    event_type = models.CharField(max_length=50, choices=[
        ('rule_evaluated', 'Rule Evaluated'),
        ('action_taken', 'Action Taken'),
        ('action_skipped', 'Action Skipped'),
        ('error_occurred', 'Error Occurred'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ])
    details = models.TextField(blank=True, help_text="Details about the event")
    triggered_at = models.DateTimeField(default=timezone.now)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='automated_lifecycle_events_executed')
    
    class Meta:
        verbose_name = "Automated Tenant Lifecycle Event"
        verbose_name_plural = "Automated Tenant Lifecycle Events"
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.event_type} for {self.tenant.name} by {self.rule.name}"


class TenantLifecycleWorkflow(models.Model):
    """Model for managing tenant lifecycle workflows"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the workflow")
    description = models.TextField(blank=True, help_text="Description of the workflow")
    workflow_type = models.CharField(max_length=50, choices=[
        ('onboarding', 'Onboarding'),
        ('offboarding', 'Offboarding'),
        ('suspension', 'Suspension'),
        ('reactivation', 'Reactivation'),
        ('termination', 'Termination'),
        ('migration', 'Migration'),
    ])
    is_active = models.BooleanField(default=True, help_text="Whether this workflow is active")
    steps = models.JSONField(default=list, blank=True, help_text="Ordered list of steps in the workflow")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifecycle_workflows_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Lifecycle Workflow"
        verbose_name_plural = "Tenant Lifecycle Workflows"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.workflow_type}"


class TenantLifecycleWorkflowExecution(models.Model):
    """Model for tracking execution of lifecycle workflows"""
    id = models.AutoField(primary_key=True)
    workflow = models.ForeignKey(TenantLifecycleWorkflow, on_delete=models.CASCADE, related_name='executions')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='lifecycle_workflow_executions')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lifecycle_workflow_executions')
    current_step = models.IntegerField(default=0, help_text="Current step in the workflow")
    total_steps = models.IntegerField(default=0, help_text="Total number of steps in the workflow")
    progress_percentage = models.FloatField(default=0.0, help_text="Progress percentage of the workflow")
    execution_log = models.TextField(blank=True, help_text="Log of workflow execution")
    error_message = models.TextField(blank=True, help_text="Error message if workflow failed")
    
    class Meta:
        verbose_name = "Tenant Lifecycle Workflow Execution"
        verbose_name_plural = "Tenant Lifecycle Workflow Executions"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.workflow.name} for {self.tenant.name} - {self.status}"
    
    def update_progress(self, current_step, total_steps):
        """Update the progress of the workflow"""
        self.current_step = current_step
        self.total_steps = total_steps
        if total_steps > 0:
            self.progress_percentage = (current_step / total_steps) * 100
        else:
            self.progress_percentage = 0
        self.save()


class TenantSuspensionWorkflow(models.Model):
    """Model for managing the tenant suspension workflow"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='suspension_workflows')
    status = models.CharField(max_length=20, choices=[
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='pending_approval')
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='suspension_workflows_initiated')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='suspension_workflows_approved')
    suspension_reason = models.TextField(help_text="Reason for the suspension")
    approval_notes = models.TextField(blank=True, help_text="Notes from the approver")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    steps_completed = models.JSONField(default=list, blank=True, help_text="List of steps that have been completed")
    total_steps = models.IntegerField(default=5, help_text="Total number of steps in the suspension workflow")
    
    class Meta:
        verbose_name = "Tenant Suspension Workflow"
        verbose_name_plural = "Tenant Suspension Workflows"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Suspension workflow for {self.tenant.name} - {self.status}"
    
    def approve(self, approved_by_user, notes=''):
        """Approve the suspension workflow"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_notes = notes
        self.approved_at = timezone.now()
        self.save()
    
    def complete_step(self, step_name):
        """Mark a step as completed"""
        if step_name not in self.steps_completed:
            self.steps_completed.append(step_name)
        self.save()


class TenantTerminationWorkflow(models.Model):
    """Model for managing the tenant termination workflow"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='termination_workflows')
    status = models.CharField(max_length=20, choices=[
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='pending_approval')
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='termination_workflows_initiated')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='termination_workflows_approved')
    termination_reason = models.TextField(help_text="Reason for the termination")
    approval_notes = models.TextField(blank=True, help_text="Notes from the approver")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    steps_completed = models.JSONField(default=list, blank=True, help_text="List of steps that have been completed")
    total_steps = models.IntegerField(default=7, help_text="Total number of steps in the termination workflow")
    data_preservation_required = models.BooleanField(default=True, help_text="Whether data preservation is required")
    data_preservation_record = models.ForeignKey('tenants.TenantDataPreservation', on_delete=models.SET_NULL, null=True, blank=True, related_name='termination_workflows')
    
    class Meta:
        verbose_name = "Tenant Termination Workflow"
        verbose_name_plural = "Tenant Termination Workflows"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Termination workflow for {self.tenant.name} - {self.status}"
    
    def approve(self, approved_by_user, notes=''):
        """Approve the termination workflow"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approval_notes = notes
        self.approved_at = timezone.now()
        self.save()
    
    def complete_step(self, step_name):
        """Mark a step as completed"""
        if step_name not in self.steps_completed:
            self.steps_completed.append(step_name)
        self.save()
