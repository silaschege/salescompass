from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User, TimeStampedModel
from opportunities.models import Opportunity
from django.utils import timezone

ACTION_TYPES = [
    ('send_email', 'Send Email'),
    ('schedule_call', 'Schedule Call'),
    ('send_proposal', 'Send Proposal'),
    ('share_esg_brief', 'Share ESG Brief'),
    ('check_in', 'Check In'),
    ('create_task', 'Create Task'),
]

class EngagementEvent(TenantModel, TimeStampedModel):
    """
    Unified activity log for all customer interactions.
    """
    EVENT_TYPES = [
    ('task_lead_contact_completed', 'Lead Contact Completed'),
    ('task_lead_review_completed', 'Task Lead Review Completed'),
    ('task_lead_qualify_completed', 'Lead Qualification Completed'),
    ('task_opportunity_demo_completed', 'Opportunity Demo Completed'),
    ('task_case_escalation_completed', 'Case Escalation Completed'),
    ('task_user_followup_completed', 'User Follow-up Completed'),
    ('task_proposal_followup_completed', 'Proposal Follow-up Completed'),

    ('lead_created', 'Lead Created'),
    ('lead_contacted', 'Lead Contacted'),
    ('user_followup_completed', 'User Follow-up Completed'),
    ('demo_completed', 'Demo Completed'),
    ('case_escalation_handled', 'Case Escalation Handled'),
    ('detractor_followup_completed', 'Detractor Follow-up Completed'),
    ('proposal_viewed', 'Proposal Viewed'),
    ('email_opened', 'Email Opened'),
    ('link_clicked', 'Link Clicked'),
    ('landing_page_visited', 'Landing Page Visited'),
    ('form_submitted', 'Form Submitted'),
    ('content_downloaded', 'Content Downloaded'),
    ('renewal_reminder', 'Renewal Reminder'),
    ('nps_submitted', 'NPS Submitted'),
    
    ('social_interaction', 'Social Media Interaction'),
    ('website_visit', 'Website Visit'),
    ('document_view', 'Document Viewed'),
    ('webinar_attended', 'Webinar Attended'),
    ('support_ticket', 'Support Ticket Created'),
    ('video_viewed', 'Video Viewed'),
    ('video_watched_full', 'Video Watched Completely'),
    ('forum_post_created', 'Forum Post Created'),
    ('forum_reply_created', 'Forum Reply Created'),
    ('product_usage_session', 'Product Usage Session'),
    ('feature_used', 'Specific Feature Used'),
    ('login_event', 'User Login'),
    ('page_view_duration', 'Page View Duration'),
    
    ('whatsapp_sent', 'WhatsApp Message Sent'),
    ('linkedin_inmail_tracked', 'LinkedIn InMail Tracked'),
    ('payment_received', 'Payment Received'),
    ('course_completed', 'Learning Course Completed'),
    ('win_probability_update', 'Win Probability Update'),
    ('task_assigned', 'Task Assigned'),
    
    ('opportunity_created', 'Opportunity Created'),
    ('opportunity_stage_changed', 'Opportunity Stage Changed'),
    ('opportunity_won', 'Opportunity Won'),
    ('opportunity_lost', 'Opportunity Lost'),
    ('lead_qualified', 'Lead Qualified'),
    ('lead_unqualified', 'Lead Unqualified'),
    ('lead_converted', 'Lead Converted'),
    ('case_resolved', 'Case Resolved'),
    ('proposal_accepted', 'Proposal Accepted'),
    ('proposal_rejected', 'Proposal Rejected'),
    ('proposal_sent', 'Proposal Sent'),
    ('whatsapp_delivered', 'WhatsApp Delivered'),
    ('whatsapp_read', 'WhatsApp Read'),
    ('linkedin_message_read', 'LinkedIn Message Read'),
    ('account_created', 'Account Created'),
    ('account_owner_changed', 'Account Owner Changed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement_events', null=True, blank=True)
    account_company = models.ForeignKey(
        'accounts.Account', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='engagement_events'
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField()
    title = models.CharField(max_length=255, blank=True)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, null=True, blank=True)
    nps_response = models.ForeignKey('nps.NpsResponse', on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey('accounts.Contact', on_delete=models.CASCADE, null=True, blank=True)
    lead = models.ForeignKey('leads.Lead', on_delete=models.CASCADE, null=True, blank=True, related_name='engagement_events')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, null=True, blank=True, related_name='engagement_events')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='engagement_events')
    proposal = models.ForeignKey('proposals.Proposal', on_delete=models.CASCADE, null=True, blank=True, related_name='engagement_events')
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    internal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    contact_email = models.EmailField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    engagement_score = models.FloatField(default=0.0)
    is_important = models.BooleanField(default=False)

    utm_source = models.CharField(max_length=255, blank=True, null=True)
    utm_medium = models.CharField(max_length=255, blank=True, null=True)
    utm_campaign = models.CharField(max_length=255, blank=True, null=True)
    utm_term = models.CharField(max_length=255, blank=True, null=True)
    utm_content = models.CharField(max_length=255, blank=True, null=True)
    referrer_url = models.URLField(blank=True, null=True)
    referring_domain = models.CharField(max_length=255, blank=True, null=True)
    campaign_name = models.CharField(max_length=255, blank=True, null=True)
    campaign_source = models.CharField(max_length=255, blank=True, null=True)
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_engagement_events')
    mentions = models.ManyToManyField(User, blank=True, related_name='mentioned_in_engagement_events')
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not any([self.account_company, self.lead, self.contact]):
            raise ValidationError("At least one target entity (Account, Lead, or Contact) must be linked to the event.")
        if not (0 <= self.engagement_score <= 100):
            raise ValidationError("Engagement score must be between 0 and 100.")

    @property
    def primary_entity(self):
        """Returns the primary CRM entity associated with this event."""
        if self.contact:
            return self.contact
        if self.lead:
            return self.lead
        if self.account_company:
            return self.account_company
        if self.account:
            return self.account
        return None

    @property
    def primary_entity_name(self):
        """Returns the name of the primary entity."""
        entity = self.primary_entity
        if not entity:
            return "Unknown Entity"
        
        if hasattr(entity, 'get_full_name'):
            return entity.get_full_name()
        if hasattr(entity, 'name'):
            return entity.name
        if hasattr(entity, 'first_name') and hasattr(entity, 'last_name'):
            return f"{entity.first_name} {entity.last_name}"
        return str(entity)

    @property
    def icon(self):
        """Returns a Bootstrap icon class based on the event type."""
        icon_map = {
            'email_sent': 'bi-envelope',
            'email_opened': 'bi-envelope-open',
            'link_clicked': 'bi-link-45deg',
            'call_completed': 'bi-telephone',
            'lead_created': 'bi-person-plus',
            'lead_contacted': 'bi-person-lines-fill',
            'whatsapp_sent': 'bi-whatsapp',
            'whatsapp_received': 'bi-whatsapp',
            'task_assigned': 'bi-list-task',
            'opportunity_created': 'bi-gem',
            'opportunity_won': 'bi-trophy',
            'proposal_sent': 'bi-file-earmark-text',
            'nps_submitted': 'bi-star',
            'website_visit': 'bi-globe',
        }
        # Default icon if not in map
        return icon_map.get(self.event_type, 'bi-record-circle')

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.primary_entity_name}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        if not self.pk:
            from automation.utils import emit_event
            emit_event('engagement.event_logged', {
                'event_id': self.id,
                'event_type': self.event_type,
                'title': self.title,
                'account_id': self.account.id if self.account else None,
                'engagement_score': self.engagement_score,
                'tenant_id': self.tenant_id
            })

    def get_event_data_for_websocket(self):
        """Return serialized data for WebSocket consumers."""
        return {
            "id": self.id,
            "account_name": self.account.get_full_name() if self.account else "Unknown",
            "title": self.title,
            "description": self.description,
            "event_type": self.get_event_type_display(),
            "created_at": self.created_at.isoformat(),
            "is_important": self.is_important,
            "engagement_score": self.engagement_score,
            "icon_class": self.get_icon_class()
        }

    def get_icon_class(self):
        """Return FontAwesome icon class based on event type."""
        if 'email' in self.event_type: return 'fas fa-envelope'
        if 'call' in self.event_type: return 'fas fa-phone'
        if 'meeting' in self.event_type: return 'fas fa-calendar-check'
        if 'opportunity' in self.event_type: return 'fas fa-trophy'
        if 'case' in self.event_type: return 'fas fa-ticket-alt'
        return 'fas fa-stream'

