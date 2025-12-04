from django.db import models
from core.models import TenantModel
from core.models import User
from accounts.models import Account

CAMPAIGN_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('scheduled', 'Scheduled'),
    ('sending', 'Sending'),
    ('sent', 'Sent'),
    ('paused', 'Paused'),
    ('cancelled', 'Cancelled'),
]

EMAIL_PROVIDER_CHOICES = [
    ('ses', 'Amazon SES'),
    ('sendgrid', 'SendGrid'),
    ('mailgun', 'Mailgun'),
    ('native', 'Django Email'),
]
class MarketingCampaign(TenantModel):
    """
    Marketing campaign container.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='draft')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Scheduling
    send_date = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Targeting
    target_list = models.JSONField(default=list, blank=True)  # list of account IDs
    segment_filter = models.JSONField(default=dict, blank=True)  # e.g., {"industry": "tech"}
    
    # Analytics
    total_sent = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_replied = models.IntegerField(default=0)
    roi = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.name


class LandingPage(TenantModel):
    """
    Marketing landing page.
    """
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='landing_pages')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    html_content = models.TextField()
    is_published = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    conversions = models.IntegerField(default=0)  # form submissions
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def get_absolute_url(self):
        return f"/marketing/landing/{self.slug}/"

    def __str__(self):
        return self.title

class LandingPageBlock(TenantModel): 
    """
    Individual block/content section for landing pages.
    """
    BLOCK_TYPES = [
        ('hero', 'Hero Section'),
        ('features', 'Features'),
        ('testimonials', 'Testimonials'),
        ('pricing', 'Pricing'),
        ('cta', 'Call to Action'),
        ('faq', 'FAQ'),
        ('text', 'Text Content'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('form', 'Contact Form'),
    ]
    
    landing_page = models.ForeignKey(LandingPage, on_delete=models.CASCADE, related_name='blocks')
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPES)
    content = models.JSONField(default=dict, blank=True)  # Block-specific content
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    title=models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.get_block_type_display()} - {self.landing_page.title}"
    


class EmailTemplate(TenantModel):
    """
    Reusable email template with merge tag support.
    Enhanced for Template Builder functionality.
    """
    CATEGORY_CHOICES = [
        ('newsletter', 'Newsletter'),
        ('transactional', 'Transactional'),
        ('follow_up', 'Follow-up'),
        ('welcome', 'Welcome'),
        ('reminder', 'Reminder'),
        ('promotional', 'Promotional'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    subject_line = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField(blank=True, help_text="Plain text version for email clients that don't support HTML")
    
    # Template Builder enhancements
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, help_text="Description of template purpose and usage")
    is_shared = models.BooleanField(default=False, help_text="Share with all users in tenant")
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0, help_text="Number of times this template has been used")
    
    # Merge tags configuration
    merge_tags = models.JSONField(
        default=dict,
        blank=True,
        help_text="Available merge tags for this template, e.g., {'first_name': 'John', 'company': 'Acme Corp'}"
    )
    
    # Ownership
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_templates')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['tenant_id', 'is_shared']),
        ]

    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """Increment usage counter when template is used."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class MessageTemplate(TenantModel):
    """
    Reusable message template for SMS, in-app messages, and push notifications.
    Part of Template Builder system.
    """
    MESSAGE_TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('in_app', 'In-App Message'),
        ('push', 'Push Notification'),
        ('slack', 'Slack Message'),
    ]
    
    CATEGORY_CHOICES = [
        ('reminder', 'Reminder'),
        ('notification', 'Notification'),
        ('alert', 'Alert'),
        ('update', 'Update'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField(help_text="Message content with merge tag support")
    
    # Template Builder enhancements
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    is_shared = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    # Merge tags configuration  
    merge_tags = models.JSONField(default=dict, blank=True)
    
    # Ownership
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_message_templates')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_type', 'category']),
            models.Index(fields=['tenant_id', 'is_shared']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_message_type_display()})"
    
    def increment_usage(self):
        """Increment usage counter when template is used."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])



class EmailCampaign(TenantModel):
    """
    Email campaign instance.
    """
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='email_campaigns')
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    from_email = models.EmailField()
    reply_to = models.EmailField(blank=True)
    email_provider = models.CharField(max_length=20, choices=EMAIL_PROVIDER_CHOICES, default='native')
    
    # Tracking
    tracking_enabled = models.BooleanField(default=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Email for {self.campaign.name}"





class CampaignRecipient(TenantModel):
    """
    Individual recipient of a campaign.
    """
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('opened', 'Opened'),
            ('clicked', 'Clicked'),
            ('bounced', 'Bounced'),
            ('unsubscribed', 'Unsubscribed'),
        ],
        default='pending'
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('campaign', 'email')]

    def __str__(self):
        return f"{self.email} - {self.campaign.name}"

class CampaignPerformance(TenantModel):
    """
    Daily performance snapshot for campaigns.
    Tracks key metrics for ROI analysis and trend reporting.
    """
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='performance_snapshots')
    date = models.DateField()
    open_rate = models.FloatField(default=0.0, help_text="Percentage of emails opened")
    click_rate = models.FloatField(default=0.0, help_text="Percentage of emails clicked")
    conversion_rate = models.FloatField(default=0.0, help_text="Percentage of conversions")
    total_sent = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_conversions = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    
    class Meta:
        unique_together = [('campaign', 'date')]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['campaign', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.campaign.name} - {self.date}"

class AbTest(TenantModel):
    """
    A/B test for marketing campaigns.
    """
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.CASCADE, related_name='ab_tests')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    winner_variant = models.CharField(max_length=10, blank=True)  # 'A' or 'B'
    min_responses = models.IntegerField(default=1000)
    confidence_level = models.FloatField(default=0.95)

    def __str__(self):
        return f"{self.campaign.name} - {self.name}"


class AbVariant(TenantModel):
    """
    Variant for A/B test.
    """
    VARIANT_CHOICES = [('A', 'Variant A'), ('B', 'Variant B')]
    
    ab_test = models.ForeignKey(AbTest, on_delete=models.CASCADE, related_name='variants')
    variant = models.CharField(max_length=1, choices=VARIANT_CHOICES)
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    landing_page = models.ForeignKey(LandingPage, on_delete=models.SET_NULL, null=True, blank=True)
    assignment_rate = models.FloatField(default=0.5)


class Unsubscribe(TenantModel):
    """
    GDPR-compliant unsubscribe tracking.
    """
    email = models.EmailField()
    campaign = models.ForeignKey(MarketingCampaign, on_delete=models.SET_NULL, null=True, blank=True)
    unsubscribed_at = models.DateTimeField(auto_now_add=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    class Meta:
        unique_together = [('email', 'tenant_id')]

    def __str__(self):
        return f"{self.email} unsubscribed"


class DripCampaign(TenantModel):
    """
    Automated email sequence (drip campaign).
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return self.name


class DripStep(TenantModel):
    """
    Step in a drip campaign.
    """
    STEP_TYPES = [
        ('email', 'Send Email'),
        ('wait', 'Wait'),
    ]
    drip_campaign = models.ForeignKey(DripCampaign, on_delete=models.CASCADE, related_name='steps')
    step_type = models.CharField(max_length=20, choices=STEP_TYPES)
    order = models.IntegerField(default=0)
    
    # For email steps
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # For wait steps
    wait_days = models.IntegerField(default=0, help_text="Days to wait before next step")
    wait_hours = models.IntegerField(default=0, help_text="Hours to wait before next step")
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.get_step_type_display()} - {self.drip_campaign.name}"


class DripEnrollment(TenantModel):
    """
    Enrollment of an account/email in a drip campaign.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    drip_campaign = models.ForeignKey(DripCampaign, on_delete=models.CASCADE, related_name='enrollments')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    email = models.EmailField()
    
    current_step = models.ForeignKey(DripStep, on_delete=models.SET_NULL, null=True, blank=True)
    next_execution_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    def __str__(self):
        return f"{self.email} in {self.drip_campaign.name}"