from django.db import models
from core.models import TimeStampedModel, TenantModel,User
from django.urls import reverse
from typing import Any
from django.utils import timezone
from django.utils import timezone
from datetime import timedelta
from core.managers import VisibilityAwareManager


# Legacy choices - kept for backward compatibility during migration
LEAD_SOURCE_CHOICES = [
    ('web', 'Web Form'),
    ('event', 'Event'),
    ('referral', 'Referral'),
    ('ads', 'Paid Ads'),
    ('manual', 'Manual Entry'),
]

LEAD_STATUS_CHOICES = [
    ('new', 'New'),
    ('contacted', 'Contacted'),
    ('qualified', 'Qualified'),
    ('unqualified', 'Unqualified'),
    ('converted', 'Converted'),
]

INDUSTRY_CHOICES = [
    ('tech', 'Technology'),
    ('manufacturing', 'Manufacturing'),
    ('finance', 'Finance'),
    ('healthcare', 'Healthcare'),
    ('retail', 'Retail'),
    ('energy', 'Energy'),
    ('education', 'Education'),
    ('other', 'Other'),
]


class LeadSource(TenantModel):
    """
    Dynamic lead source values - allows tenant-specific source tracking.
    """
    name = models.CharField(max_length=50, db_index=True)  # e.g., 'web', 'event'
    label = models.CharField(max_length=100)  # e.g., 'Web Form', 'Trade Show'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    # Analytics tracking
    conversion_rate_target = models.FloatField(default=0.0, help_text="Target conversion rate (0-100)")
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = [('tenant_id', 'name')]
        verbose_name_plural = 'Lead Sources'
    
    def __str__(self):
        return self.label


class LeadStatus(TenantModel):
    """
    Dynamic lead status values - allows tenant-specific lead workflows.
    """
    name = models.CharField(max_length=50, db_index=True)  # e.g., 'new', 'qualified'
    label = models.CharField(max_length=100)  # e.g., 'New Lead', 'Qualified'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    # Workflow flags
    is_qualified = models.BooleanField(default=False, help_text="Indicates lead is qualified")
    is_closed = models.BooleanField(default=False, help_text="Indicates lead is closed (won/lost)")
    
    class Meta:
        ordering = ['order', 'name']
        unique_together = [('tenant_id', 'name')]
        verbose_name_plural = 'Lead Statuses'
    
    def __str__(self):
        return self.label


