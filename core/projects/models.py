from django.db import models
from django.utils import timezone
from tenants.models import TenantAwareModel as TenantModel
from core.models import User, TimeStampedModel
from accounts.models import Account

class Project(TenantModel, TimeStampedModel):
    """
    Project container for PSA and billability tracking.
    """
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PROJECT_TYPE_CHOICES = [
        ('fixed_price', 'Fixed Price'),
        ('time_materials', 'Time & Materials'),
        ('internal', 'Internal / Non-Billable'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    customer = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='fixed_price')
    
    # Financials
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    billable_hours_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Ownership
    project_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')

    def __str__(self):
        return self.name

class ProjectMilestone(TenantModel, TimeStampedModel):
    """
    Key project milestones, often linked to invoicing.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Billability
    is_billable = models.BooleanField(default=False)
    billing_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    invoice = models.ForeignKey('billing.Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='milestones')

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class ResourceAllocation(TenantModel, TimeStampedModel):
    """
    Allocates staff to projects with billing rates.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='allocations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_allocations')
    role = models.CharField(max_length=100, blank=True)
    
    # Billing
    billing_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Hourly billing rate")
    cost_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Hourly internal cost rate")
    
    allocation_percentage = models.IntegerField(default=100, help_text="Percentage of user time allocated")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} on {self.project.name}"