class EngagementStatus(TenantModel, TimeStampedModel):
    account = models.OneToOneField(User, on_delete=models.CASCADE, related_name='engagement_status')
    last_engaged_at = models.DateTimeField(null=True, blank=True)
    last_decay_calculation = models.DateTimeField(null=True, blank=True)
    engagement_score = models.FloatField(default=0.0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.account.email} - {self.engagement_score}"

class NextBestAction(TenantModel, TimeStampedModel):
    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='next_actions')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    contact = models.ForeignKey('accounts.Contact', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium')
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')], default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_nb_actions')
    collaborators = models.ManyToManyField(User, blank=True, related_name='collaborating_on_nb_actions')
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_action_type_display()} for {self.account.email}"

class AutoNBARule(TenantModel, TimeStampedModel):
    rule_name = models.CharField(max_length=255)
    trigger_event = models.CharField(max_length=50, choices=[
        ('low_engagement_score', 'Low Engagement Score'),
        ('no_engagement_7_days', 'No Engagement for 7 Days'),
        ('proposal_viewed', 'Proposal Viewed'),
        ('high_engagement_score', 'High Engagement Score'),
        ('nps_submitted_promoter', 'NPS Promoter (9-10)'),
        ('nps_submitted_detractor', 'NPS Detractor (0-6)'),
        ('email_opened', 'Email Opened'),
        ('link_clicked', 'Link Clicked'),
    ])
    auto_nba_is_active = models.BooleanField(default=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description_template = models.TextField()
    due_in_days = models.IntegerField(default=7)
    priority = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium')
    assigned_to_creator = models.BooleanField(default=False)

    def __str__(self):
        return self.rule_name

class EngagementWebhook(TenantModel, TimeStampedModel):
    engagement_webhook_name = models.CharField(max_length=255)
    webhook_url = models.URLField()
    secret_key = models.CharField(max_length=255, blank=True)
    event_types = models.JSONField(default=list)
    engagement_webhook_is_active = models.BooleanField(default=True)
    payload_template = models.TextField(blank=True)
    http_method = models.CharField(max_length=10, choices=[('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH')], default='POST')
    headers = models.JSONField(default=dict, blank=True)
    timeout_seconds = models.IntegerField(default=30)
    max_retry_attempts = models.IntegerField(default=3)
    initial_retry_delay = models.IntegerField(default=5)
    retry_backoff_factor = models.FloatField(default=2.0)
    retry_on_status_codes = models.JSONField(default=list, blank=True)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.engagement_webhook_name

class EngagementWorkflow(TenantModel, TimeStampedModel):
    workflow_name = models.CharField(max_length=255)
    workflow_description = models.TextField(blank=True)
    workflow_type = models.CharField(max_length=50, choices=[
        ('email_sequence', 'Email Sequence'),
        ('task_creation', 'Task Creation'),
        ('escalation', 'Escalation Workflow'),
        ('notification', 'Notification'),
    ])
    trigger_condition = models.CharField(max_length=50, choices=[
        ('low_engagement', 'Low Engagement Score'),
        ('high_engagement', 'High Engagement Score'),
        ('inactivity', 'Account Inactivity'),
        ('milestone', 'Engagement Milestone'),
        ('nps_promoter', 'NPS Promoter'),
        ('nps_detractor', 'NPS Detractor'),
        ('high_video_engagement', 'High Video Engagement'),
        ('forum_activity', 'Forum Activity'),
        ('product_power_user', 'Product Power User'),
    ])
    engagement_work_flow_is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    email_template_ids = models.JSONField(default=list, blank=True)
    delay_between_emails = models.IntegerField(default=1)
    task_title_template = models.CharField(max_length=255, blank=True)
    task_description_template = models.TextField(blank=True)
    task_due_date_offset = models.IntegerField(default=7)
    task_priority = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium')
    escalation_recipients = models.JSONField(default=list, blank=True)
    escalation_delay = models.IntegerField(default=2)

    def __str__(self):
        return self.workflow_name

class EngagementWorkflowExecution(TenantModel, TimeStampedModel):
    workflow = models.ForeignKey(EngagementWorkflow, on_delete=models.CASCADE, related_name='executions')
    engagement_event = models.ForeignKey(EngagementEvent, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.workflow.workflow_name} - {self.account.email}"

class EngagementPlaybook(TenantModel, TimeStampedModel):
    INDUSTRY_CHOICES = [
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('education', 'Education'),
        ('government', 'Government'),
        ('nonprofit', 'Non-Profit'),
        ('other', 'Other'),
    ]
    
    PLAYBOOK_TYPES = [
        ('standard', 'Standard'),
        ('industry_best_practice', 'Industry Best Practice'),
        ('template', 'Template'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=50, null=True, blank=True, choices=INDUSTRY_CHOICES)
    playbook_type = models.CharField(max_length=50, choices=PLAYBOOK_TYPES, default='standard')
    is_active = models.BooleanField(default=True)
    is_template = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    times_used = models.PositiveIntegerField(default=0)
    average_completion_rate = models.FloatField(default=0.0)
    average_effectiveness_score = models.FloatField(default=0.0)

    def __str__(self):
        return self.name

class PlaybookStep(models.Model): # Note: This one doesn't necessarily need TenantModel if Playbook has it, but consistency is better.
    playbook = models.ForeignKey(EngagementPlaybook, on_delete=models.CASCADE, related_name='steps')
    day_offset = models.PositiveIntegerField()
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium')
    times_completed = models.PositiveIntegerField(default=0)
    times_skipped = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['day_offset']

    def __str__(self):
        return f"{self.playbook.name} - Step {self.day_offset}"

class PlaybookExecution(TenantModel, TimeStampedModel):
    playbook = models.ForeignKey(EngagementPlaybook, on_delete=models.CASCADE)
    account = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('partially_completed', 'Partially Completed'),
        ('abandoned', 'Abandoned'),
    ], default='not_started')
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_rate = models.FloatField(default=0.0)
    effectiveness_score = models.FloatField(default=0.0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.playbook.name} - {self.account.email}"

