"""
WhatsApp Models for SalesCompass Communication Module.
Provides dedicated models for tracking WhatsApp Business API messages.
"""
from django.db import models
from django.utils import timezone
from tenants.models import TenantAwareModel
from core.models import User


class WhatsAppConfiguration(TenantAwareModel):
    """
    Tenant-specific WhatsApp Business API configuration.
    Stores credentials and settings for WhatsApp integration.
    """
    
    name = models.CharField(max_length=100, help_text="Configuration name (e.g., 'Main Business Line')")
    phone_number = models.CharField(max_length=20, help_text="WhatsApp Business phone number with country code")
    phone_number_id = models.CharField(max_length=50, blank=True, help_text="WhatsApp Phone Number ID from Meta")
    business_account_id = models.CharField(max_length=50, blank=True, help_text="WhatsApp Business Account ID")
    
    # API Configuration (for direct Meta API usage, Wazo handles this internally)
    api_token = models.TextField(blank=True, help_text="Encrypted API access token")
    webhook_verify_token = models.CharField(max_length=100, blank=True, help_text="Webhook verification token")
    
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text="Primary number for outbound messages")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "WhatsApp Configuration"
        verbose_name_plural = "WhatsApp Configurations"
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary per tenant
            WhatsAppConfiguration.objects.filter(
                tenant=self.tenant, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class WhatsAppMessage(TenantAwareModel):
    """
    Track all WhatsApp messages sent/received through the WhatsApp Business API.
    Links messages to CRM entities for comprehensive communication tracking.
    """
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('template', 'Template'),
        ('image', 'Image'),
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('location', 'Location'),
        ('contact', 'Contact'),
        ('interactive', 'Interactive'),
    ]
    
    # Message identification
    message_id = models.CharField(max_length=100, unique=True, db_index=True, help_text="WhatsApp message ID (wamid)")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    
    # Phone numbers
    from_number = models.CharField(max_length=20, db_index=True)
    to_number = models.CharField(max_length=20, db_index=True)
    
    # Content
    body = models.TextField(blank=True, help_text="Message text content")
    caption = models.TextField(blank=True, help_text="Media caption if applicable")
    media_url = models.URLField(max_length=500, blank=True, help_text="URL to media file")
    media_mime_type = models.CharField(max_length=100, blank=True)
    
    # Template message fields
    template_name = models.CharField(max_length=100, blank=True, help_text="WhatsApp template name if template message")
    template_language = models.CharField(max_length=10, blank=True, default='en')
    template_variables = models.JSONField(default=list, blank=True, help_text="Template variable values")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_code = models.CharField(max_length=20, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # CRM Entity linking
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='whatsapp_messages',
        help_text="User who sent/handled this message"
    )
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='whatsapp_messages'
    )
    contact = models.ForeignKey(
        'accounts.Contact',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='whatsapp_messages'
    )
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='whatsapp_messages'
    )
    opportunity = models.ForeignKey(
        'opportunities.Opportunity',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='whatsapp_messages'
    )
    
    # Configuration reference
    configuration = models.ForeignKey(
        WhatsAppConfiguration,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='messages'
    )
    
    # Raw API data
    wazo_data = models.JSONField(default=dict, blank=True, help_text="Raw Wazo/WhatsApp API response")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "WhatsApp Message"
        verbose_name_plural = "WhatsApp Messages"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['from_number']),
            models.Index(fields=['to_number']),
            models.Index(fields=['status']),
            models.Index(fields=['direction', 'status']),
        ]
    
    def __str__(self):
        preview = self.body[:50] + '...' if len(self.body) > 50 else self.body
        return f"{self.direction}: {self.from_number} → {self.to_number}: {preview}"
    
    def mark_sent(self):
        """Update status to sent with timestamp."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_delivered(self):
        """Update status to delivered with timestamp."""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])
    
    def mark_read(self):
        """Update status to read with timestamp."""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])
    
    def mark_failed(self, error_code='', error_message=''):
        """Update status to failed with error details."""
        self.status = 'failed'
        self.error_code = error_code
        self.error_message = error_message
        self.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])


class WhatsAppTemplate(TenantAwareModel):
    """
    Store approved WhatsApp message templates for the tenant.
    Templates must be approved by Meta before use.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    CATEGORY_CHOICES = [
        ('marketing', 'Marketing'),
        ('utility', 'Utility'),
        ('authentication', 'Authentication'),
    ]
    
    template_name = models.CharField(max_length=100, help_text="Template name (must match Meta's template name)")
    template_id = models.CharField(max_length=50, blank=True, help_text="Meta template ID")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='utility')
    language = models.CharField(max_length=10, default='en')
    
    # Template content
    header_text = models.TextField(blank=True, help_text="Template header text")
    body_text = models.TextField(help_text="Template body text with {{1}}, {{2}} placeholders")
    footer_text = models.TextField(blank=True, help_text="Template footer text")
    
    # Button configuration
    buttons = models.JSONField(default=list, blank=True, help_text="Button configurations")
    
    # Variables info
    variable_count = models.IntegerField(default=0, help_text="Number of variables in template")
    variable_examples = models.JSONField(default=list, blank=True, help_text="Example values for variables")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "WhatsApp Template"
        verbose_name_plural = "WhatsApp Templates"
        unique_together = ['tenant', 'template_name', 'language']
        ordering = ['category', 'template_name']
    
    def __str__(self):
        return f"{self.template_name} ({self.language}) - {self.get_status_display()}"
