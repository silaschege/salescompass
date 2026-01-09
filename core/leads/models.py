from django.db import models
from core.models import TimeStampedModel,User
from tenants.models import TenantAwareModel as TenantModel
from settings_app.models import AssignmentRuleType
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

MARKETING_CHANNEL_CHOICES = [
    ('email', 'Email Marketing'),
    ('social', 'Social Media'),
    ('paid_ads', 'Paid Ads'),
    ('content', 'Content Marketing'),
    ('seo', 'SEO'),
    ('referral', 'Referral'),
    ('event', 'Events'),
    ('direct', 'Direct Traffic'),
    ('other', 'Other'),
]


class MarketingChannel(TenantModel):
    """
    Dynamic marketing channel values - allows tenant-specific channel tracking.
    """
    channel_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'email', 'social'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Email Marketing', 'Social Media'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True)
    channel_is_active = models.BooleanField(default=True, help_text="Whether this channel is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'channel_name']
        unique_together = [('tenant_id', 'channel_name')]
        verbose_name_plural = 'Marketing Channels'
    
    def __str__(self):
        return self.label


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


class Industry(TenantModel):
    """
    Dynamic industry values - allows tenant-specific industry tracking.
    """
    industry_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'tech', 'finance'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Technology', 'Finance'
    order = models.IntegerField(default=0)
    industry_is_active = models.BooleanField(default=True, help_text="Whether this industry is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'industry_name']
        unique_together = [('tenant_id', 'industry_name')]
        verbose_name_plural = 'Industries'
    
    def __str__(self):
        return self.label


class LeadSource(TenantModel):
    """
    Dynamic lead source values - allows tenant-specific source tracking.
    """
    source_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'web', 'event'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Web Form', 'Trade Show'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True)
    source_is_active = models.BooleanField(default=True, help_text="Whether this source is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    # Analytics tracking
    conversion_rate_target = models.FloatField(default=0.0, help_text="Target conversion rate (0-100)")
    
    class Meta:
        ordering = ['order', 'source_name']
        unique_together = [('tenant_id', 'source_name')]
        verbose_name_plural = 'Lead Sources'
    
    def __str__(self):
        return self.label


class LeadStatus(TenantModel):
    """
    Dynamic lead status values - allows tenant-specific lead workflows.
    """
    status_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'new', 'qualified'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'New Lead', 'Qualified'
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True)
    status_is_active = models.BooleanField(default=True, help_text="Whether this status is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    # Workflow flags
    is_qualified = models.BooleanField(default=False, help_text="Indicates lead is qualified")
    is_closed = models.BooleanField(default=False, help_text="Indicates lead is closed (won/lost)")
    
    class Meta:
        ordering = ['order', 'status_name']
        unique_together = [('tenant_id', 'status_name')]
        verbose_name_plural = 'Lead Statuses'
    
    def __str__(self):
        return self.label


class Lead(TenantModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255)
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)  # Temporary: keeping old field for backward compatibility
    job_title = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # New dynamic industry field
    industry_ref = models.ForeignKey(
        Industry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Dynamic industry (replaces industry field)",
        db_constraint=False
    )
    
    # Add missing fields
    lead_description = models.TextField(blank=True, help_text="Additional notes about the lead")
    title = models.CharField(max_length=255, blank=True, help_text="Custom title for the lead")
    
    # Fix field name consistency
    # Legacy choice fields (deprecated - use _ref fields instead)
    lead_source = models.CharField(max_length=20, choices=LEAD_SOURCE_CHOICES)  # Changed from 'source'
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default='new')
    lead_score = models.IntegerField(default=0)  # 0–100
    
    # New business metrics fields
    company_size = models.IntegerField(null=True, blank=True, help_text="Number of employees at the company")
    annual_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Annual revenue of the company")
    funding_stage = models.CharField(max_length=50, blank=True, help_text="Funding stage of the company (e.g., Series A, IPO)")
    business_type = models.CharField(max_length=50, blank=True, help_text="Business type (B2B, B2C, etc.)", default='B2B')
    
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
    # Marketing attribution fields
    cac_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Customer acquisition cost for this lead"
    )
    marketing_channel = models.CharField(
        max_length=20, 
        choices=MARKETING_CHANNEL_CHOICES, 
        blank=True,
        help_text="Marketing channel that brought this lead (legacy field)"
    )
    # New dynamic marketing channel field
    marketing_channel_ref = models.ForeignKey(
        'MarketingChannel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Dynamic marketing channel (replaces marketing_channel field)",
        db_constraint=False
    )
    campaign_source = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Specific campaign that generated this lead"
    )
    # Direct link to internal Campaign
    campaign_ref = models.ForeignKey(
        'marketing.Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Internal Campaign reference"
    )
    lead_acquisition_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date when the lead was acquired"
    )
    
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


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
        if self.lead_description:
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
            
            # Set lead acquisition date if not already set
            if not self.lead_acquisition_date:
                self.lead_acquisition_date = timezone.now()
            
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
                task_description="This lead needs initial review and potential outreach",
                assigned_to=self.owner,
                account=self.account,
                priority='low',
                status='todo',
                due_date=timezone.now() + timedelta(days=3),
                task_type='lead_review',
                tenant_id=self.tenant_id,
                lead=self
            )
            
        elif self.status == 'contacted':
            # Medium priority contact task
            Task.objects.create(
                title=f"Contact lead: {self.full_name}",
                task_description="Follow up with this lead based on their engagement score",
                assigned_to=self.owner,
                account=self.account,
                priority='medium',
                status='todo',
                due_date=timezone.now() + timedelta(days=1),
                task_type='lead_contact',
                tenant_id=self.tenant_id,
                lead=self
            )
            
        elif self.status == 'qualified':
            # High priority qualification task
            Task.objects.create(
                title=f"Qualify lead: {self.full_name}",
                task_description="This lead has high engagement score and needs immediate qualification",
                assigned_to=self.owner,
                account=self.account,
                priority='high',
                status='todo',
                due_date=timezone.now() + timedelta(hours=4),
                task_type='lead_qualify',
                tenant_id=self.tenant_id,
                lead=self
            )

    def calculate_cac(self):
        """Calculate Customer Acquisition Cost for this lead."""
        if self.cac_cost:
            return self.cac_cost
        return 0.0

    @classmethod
    def get_channel_metrics(cls, marketing_channel, tenant_id=None, use_ref=False):
        """Get performance metrics for a specific marketing channel."""
        queryset = cls.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        if use_ref:
            # Filter by marketing channel reference (new field)
            queryset = queryset.filter(marketing_channel_ref__channel_name=marketing_channel)
        else:
            # Filter by marketing channel (legacy field)
            queryset = queryset.filter(marketing_channel=marketing_channel)
        
        total_leads = queryset.count()
        total_cac = float(queryset.aggregate(total=models.Sum('cac_cost'))['total'] or 0)
        
        # Get converted leads for conversion rate
        converted_leads = queryset.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            'channel': marketing_channel,
            'total_leads': total_leads,
            'total_cac_spent': total_cac,
            'average_cac': total_cac / total_leads if total_leads > 0 else 0,
            'conversion_rate': conversion_rate,
            'converted_leads': converted_leads
        }

    @classmethod
    def get_channel_metrics_by_ref(cls, marketing_channel_ref_id, tenant_id=None):
        """Get performance metrics for a specific marketing channel reference."""
        queryset = cls.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
            
        queryset = queryset.filter(marketing_channel_ref_id=marketing_channel_ref_id)
        
        total_leads = queryset.count()
        total_cac = float(queryset.aggregate(total=models.Sum('cac_cost'))['total'] or 0)
        
        # Get converted leads for conversion rate
        converted_leads = queryset.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 10) if total_leads > 0 else 0
        
        # Get channel name for the response
        from .models import MarketingChannel
        try:
            channel = MarketingChannel.objects.get(id=marketing_channel_ref_id)
            channel_name = channel.channel_name
        except MarketingChannel.DoesNotExist:
            channel_name = "Unknown Channel"
        
        return {
            'channel': channel_name,
            'total_leads': total_leads,
            'total_cac_spent': total_cac,
            'average_cac': total_cac / total_leads if total_leads > 0 else 0,
            'conversion_rate': conversion_rate,
            'converted_leads': converted_leads
        }

    @classmethod
    def get_campaign_metrics(cls, campaign_source, tenant_id=None):
        """Get performance metrics for a specific campaign."""
        queryset = cls.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
            
        queryset = queryset.filter(campaign_source=campaign_source)
        
        total_leads = queryset.count()
        total_cac = float(queryset.aggregate(total=models.Sum('cac_cost'))['total'] or 0)
        
        # Get converted leads for conversion rate
        converted_leads = queryset.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            'campaign': campaign_source,
            'total_leads': total_leads,
            'total_cac_spent': total_cac,
            'average_cac': total_cac / total_leads if total_leads > 0 else 0,
            'conversion_rate': conversion_rate,
            'converted_leads': converted_leads
        }

    @classmethod
    def get_total_cac_by_period(cls, start_date, end_date, tenant_id=None):
        """Get total CAC for leads acquired within a specific period."""
        queryset = cls.objects.filter(
            lead_acquisition_date__date__gte=start_date,
            lead_acquisition_date__date__lte=end_date
        )
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        total_leads = queryset.count()
        total_cac = float(queryset.aggregate(total=models.Sum('cac_cost'))['total'] or 0)
        
        return {
            'period_start': start_date,
            'period_end': end_date,
            'total_leads': total_leads,
            'total_cac_spent': total_cac,
            'average_cac': total_cac / total_leads if total_leads > 0 else 0
        }