class PlaybookStepExecution(TenantModel, TimeStampedModel):
    playbook_execution = models.ForeignKey(PlaybookExecution, on_delete=models.CASCADE, related_name='step_executions')
    step = models.ForeignKey(PlaybookStep, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ], default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.playbook_execution} - Step {self.step.day_offset}"

class EngagementEventComment(TenantModel, TimeStampedModel):
    engagement_event = models.ForeignKey(EngagementEvent, on_delete=models.CASCADE, related_name='event_comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"Comment by {self.user.email} on {self.engagement_event.id}"

class NextBestActionComment(TenantModel, TimeStampedModel):
    next_best_action = models.ForeignKey(NextBestAction, on_delete=models.CASCADE, related_name='action_comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"Comment by {self.user.email} on {self.next_best_action.id}"

class ScoringRule(models.Model):
    tenant_id = models.CharField(max_length=50, db_index=True)
    event_type = models.CharField(max_length=50, choices=EngagementEvent.EVENT_TYPES)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    rule_is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Scoring Rules'

class EngagementScoringConfig(models.Model):
    tenant_id = models.CharField(max_length=50, db_index=True, unique=True)
    decay_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.05)
    decay_period_days = models.IntegerField(default=7)
    inactivity_threshold_days = models.IntegerField(default=14)
    rolling_window_days = models.IntegerField(default=30)

    # Specific Action Scores
    email_open_score = models.FloatField(default=1.0)
    link_click_score = models.FloatField(default=3.0)
    reply_score = models.FloatField(default=5.0)
    meeting_score = models.FloatField(default=10.0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class EngagementScoreSnapshot(models.Model):
    tenant_id = models.CharField(max_length=50, db_index=True)
    account = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date']

class WebhookDeliveryLog(models.Model):
    tenant_id = models.CharField(max_length=50, db_index=True)
    webhook = models.ForeignKey(EngagementWebhook, on_delete=models.CASCADE, related_name='delivery_logs')
    payload = models.JSONField(default=dict)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    success = models.BooleanField(default=False)
    request_headers = models.JSONField(default=dict, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    signature = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class EngagementExperiment(TenantModel, TimeStampedModel):
    """
    Model for A/B testing engagement strategies.
    
    Allows creating experiments to test different engagement approaches (e.g., subject lines, 
    send times, content variations) and measuring their effectiveness.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    experiment_type = models.CharField(max_length=50, choices=[
        ('email_subject', 'Email Subject Line'),
        ('email_content', 'Email Content'),
        ('send_time', 'Send Time'),
        ('channel', 'Communication Channel'),
        ('cta', 'Call to Action'),
        ('workflow_path', 'Workflow Path'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ], default='draft')
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Success metrics
    primary_metric = models.CharField(max_length=50, choices=[
        ('open_rate', 'Open Rate'),
        ('click_rate', 'Click Rate'),
        ('reply_rate', 'Reply Rate'),
        ('conversion_rate', 'Conversion Rate'),
        ('engagement_score', 'Engagement Score Increase'),
    ])
    
    target_sample_size = models.PositiveIntegerField(help_text="Target number of participants per variant")
    current_sample_size = models.PositiveIntegerField(default=0)
    
    winner_variant = models.ForeignKey('ExperimentVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='won_experiments')
    confidence_level = models.FloatField(default=0.0, help_text="Statistical confidence level of the result")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_experiments')
    
    def __str__(self):
        return self.name

class ExperimentVariant(TenantModel, TimeStampedModel):
    """
    A specific variation within an experiment (e.g., control vs treatment).
    """
    experiment = models.ForeignKey(EngagementExperiment, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255, help_text="e.g., 'Variant A', 'Control Group'")
    description = models.TextField(blank=True)
    is_control = models.BooleanField(default=False)
    
    # Configuration for this variant
    config = models.JSONField(default=dict, blank=True, help_text="Specific configuration for this variant (e.g., subject line text)")
    
    # Performance Stats
    participants_count = models.PositiveIntegerField(default=0)
    conversions_count = models.PositiveIntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"{self.experiment.name} - {self.name}"
