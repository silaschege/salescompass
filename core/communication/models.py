from django.db import models
from django.utils import timezone
from core.models import User
from tenants.models import Tenant, TenantAwareModel


class NotificationTemplate(models.Model):
    """Model for notification templates"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the notification template")
    description = models.TextField(blank=True, help_text="Description of when this template is used")
    template_type = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('microsoft_teams', 'Microsoft Teams'),
        ('discord', 'Discord'),
    ])
    subject = models.CharField(max_length=255, help_text="Subject line for email notifications")
    body_html = models.TextField(help_text="HTML content of the notification")
    body_text = models.TextField(help_text="Plain text version of the notification")
    is_active = models.BooleanField(default=True, help_text="Whether this template is currently active")
    is_default = models.BooleanField(default=False, help_text="Whether this is the default template for its type")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='notification_templates')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notification_templates_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    variables = models.JSONField(default=list, blank=True, help_text="List of variables that can be used in the template")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing templates")
    notes = models.TextField(blank=True, help_text="Internal notes about this template")
    
    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.template_type.upper()}"


class EmailSMSServiceConfiguration(models.Model):
    """Model for email and SMS service configuration"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name for this configuration")
    service_provider = models.CharField(max_length=100, choices=[
        ('smtp', 'SMTP Server'),
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('twilio', 'Twilio'),
        ('aws_sns', 'AWS SNS'),
        ('firebase', 'Firebase Messaging'),
        ('custom_api', 'Custom API'),
    ])
    configuration = models.JSONField(default=dict, blank=True, help_text="Configuration settings for the service")
    is_active = models.BooleanField(default=True, help_text="Whether this service configuration is active")
    is_primary = models.BooleanField(default=False, help_text="Whether this is the primary service for its type")
    service_type = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both Email and SMS'),
    ])
    rate_limit_requests = models.IntegerField(default=100, help_text="Number of requests allowed per time period")
    rate_limit_period_seconds = models.IntegerField(default=60, help_text="Time period for rate limiting in seconds")
    retry_attempts = models.IntegerField(default=3, help_text="Number of retry attempts for failed messages")
    retry_delay_seconds = models.IntegerField(default=5, help_text="Delay between retry attempts in seconds")
    encryption_enabled = models.BooleanField(default=True, help_text="Whether to encrypt sensitive configuration data")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='service_configurations')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_configs_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_tested = models.DateTimeField(null=True, blank=True, help_text="When this configuration was last tested")
    last_test_result = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('pending', 'Pending'),
    ], default='pending')
    last_test_error = models.TextField(blank=True, help_text="Error from last test if it failed")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing configurations")
    notes = models.TextField(blank=True, help_text="Internal notes about this configuration")
    
    class Meta:
        verbose_name = "Email/SMS Service Configuration"
        verbose_name_plural = "Email/SMS Service Configurations"
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.service_provider} ({self.service_type})"


