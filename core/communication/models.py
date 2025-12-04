from django.db import models
from core.models import TenantModel, User
from leads.models import Lead
from accounts.models import Account, Contact

class Interaction(TenantModel):
    """
    Abstract base class for all interactions.
    """
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(app_label)s_%(class)s_owned')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Links to core entities (nullable to allow linking to any combination)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)ss')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)ss')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)ss')
    
    # Intelligence
    sentiment_score = models.FloatField(default=0.0, help_text="-1.0 to 1.0")
    sentiment_label = models.CharField(max_length=20, blank=True, help_text="positive, negative, neutral")

    class Meta:
        abstract = True
        ordering = ['-timestamp']

class Email(Interaction):
    DIRECTION_CHOICES = [('inbound', 'Inbound'), ('outbound', 'Outbound')]
    
    subject = models.CharField(max_length=255)
    body = models.TextField()
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outbound')
    message_id = models.CharField(max_length=255, blank=True, help_text="External Message ID")
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Email: {self.subject}"

class Call(Interaction):
    OUTCOME_CHOICES = [
        ('connected', 'Connected'),
        ('voicemail', 'Voicemail'),
        ('no_answer', 'No Answer'),
        ('wrong_number', 'Wrong Number'),
    ]
    
    duration = models.DurationField(null=True, blank=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='connected')
    recording_url = models.URLField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Call: {self.outcome} ({self.timestamp})"

class Meeting(Interaction):
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    agenda = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Meeting: {self.title}"