class Lead(TenantModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255)
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)
    job_title = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Add missing fields
    description = models.TextField(blank=True, help_text="Additional notes about the lead")
    title = models.CharField(max_length=255, blank=True, help_text="Custom title for the lead")
    
    # Fix field name consistency
    # Legacy choice fields (deprecated - use _ref fields instead)
    lead_source = models.CharField(max_length=20, choices=LEAD_SOURCE_CHOICES)  # Changed from 'source'
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default='new')
    lead_score = models.IntegerField(default=0)  # 0–100
    
    # New dynamic configuration fields
    source_ref = models.ForeignKey(
        LeadSource,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Dynamic lead source (replaces lead_source field)"
    )
    status_ref = models.ForeignKey(
        LeadStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Dynamic lead status (replaces status field)"
    )
    
    # Conversion - when lead becomes a new account
    converted_to_account = models.OneToOneField(
        'accounts.Account', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='converted_from_lead'
    )
    
    # Association - when lead is for an existing account (upsell/cross-sell)
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'  # This allows Account.leads.all()
    )
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    objects = VisibilityAwareManager()

    def get_timeline_event(self):
        """Get timeline event data for this lead."""
        if self.converted_to_account:
            return {
                'event_type': 'lead_converted',
                'title': f'Lead Converted: {self.first_name} {self.last_name}',
                'description': f'Lead converted to account with status: {self.get_status_display()}',
                'created_at': self.updated_at,
                'lead_id': self.id,
                'lead_status': self.status,
            }
        else:
            return {
                'event_type': 'lead_created',
                'title': f'New Lead: {self.first_name} {self.last_name}',
                'description': f'{self.get_lead_source_display()} lead created for {self.company}',
                'created_at': self.created_at,
                'lead_id': self.id,
                'lead_status': self.status,
            }

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.company})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def calculate_initial_score(self):
        """Calculate initial lead score based on provided information."""
        score = 0
        
        # Basic contact information (10 points each)
        if self.email:
            score += 10
        if self.phone:
            score += 10
        if self.job_title:
            score += 5
        if self.description:
            score += 5
            
        # Company information
        if self.industry:
            score += 10
            
        # Lead source scoring
        high_value_sources = ['referral', 'partner', 'event']
        if self.lead_source in high_value_sources:
            score += 15
        elif self.lead_source == 'web_form':
            score += 5
        elif self.lead_source == 'manual':
            score += 2
            
        # Account association bonus
        if self.account:  # Existing customer lead
            score += 20
            
        # Cap score at 100
        return min(score, 100)
    
    def update_status_from_score(self):
        """Update lead status based on current score."""
        current_score = self.lead_score
        
        if current_score >= 70:
            new_status = 'qualified'
        elif current_score >= 40:
            new_status = 'contacted'
        else:
            new_status = 'new'
            
        if self.status != new_status:
            old_status = self.status
            self.status = new_status
            self.save(update_fields=['status'])
            
            # Emit status change event
            from automation.utils import emit_event
            if new_status == 'qualified':
                emit_event('leads.lead_qualified', {
                    'lead_id': self.id,
                    'lead_name': self.full_name,
                    'lead_score': self.lead_score,
                    'company': self.company,
                    'owner_id': self.owner_id if self.owner else None,
                    'tenant_id': self.tenant_id
                })
            
            return True, old_status, new_status
        return False, None, None
    
    def save(self, *args, **kwargs):
        """Override save to calculate initial score and set status."""
        is_new = self.pk is None
        
        if is_new:
            # Calculate initial score for new leads
            self.lead_score = self.calculate_initial_score()
            
        super().save(*args, **kwargs)
        
        if is_new:
            # Update status based on initial score
            self.update_status_from_score()
            
            # Create initial tasks based on lead score and status
            self.create_initial_tasks()
            
            # Emit creation event
            from automation.utils import emit_event
            emit_event('leads.lead_created', {
                'lead_id': self.id,
                'lead_name': self.full_name,
                'lead_score': self.lead_score,
                'status': self.status,
                'company': self.company,
                'email': self.email,
                'owner_id': self.owner_id if self.owner else None,
                'tenant_id': self.tenant_id
            })
    
    def create_initial_tasks(self):
        """Create initial follow-up tasks based on lead score and status."""
        from tasks.models import Task  # Import here to avoid circular imports
        
        if self.status == 'new':
            # Low priority nurturing task
            Task.objects.create(
                title=f"Review lead: {self.full_name}",
                description="This lead needs initial review and potential outreach",
                assigned_to=self.owner,
                account=self.account,
                priority='low',
                status='todo',
                due_date=timezone.now() + timedelta(days=3),
                task_type='lead_review',
                tenant_id=self.tenant_id,
                related_lead=self
            )
            
        elif self.status == 'contacted':
            # Medium priority contact task
            Task.objects.create(
                title=f"Contact lead: {self.full_name}",
                description="Follow up with this lead based on their engagement score",
                assigned_to=self.owner,
                account=self.account,
                priority='medium',
                status='todo',
                due_date=timezone.now() + timedelta(days=1),
                task_type='lead_contact',
                tenant_id=self.tenant_id,
                related_lead=self
            )
            
        elif self.status == 'qualified':
            # High priority qualification task
            Task.objects.create(
                title=f"Qualify lead: {self.full_name}",
                description="This lead has high engagement score and needs immediate qualification",
                assigned_to=self.owner,
                account=self.account,
                priority='high',
                status='todo',
                due_date=timezone.now() + timedelta(hours=4),
                task_type='lead_qualify',
                tenant_id=self.tenant_id,
                related_lead=self
            )


class WebToLeadForm(TenantModel):
    """
    Web-to-lead form configuration.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    success_redirect_url = models.URLField(default='/thank-you/')
    
    # Form fields configuration
    include_first_name = models.BooleanField(default=True)
    include_last_name = models.BooleanField(default=True)
    include_email = models.BooleanField(default=True)
    include_phone = models.BooleanField(default=False)
    include_company = models.BooleanField(default=True)
    include_job_title = models.BooleanField(default=False)
    include_industry = models.BooleanField(default=True)
    
    # Custom fields
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Assignment
    assign_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assign_to_role = models.CharField(max_length=100, blank=True)
    
    # Tracking
    form_submissions = models.IntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    @property
    def total_submissions(self):
        return self.submissions.count()
    
    @property
    def conversion_rate(self):
        if self.total_submissions == 0:
            return 0.0
        converted_leads = self.submissions.filter(lead__isnull=False).count()
        return (converted_leads / self.total_submissions) * 100
    
    def get_embed_code_url(self):
        return reverse('leads:webtoleadform_embed', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class LeadSourceAnalytics(TenantModel):
    """
    Daily analytics for lead sources.
    """
    date = models.DateField()
    source = models.CharField(max_length=20, choices=LEAD_SOURCE_CHOICES)
    lead_count = models.IntegerField(default=0)
    qualified_count = models.IntegerField(default=0)
    converted_count = models.IntegerField(default=0)
    avg_lead_score = models.FloatField(default=0.0)
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    class Meta:
        unique_together = [('date', 'source', 'tenant_id')]

    def __str__(self):
        return f"{self.source} - {self.date}"