class CommunicationHistory(models.Model):
    """Model for tracking communication history"""
    id = models.AutoField(primary_key=True)
    communication_type = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('microsoft_teams', 'Microsoft Teams'),
        ('discord', 'Discord'),
    ])
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outbound')
    recipient = models.CharField(max_length=255, help_text="Recipient of the communication (email, phone number, etc.)")
    recipient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications_received')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications_sent')
    subject = models.CharField(max_length=255, help_text="Subject of the communication")
    content_html = models.TextField(help_text="HTML content of the communication")
    content_text = models.TextField(help_text="Plain text content of the communication")
    status = models.CharField(max_length=20, choices=[
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ], default='queued')
    service_used = models.ForeignKey(EmailSMSServiceConfiguration, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications_sent')
    sent_at = models.DateTimeField(null=True, blank=True, help_text="When the communication was sent")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="When the communication was delivered")
    opened_at = models.DateTimeField(null=True, blank=True, help_text="When the communication was opened")
    clicked_at = models.DateTimeField(null=True, blank=True, help_text="When links in the communication were clicked")
    error_message = models.TextField(blank=True, help_text="Error message if the communication failed")
    response_code = models.IntegerField(null=True, blank=True, help_text="Response code from the service provider")
    response_message = models.TextField(blank=True, help_text="Response message from the service provider")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    template_used = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications_sent')
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing communications")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata about the communication")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Communication History"
        verbose_name_plural = "Communication Histories"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['status']),
            models.Index(fields=['tenant']),
            models.Index(fields=['created_at']),
            models.Index(fields=['communication_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.communication_type.upper()} to {self.recipient} - {self.status}"


class CustomerSupportTicket(models.Model):
    """Model for customer support tickets"""
    id = models.AutoField(primary_key=True)
    subject = models.CharField(max_length=255, help_text="Subject of the ticket")
    description = models.TextField(help_text="Detailed description of the issue")
    ticket_type = models.CharField(max_length=50, choices=[
        ('technical_issue', 'Technical Issue'),
        ('feature_request', 'Feature Request'),
        ('billing_inquiry', 'Billing Inquiry'),
        ('account_question', 'Account Question'),
        ('security_concern', 'Security Concern'),
        ('feedback', 'Feedback'),
        ('complaint', 'Complaint'),
        ('other', 'Other'),
    ])
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ], default='medium')
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('duplicate', 'Duplicate'),
        ('wont_fix', 'Won\'t Fix'),
    ], default='open')
    source = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('web_form', 'Web Form'),
        ('api', 'API'),
        ('chat', 'Chat'),
        ('phone', 'Phone'),
        ('social_media', 'Social Media'),
    ], default='web_form')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_submitted')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assigned')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='support_tickets')
    related_objects = models.JSONField(default=list, blank=True, help_text="Related objects (e.g., accounts, leads, opportunities)")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing tickets")
    internal_notes = models.TextField(blank=True, help_text="Internal notes about the ticket")
    resolution_notes = models.TextField(blank=True, help_text="Notes about how the ticket was resolved")
    resolution_type = models.CharField(max_length=50, choices=[
        ('fixed', 'Fixed'),
        ('workaround', 'Workaround Provided'),
        ('answered', 'Question Answered'),
        ('feature_implemented', 'Feature Implemented'),
        ('wont_do', 'Won\'t Do'),
        ('duplicate', 'Duplicate'),
    ], null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_resolved')
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_closed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_response_at = models.DateTimeField(null=True, blank=True, help_text="When the ticket first received a response")
    first_responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_first_responded')
    sla_deadline = models.DateTimeField(null=True, blank=True, help_text="SLA deadline for responding to the ticket")
    sla_met = models.BooleanField(null=True, blank=True, help_text="Whether the SLA was met for this ticket")
    satisfaction_rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)], help_text="Satisfaction rating from 1-5")
    satisfaction_comment = models.TextField(blank=True, help_text="Comment about the satisfaction rating")
    
    class Meta:
        verbose_name = "Customer Support Ticket"
        verbose_name_plural = "Customer Support Tickets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['tenant']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.ticket_type.replace('_', ' ').title()}: {self.subject}"


