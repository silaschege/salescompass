from django.db import models
from core.models import TimeStampedModel, TenantModel
from core.models import User
from django.utils import timezone
from core.managers import VisibilityAwareManager

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

TIER_CHOICES = [
    ('bronze', 'Bronze'),
    ('silver', 'Silver'),
    ('gold', 'Gold'),
    ('platinum', 'Platinum'),
]

ESG_ENGAGEMENT_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

STATUS_CHOICES = [
    ('active', 'Active'),
    ('at_risk', 'At Risk'),
    ('churned', 'Churned'),
]

class Account(TenantModel):
    """
    Core customer account with ESG intelligence.
    """
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    website = models.URLField(blank=True)
    country = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    
    # ESG
    esg_engagement = models.CharField(max_length=10, choices=ESG_ENGAGEMENT_CHOICES, default='low')
    sustainability_goals = models.TextField(blank=True)
    
    # Computed analytics (denormalized for performance)
    health_score = models.FloatField(default=0.0)  # 0–100
    clv = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)  # Customer Lifetime Value
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Ownership
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_accounts')
    
    # Compliance
    gdpr_consent = models.BooleanField(default=False)
    ccpa_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['industry', 'tier']),
            models.Index(fields=['health_score']),
            models.Index(fields=['renewal_date']),
            models.Index(fields=['tenant_id']),
        ]

    objects = VisibilityAwareManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_health_score = 0.0
        
        if not is_new:
            try:
                old_instance = Account.objects.get(pk=self.pk)
                old_health_score = old_instance.health_score
            except Account.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        from automation.utils import emit_event
        
        if is_new:
            emit_event('accounts.created', {
                'account_id': self.id,
                'name': self.name,
                'industry': self.industry,
                'tier': self.tier,
                'owner_id': self.owner_id if self.owner else None,
                'tenant_id': self.tenant_id
            })
            
        # Check for low health score
        if self.health_score < 40 and (is_new or old_health_score >= 40):
             emit_event('accounts.health_low', {
                'account_id': self.id,
                'name': self.name,
                'health_score': self.health_score,
                'owner_id': self.owner_id if self.owner else None,
                'tenant_id': self.tenant_id
            })
    # Add to Account model
    def create_renewal_reminder(self):
        """Create renewal reminder task."""
        from tasks.models import Task
        from datetime import timedelta
    
        Task.objects.create(
            title=f"Renewal reminder: {self.name}",
            description=f"Account {self.name} renewal is coming up",
            assigned_to=self.owner,
            account=self,
            priority='high',
            status='todo',
            task_type='renewal_reminder',
            due_date=self.renewal_date - timedelta(days=30) if self.renewal_date else timezone.now() + timedelta(days=30),
            tenant_id=self.tenant_id
        )


class Contact(TenantModel):
    """
    Person associated with an account.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=100, blank=True)
    
    COMM_PREF_CHOICES = [('email', 'Email'), ('sms', 'SMS'), ('none', 'None')]
    communication_preference = models.CharField(max_length=10, choices=COMM_PREF_CHOICES, default='email')
    is_primary = models.BooleanField(default=False)
    
    # ESG influence (computed based on engagement with ESG materials)
    esg_influence = models.CharField(
        max_length=10,
        choices=ESG_ENGAGEMENT_CHOICES,
        default='low',
        help_text="Inferred from engagement with ESG materials"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.account.name})"