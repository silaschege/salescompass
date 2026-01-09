"""
Wazo Integration Models for SalesCompass CRM.
Tracks call logs, SMS messages, and telephony activities.
"""
from django.db import models
from django.conf import settings
from tenants.models import TenantAwareModel


class WazoCallLog(TenantAwareModel):
    """
    Track all calls made/received through Wazo.
    Links calls to CRM entities (contacts, leads, opportunities).
    """
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('busy', 'Busy'),
        ('no_answer', 'No Answer'),
        ('voicemail', 'Voicemail'),
    ]
    
    call_id = models.CharField(max_length=100, unique=True, db_index=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    from_number = models.CharField(max_length=50)
    to_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    recording_url = models.URLField(max_length=500, null=True, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Link to CRM entities
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_calls'
    )
    contact = models.ForeignKey(
        'accounts.Contact',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_calls'
    )
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_calls'
    )
    opportunity = models.ForeignKey(
        'opportunities.Opportunity',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_calls'
    )
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_calls'
    )
    
    # Raw Wazo data
    wazo_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['tenant', 'started_at']),
            models.Index(fields=['from_number']),
            models.Index(fields=['to_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.direction}: {self.from_number} → {self.to_number} ({self.status})"


class WazoSMSLog(TenantAwareModel):
    """
    Track all SMS messages sent/received through Wazo.
    """
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('received', 'Received'),
    ]
    
    message_id = models.CharField(max_length=100, unique=True, db_index=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    from_number = models.CharField(max_length=50)
    to_number = models.CharField(max_length=50)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Link to CRM entities
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_sms'
    )
    contact = models.ForeignKey(
        'accounts.Contact',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_sms'
    )
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wazo_sms'
    )
    
    # Raw Wazo data
    wazo_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['tenant', 'sent_at']),
            models.Index(fields=['from_number']),
            models.Index(fields=['to_number']),
        ]
    
    def __str__(self):
        return f"{self.direction}: {self.from_number} → {self.to_number}"


class WazoExtension(TenantAwareModel):
    """
    Maps CRM users to Wazo extensions for click-to-call.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wazo_extension'
    )
    extension = models.CharField(max_length=20, help_text="Wazo extension number (e.g., 1001)")
    caller_id = models.CharField(max_length=50, blank=True, help_text="Outbound caller ID")
    is_active = models.BooleanField(default=True)
    wazo_user_uuid = models.CharField(max_length=100, blank=True, help_text="Wazo user UUID")
    
    class Meta:
        unique_together = ['tenant', 'extension']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Ext: {self.extension}"