class FeedbackAndSurvey(models.Model):
    """Model for managing feedback and surveys"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, help_text="Title of the feedback form or survey")
    description = models.TextField(blank=True, help_text="Description of the feedback form or survey")
    feedback_type = models.CharField(max_length=50, choices=[
        ('nps', 'Net Promoter Score'),
        ('csat', 'Customer Satisfaction'),
        ('ces', 'Customer Effort Score'),
        ('general_feedback', 'General Feedback'),
        ('product_feedback', 'Product Feedback'),
        ('feature_request', 'Feature Request'),
        ('bug_report', 'Bug Report'),
        ('survey', 'Custom Survey'),
        ('review', 'Review'),
    ])
    is_active = models.BooleanField(default=True, help_text="Whether this feedback form/survey is active")
    is_anonymous = models.BooleanField(default=False, help_text="Whether responses are anonymous")
    collect_user_data = models.BooleanField(default=True, help_text="Whether to collect user identification data")
    target_audience = models.CharField(max_length=50, choices=[
        ('all_users', 'All Users'),
        ('specific_tenant', 'Specific Tenant'),
        ('specific_role', 'Specific Role'),
        ('customers', 'Customers Only'),
        ('internal_users', 'Internal Users Only'),
    ], default='all_users')
    tenant_target = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='feedback_forms')
    role_target = models.CharField(max_length=100, blank=True, help_text="Specific role this targets if applicable")
    start_date = models.DateTimeField(help_text="When the feedback collection starts")
    end_date = models.DateTimeField(null=True, blank=True, help_text="When the feedback collection ends (optional)")
    redirect_url = models.URLField(blank=True, help_text="URL to redirect after submission")
    confirmation_message = models.TextField(default="Thank you for your feedback!", help_text="Message to show after submission")
    questions = models.JSONField(default=list, blank=True, help_text="Questions in the survey/feedback form")
    response_count = models.IntegerField(default=0, help_text="Number of responses received")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_forms_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing feedback forms")
    notes = models.TextField(blank=True, help_text="Internal notes about this feedback form")
    
    class Meta:
        verbose_name = "Feedback and Survey"
        verbose_name_plural = "Feedback and Surveys"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.feedback_type.replace('_', ' ').title()}: {self.title}"


class Email(TenantAwareModel):
    """Model for managing email communications"""
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outbound')
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    contact = models.ForeignKey('accounts.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('blocked', 'Blocked'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    email_name = models.CharField(max_length=255, help_text="Name/title of the email")
    subject = models.CharField(max_length=255, help_text="Subject line of the email")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails_sent')
    recipients = models.JSONField(default=list, help_text="List of recipient email addresses")
    cc = models.JSONField(default=list, blank=True, help_text="List of CC email addresses")
    bcc = models.JSONField(default=list, blank=True, help_text="List of BCC email addresses")
    content_html = models.TextField(help_text="HTML content of the email")
    content_text = models.TextField(help_text="Plain text content of the email")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_read_receipt_requested = models.BooleanField(default=False, help_text="Whether to request a read receipt")
    is_reply_to_different = models.BooleanField(default=False, help_text="Whether reply-to is different from sender")
    reply_to_email = models.EmailField(blank=True, help_text="Reply-to email address if different from sender")
    attachments = models.JSONField(default=list, blank=True, help_text="List of attachment file paths/URLs")
    send_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled time to send the email")
    sent_at = models.DateTimeField(null=True, blank=True, help_text="Actual time the email was sent")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="Time the email was delivered")
    opened_at = models.DateTimeField(null=True, blank=True, help_text="Time the email was opened")
    clicked_at = models.DateTimeField(null=True, blank=True, help_text="Time the email was clicked")
    error_message = models.TextField(blank=True, help_text="Error message if email failed to send")
    service_used = models.CharField(max_length=50, blank=True, help_text="Email service used to send (e.g., smtp, sendgrid)")
    tracking_enabled = models.BooleanField(default=True, help_text="Whether to track opens/clicks for this email")
    tracking_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email_name


class CallLog(TenantAwareModel):
    """Model for logging phone calls"""
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    contact = models.ForeignKey('accounts.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    CALL_TYPE_CHOICES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
        ('missed', 'Missed'),
        ('voicemail', 'Voicemail'),
    ]
    
    RESULT_CHOICES = [
        ('answered', 'Answered'),
        ('no_answer', 'No Answer'),
        ('busy', 'Busy'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
        ('transferred', 'Transferred'),
    ]
    
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES, help_text="Type of call")
    direction = models.CharField(max_length=10, choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')])
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='calls_initiated')
    phone_number = models.CharField(max_length=20, help_text="Phone number")
    contact_name = models.CharField(max_length=255, blank=True, help_text="Name of the contact")
    duration_seconds = models.IntegerField(default=0, help_text="Duration of the call in seconds")
    outcome = models.CharField(max_length=20, choices=RESULT_CHOICES, help_text="Result of the call")
    recording_url = models.URLField(blank=True, help_text="URL to the call recording")
    transcript = models.TextField(blank=True, help_text="Text transcript of the call")
    notes = models.TextField(blank=True, help_text="Notes about the call")
    follow_up_required = models.BooleanField(default=False, help_text="Whether follow-up is required")
    related_object_type = models.CharField(max_length=50, blank=True, help_text="Type of object this call is related to")
    related_object_id = models.CharField(max_length=50, blank=True, help_text="ID of the related object")
    call_started_at = models.DateTimeField(default=timezone.now)
    call_ended_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Call Log"
        verbose_name_plural = "Call Logs"
        ordering = ['-call_started_at']
    
    def __str__(self):
        return f"{self.call_type.title()} call: {self.phone_number} ({self.outcome})"


class SMS(TenantAwareModel):
    """Model for managing SMS communications"""
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outbound')
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_messages')
    contact = models.ForeignKey('accounts.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_messages')
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_messages')
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    recipient_phone = models.CharField(max_length=20, help_text="Recipient phone number")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sms_sent')
    message = models.TextField(help_text="SMS content")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_send_time = models.DateTimeField(null=True, blank=True, help_text="Scheduled time to send the SMS")
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SMS"
        verbose_name_plural = "SMS Messages"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS to {self.recipient_phone}"


class Meeting(TenantAwareModel):
    """Model for managing meetings"""
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    contact = models.ForeignKey('accounts.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    MEETING_TYPE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid'),
        ('video_conference', 'Video Conference'),
        ('audio_only', 'Audio Only'),
        ('screen_sharing', 'Screen Sharing'),
    ]
    
    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
        ('protected', 'Protected'),
    ]
    
    meeting_name = models.CharField(max_length=255, help_text="Name/title of the meeting")
    meeting_description = models.TextField(blank=True, help_text="Description of the meeting")
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES, help_text="Type of meeting")
    location = models.CharField(max_length=500, blank=True, help_text="Location of the meeting (physical or virtual)")
    start_time = models.DateTimeField(help_text="When the meeting starts")
    end_time = models.DateTimeField(help_text="When the meeting ends")
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings_organized')
    attendees = models.JSONField(default=list, help_text="List of attendee user IDs or emails")
    invitees = models.JSONField(default=list, blank=True, help_text="List of invited user IDs or emails")
    is_confirmed = models.BooleanField(default=True, help_text="Whether the meeting is confirmed")
    is_recurring = models.BooleanField(default=False, help_text="Whether this is a recurring meeting")
    recurrence_pattern = models.JSONField(default=dict, blank=True, help_text="Recurrence pattern if recurring")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    timezone = models.CharField(max_length=50, default='UTC', help_text="Timezone for the meeting")
    meeting_link = models.URLField(blank=True, help_text="Link to join the online meeting")
    meeting_id = models.CharField(max_length=100, blank=True, help_text="Meeting ID for conferencing tools")
    meeting_password = models.CharField(max_length=100, blank=True, help_text="Meeting password if required")
    agenda = models.TextField(blank=True, help_text="Meeting agenda")
    notes = models.TextField(blank=True, help_text="Meeting notes")
    attachments = models.JSONField(default=list, blank=True, help_text="List of attachment file paths/URLs")
    related_object_type = models.CharField(max_length=50, blank=True, help_text="Type of object this meeting is related to")
    related_object_id = models.CharField(max_length=50, blank=True, help_text="ID of the related object")
    reminder_set = models.BooleanField(default=False, help_text="Whether a reminder has been set")
    reminder_time_minutes = models.IntegerField(default=15, help_text="Minutes before meeting to send reminder")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.meeting_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class SocialMediaPost(TenantAwareModel):
    """Model for tracking social media posts"""
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='social_posts')
    contact = models.ForeignKey('accounts.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='social_posts')
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='social_posts')
    platform = models.CharField(max_length=50, choices=[
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ])
    post_id = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    url = models.URLField(blank=True)
    is_inmail = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Social Media Post"
        verbose_name_plural = "Social Media Posts"

    def __str__(self):
        return f"{self.platform.title()} post - {self.posted_at}"


class ChatMessage(TenantAwareModel):
    """Model for tracking chat messages"""
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages')
    contact = models.ForeignKey('accounts.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages')
    channel = models.CharField(max_length=50, choices=[
        ('whatsapp', 'WhatsApp'),
        ('website_chat', 'Website Chat'),
        ('slack', 'Slack'),
        ('messenger', 'Messenger'),
    ])
    sender_name = models.CharField(max_length=255)
    message = models.TextField()
    external_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID from the external platform")
    metadata = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"{self.channel.title()} from {self.sender_name} - {self.received_at}"


class EmailSignature(TenantAwareModel):
    """Model for managing email signatures for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_signatures')
    name = models.CharField(max_length=100, help_text="Name of the signature (e.g., 'Professional', 'Informal')")
    content_html = models.TextField(help_text="HTML content of the signature")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Email Signature"
        verbose_name_plural = "Email Signatures"

    def __str__(self):
        return f"{self.user.username}'s {self.name} signature"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other signatures of this user to not default
            EmailSignature.objects.filter(user=self.user, tenant=self.tenant).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

# Import WhatsApp models to ensure they are registered
from .whatsapp_models import WhatsAppConfiguration, WhatsAppMessage, WhatsAppTemplate
