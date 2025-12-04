from django.db import models
from core.models import TenantModel
from core.models import User
from accounts.models import Account
from opportunities.models import Opportunity

PROPOSAL_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('viewed', 'Viewed'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
]

class Proposal(TenantModel):
    """
    Sales proposal linked to an opportunity.
    Tracks engagement and ESG interaction.
    """
    title = models.CharField(max_length=255)
    opportunity = models.ForeignKey(
        Opportunity, 
        on_delete=models.CASCADE, 
        related_name='proposals'
    )
    status = models.CharField(max_length=20, choices=PROPOSAL_STATUS_CHOICES, default='draft')
    
    # Content (in prod, use FileField or HTML template system)
    content = models.TextField(help_text="HTML or Markdown content of the proposal")
    esg_section_content = models.TextField(blank=True, help_text="ESG-specific content")
    
    # Engagement tracking
    view_count = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)
    total_view_time_sec = models.IntegerField(default=0)
    esg_section_viewed = models.BooleanField(default=False)
    
    # Email tracking
    email_opened = models.BooleanField(default=False)
    email_opened_at = models.DateTimeField(null=True, blank=True)
    email_click_count = models.IntegerField(default=0)
    
    # Metadata
    sent_by = models.ForeignKey(
        'core.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_proposals'
    )
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def engagement_score(self):
        """Composite score based on views and time."""
        time_score = min(50, self.total_view_time_sec / 60)  # 1 point per minute, max 50
        view_score = min(50, self.view_count * 10)           # 10 points per view, max 50
        return time_score + view_score


class ProposalEvent(TenantModel):
    """
    Detailed engagement events (for analytics).
    """
    EVENT_TYPES = [
        ('opened', 'Proposal Opened'),
        ('esg_viewed', 'ESG Section Viewed'),
        ('downloaded', 'Proposal Downloaded'),
        ('shared', 'Proposal Shared'),
        ('email_opened', 'Email Opened'),
        ('link_clicked', 'Link Clicked'),
    ]
    
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    duration_sec = models.IntegerField(default=0)  # for 'opened' events
    link_url = models.URLField(blank=True)  # for 'link_clicked' events

    def __str__(self):
        return f"{self.event_type} - {self.proposal.title}"


class EmailTemplate(TenantModel):
    """
    Reusable email template for proposals.
    """
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    is_active = models.BooleanField(default=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.name


class ProposalEmail(TenantModel):
    """
    Record of sent proposal emails with tracking.
    """
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='emails')
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    tracking_enabled = models.BooleanField(default=True)
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking tokens
    open_tracking_token = models.CharField(max_length=100, unique=True)
    click_tracking_token = models.CharField(max_length=100, unique=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Email for {self.proposal.title} to {self.recipient_email}"


class ProposalPDF(TenantModel):
    """
    Generated PDF versions of proposals.
    """
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='pdfs')
    file = models.FileField(upload_to='proposal_pdfs/')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    page_count = models.IntegerField(default=0)

    def __str__(self):
        return f"PDF for {self.proposal.title}"