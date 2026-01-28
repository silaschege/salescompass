from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from opportunities.models import Opportunity

PROPOSAL_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('viewed', 'Viewed'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
] 

class ApprovalStep(TenantModel):
    """
    Represents a step in the approval workflow.
    """
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.order + 1}. {self.name}"

class ApprovalTemplate(TenantModel):
    """
    Template for approval workflows that can be applied to proposals.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    steps = models.ManyToManyField(
        ApprovalStep,
        through='ApprovalTemplateStep',
        related_name='approval_templates'
    )
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name



class ApprovalTemplateStep(TenantModel):
    """
    Through model to order steps in an approval template.
    """
    template = models.ForeignKey(ApprovalTemplate, on_delete=models.CASCADE)
    step = models.ForeignKey(ApprovalStep, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.template.name} - Step {self.order + 1}: {self.step.name}"


class ProposalApproval(TenantModel):
    """
    Tracks the approval status of a proposal through the workflow.
    """
    proposal = models.ForeignKey(
        'Proposal', 
        on_delete=models.CASCADE, 
        related_name='approvals'
    )
    step = models.ForeignKey(
        ApprovalStep, 
        on_delete=models.CASCADE,
        related_name='proposal_approvals'
    )
    approved_by = models.ForeignKey(
        'core.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_proposals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    is_approved = models.BooleanField(null=True, blank=True)
    
    class Meta:
        ordering = ['step__order']
    
    def __str__(self):
        return f"{self.proposal.title} - {self.step.name}"

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
       # Approval workflow
    approval_template = models.ForeignKey(
        ApprovalTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposals',
        help_text="Optional approval template to use for this proposal"
    )
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


class ProposalTemplate(TenantModel):
    """
    Reusable email template for proposals.
    """
    email_template_name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    email_template_is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email_template_name


class ProposalEmail(TenantModel):
    """
    Record of sent proposal emails with tracking.
    """
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='emails')
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    tracking_enabled = models.BooleanField(default=True)
    email_template = models.ForeignKey(ProposalTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
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


class ProposalSignature(models.Model):
    """
    Stores digital signature information for proposals
    """
    proposal = models.OneToOneField(
        Proposal, 
        on_delete=models.CASCADE, 
        related_name='signature',
        unique=True
    )
    
    signature_data = models.TextField()
    signer_name = models.CharField(max_length=255)
    signer_title = models.CharField(max_length=255)
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    def __str__(self):
        return f"Signature for {self.proposal.title} by {self.signer_name}"

class ProposalLine(TenantModel):
    """
    Individual items (products/services) included in a proposal.
    Part of the CPQ (Configure, Price, Quote) system.
    """
    proposal = models.ForeignKey(
        Proposal, 
        on_delete=models.CASCADE, 
        related_name='lines'
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='proposal_lines'
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Configuration status (for CPQ rules)
    is_required_by_another = models.BooleanField(default=False)
    added_automatically = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['id']

    @property
    def line_total(self):
        total = self.unit_price * self.quantity
        if self.discount_percent:
            total -= (total * self.discount_percent / 100)
        return total

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity} in {self.proposal.title}"