class WebToLeadForm(TenantModel):
    """
    Web-to-lead form configuration.
    """
    form_name = models.CharField(max_length=255, help_text="Name of the web-to-lead form")  # Renamed from 'name' to avoid conflict
    form_description = models.TextField(blank=True, help_text="Description of the form")  # Renamed from 'description' to avoid conflict
    form_is_active = models.BooleanField(default=True, help_text="Whether this form is active")  # Renamed from 'is_active' to avoid conflict
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
    

    
    @property
    def total_submissions(self):
        return self.submissions.count()
    
    @property
    def conversion_rate(self):
        if self.total_submissions == 0:
            return 0.0
        converted_leads = self.submissions.filter(lead__isnull=False).count()
        return (converted_leads / self.total_submissions) * 10
    
    def get_embed_code_url(self):
        return reverse('leads:webtoleadform_embed', kwargs={'pk': self.pk})

    def __str__(self):
        return self.form_name


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
    


    class Meta:
        unique_together = [('date', 'source', 'tenant')]

    def __str__(self):
        return f"{self.source} - {self.date}"

class AssignmentRule(TenantModel):
    """
    Assignment rules specifically for Leads.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="lead_assignment_rules"
    )
    RULE_TYPE_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('territory', 'Territory-Based'),
        ('load_balanced', 'Load Balanced'),
        ('criteria', 'Criteria-Based'),
    ]

    assignment_rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    # Dynamic field reference
    rule_type_ref = models.ForeignKey(
        AssignmentRuleType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lead_assignment_rules',
        help_text="Dynamic rule type (replaces rule_type field)"
    )
    criteria = models.JSONField(default=dict, blank=True, help_text="Matching criteria, e.g., {'country': 'US', 'industry': 'Tech'}")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lead_assigned_rules')
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    priority = models.IntegerField(default=1, help_text="Priority of the rule (lower numbers = higher priority)")

    def __str__(self):
        return self.assignment_rule_name


class ActionType(TenantModel):
    """
    Dynamic action type values - allows tenant-specific action type tracking.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="lead_action_types"
    )
    action_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'email_open', 'link_click'")
    label = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    action_type_is_active = models.BooleanField(default=True, help_text="Whether this action type is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'action_type_name']
        unique_together = [('tenant', 'action_type_name')]
        verbose_name_plural = 'Action Types'
    
    def __str__(self):
        return self.label


class OperatorType(TenantModel):
    """
    Dynamic operator type values - allows tenant-specific operator type tracking.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="lead_operator_types"
    )
    operator_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'equals', 'contains'")
    label = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    operator_is_active = models.BooleanField(default=True, help_text="Whether this operator is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'operator_name']
        unique_together = [('tenant', 'operator_name')]
        verbose_name_plural = 'Operator Types'
    
    def __str__(self):
        return self.label


class BehavioralScoringRule(TenantModel):
    ACTION_TYPE_CHOICES = [
        ('email_open', 'Email Open'),
        ('link_click', 'Link Click'),
        ('web_visit', 'Website Visit'),
        ('form_submit', 'Form Submission'),
        ('content_download', 'Content Download'),
        ('landing_page_visit', 'Landing Page Visit'),
    ]

    OPERATOR_CHOICES = [
        ('equals', 'Equals'),
        ('contains', 'Contains'),
        ('in', 'In List'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
    ]

    BUSINESS_IMPACT_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="lead_behavioral_scoring_rules"
    )

    behavioral_scoring_rule_name = models.CharField(max_length=200, help_text="Rule name, e.g., 'Email Open Scoring'")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    # New dynamic field
    action_type_ref = models.ForeignKey(
        ActionType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='behavioral_scoring_rules',
        help_text="Dynamic action type (replaces action_type field)"
    )
    points = models.IntegerField(help_text="Points to award for this action")
    time_decay_factor = models.FloatField(default=1.0, help_text="Multiplier for time-based decay of this action's value")
    business_impact = models.CharField(max_length=50, choices=BUSINESS_IMPACT_CHOICES)
    # New dynamic field
    business_impact_ref = models.ForeignKey(
        'self',  # Self reference for impact - this might need to be a separate model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='behavioral_scoring_rules_by_impact',
        help_text="Dynamic business impact (replaces business_impact field)"
    )
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")

    def __str__(self):
        return self.behavioral_scoring_rule_name


class DemographicScoringRule(TenantModel):
    OPERATOR_CHOICES = [
        ('equals', 'Equals'),
        ('contains', 'Contains'),
        ('in', 'In List'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
    ]

    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="lead_demographic_scoring_rules"
    )

    demographic_scoring_rule_name = models.CharField(max_length=200, help_text="Rule name, e.g., 'Job Title Scoring'")
    field_name = models.CharField(max_length=100, help_text="Field to evaluate, e.g., 'job_title', 'industry', 'company_size'")
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES, default='equals')
    # New dynamic field
    operator_ref = models.ForeignKey(
        OperatorType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='demographic_scoring_rules',
        help_text="Dynamic operator (replaces operator field)"
    )
    field_value = models.CharField(max_length=500, help_text="Value to match against")
    points = models.IntegerField(help_text="Points to award when condition is met")
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")

    def __str__(self):
        return self.demographic_scoring_rule_name

