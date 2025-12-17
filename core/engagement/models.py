# apps/engagement/
# ├── __init__.py
# ├── admin.py
# ├── apps.py
# ├── forms.py
# ├── models.py
# ├── urls.py
# ├── views.py
# ├── utils.py
# ├── tasks.py
# ├── consumers.py
# ├── routing.py
# └── templates/engagement/
#     ├── feed.html
#     ├── dashboard.html
#     ├── next_best_action.html
#     └── engagement_detail.html

from django.db import models
from tenants.models import Tenant as TenantModel
from core.models import User

from opportunities.models import Opportunity



ACTION_TYPES = [
    ('send_email', 'Send Email'),
    ('schedule_call', 'Schedule Call'),
    ('send_proposal', 'Send Proposal'),
    ('share_esg_brief', 'Share ESG Brief'),
    ('check_in', 'Check In'),
    ('create_task', 'Create Task'),
]


class EngagementEvent(TenantModel):
    """
    Unified activity log for all customer interactions.
    """
    EVENT_TYPES = [
        # RESTORE legacy event types so dashboards don’t break
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
    
    # Extended Event Types (Phase 2)
    ('social_interaction', 'Social Media Interaction'),
    ('website_visit', 'Website Visit'),
    ('document_view', 'Document Viewed'),
    ('webinar_attended', 'Webinar Attended'),
    ('support_ticket', 'Support Ticket Created'),
    ]
    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement_events')
    opportunity = models.ForeignKey(
        Opportunity, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='engagement_events'
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    engagement_event_description = models.TextField()
    title = models.CharField(max_length=255, blank=True)  # e.g., "Q3 Proposal Viewed"
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, null=True, blank=True)
    nps_response = models.ForeignKey('nps.NpsResponse', on_delete=models.CASCADE, null=True, blank=True)
    contact = models.ForeignKey('accounts.Contact', on_delete=models.CASCADE, null=True, blank=True)
    # Context
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # internal user
    contact_email = models.EmailField(blank=True)  # external contact
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')])
    is_important = models.BooleanField(default=False)
    internal_notes = models.TextField(blank=True, help_text="Private notes for internal team")
    # Metadata (structured data)
    metadata = models.JSONField(default=dict, blank=True)  # e.g., {'proposal_id': 123, 'duration_sec': 120}
    
    # Engagement scoring
    engagement_score = models.FloatField(default=0.0)  # 0–100
    is_important = models.BooleanField(default=False)  # for highlighting
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return f"{self.event_type} - {self.user.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            from automation.utils import emit_event
            
            # Emit generic event for all engagement events
            emit_event('engagement.event_logged', {
                'event_id': self.id,
                'event_type': self.event_type,
                'title': self.title,
                'user_id': self.user_id,
                'engagement_score': self.engagement_score,
                'tenant_id': self.tenant_id
            })
            
            # Emit milestone event for important events
            if self.is_important or self.engagement_score >= 80:
                emit_event('engagement.milestone', {
                    'event_id': self.id,
                    'event_type': self.event_type,
                    'title': self.title,
                    'user_id': self.user_id,
                    'engagement_score': self.engagement_score,
                    'tenant_id': self.tenant_id
                })

    @property
    def user_name(self):
        return self.user.name

    @property
    def opportunity_name(self):
        return self.opportunity.name if self.opportunity else None

    def get_event_data_for_websocket(self):
        """Get event data formatted for WebSocket broadcast."""
        return {
            'id': self.id,
            'user_id': self.user.id if self.user else None,
            'user_name': self.user.name if self.user else 'Unknown User',
            'title': self.title or f'{self.get_event_type_display()} Event',
            'event_type': self.get_event_type_display(),
            'engagement_score': self.engagement_score,
            'is_important': self.is_important,
            'created_at': self.created_at.isoformat(),
        }

class EngagementStatus(TenantModel):
    """
    Aggregated engagement status per account.
    """
    account = models.OneToOneField(User, on_delete=models.CASCADE, related_name='engagement_status')
    last_engaged_at = models.DateTimeField(null=True, blank=True)
    last_decay_calculation = models.DateTimeField(null=True, blank=True)
    engagement_score = models.FloatField(default=0.0)  # rolling 30-day score
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.name} - {self.engagement_score}"
    

class NextBestAction(TenantModel):
    """
    AI or rule-based recommended action for an user.
    """
    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='next_actions')
    opportunity = models.ForeignKey(
        Opportunity, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    contact = models.ForeignKey('accounts.Contact', on_delete=models.CASCADE, null=True, blank=True)
    next_best_action_description = models.TextField()
    due_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=100, blank=True)  # e.g., "ESG Engine", "Health Predictor"
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium'
    )
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')])
    engagement_event = models.ForeignKey('EngagementEvent', on_delete=models.CASCADE, null=True, blank=True)
    assigned_to = models.ForeignKey('core.User', on_delete=models.CASCADE)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return f"{self.action_type} for {self.user.name}"

    class Meta:
        ordering = ['-due_date', 'priority']


class EngagementWebhook(TenantModel):
    """
    Webhook configuration for external engagement data.
    """
    engagement_webhook_name = models.CharField(max_length=255)
    webhook_url = models.URLField()
    secret_key = models.CharField(max_length=255, blank=True)
    event_types = models.JSONField(default=list)  # e.g., ["web_visit", "social_mention"]
    engagement_webhook_is_active = models.BooleanField(default=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.engagement_webhook_name


class EngagementPlaybook(models.Model):
    """
    Standardized sequence of engagement actions (e.g., "Onboarding Sequence", "Re-engagement Plan").
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.name


class PlaybookStep(models.Model):
    """
    Individual step within a playbook.
    """
    playbook = models.ForeignKey(EngagementPlaybook, on_delete=models.CASCADE, related_name='steps')
    day_offset = models.PositiveIntegerField(help_text="Days after playbook start to perform this action")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField(help_text="Instructions for this step")
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium'
    )
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    class Meta:
        ordering = ['day_offset']

    def __str__(self):
        return f"Day {self.day_offset}: {self.get_action_type_display()} ({self.playbook.name})"


class WebhookDeliveryLog(models.Model):
    """
    Log of webhook delivery attempts for auditing and troubleshooting.
    """
    webhook = models.ForeignKey(EngagementWebhook, on_delete=models.CASCADE, related_name='delivery_logs')
    event = models.ForeignKey(EngagementEvent, on_delete=models.CASCADE, related_name='engagement_delivery_logs')
    # Store payload for debugging (be careful with PII, but EngagementEvent usually controls this)
    payload = models.JSONField(default=dict)
    
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    attempt_number = models.PositiveIntegerField(default=1)
    success = models.BooleanField(default=False)
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Manually add timestamp since not inheriting

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Log: {self.webhook.name} -> {self.event.id} ({'Success' if self.success else 'Failed'})"