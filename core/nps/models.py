from django.db import models
from core.models import TenantModel
from core.models import User
from accounts.models import Account

class NpsSurvey(TenantModel):
    """
    NPS survey configuration.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    # Survey content
    question_text = models.TextField(default="How likely are you to recommend us to a friend or colleague?")
    follow_up_question = models.TextField(default="What's the most important reason for your score?")
    
    # Delivery
    delivery_method = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('in_app', 'In-App'), ('sms', 'SMS')],
        default='email'
    )
    
    # Trigger
    trigger_event = models.CharField(
        max_length=50,
        choices=[
            ('account.onboarded', 'Account Onboarded'),
            ('case.closed', 'Case Closed'),
            ('renewal.completed', 'Renewal Completed'),
            ('manual', 'Manual'),
        ],
        default='manual'
    )

    def __str__(self):
        return self.name


class NpsResponse(TenantModel):
    """
    Individual NPS response.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='nps_responses')
    contact_email = models.EmailField(blank=True)
    survey = models.ForeignKey(NpsSurvey, on_delete=models.CASCADE, related_name='responses')
    
    # NPS core
    score = models.IntegerField()  # -10 to +10 for extended NPS, or 0-10 for standard
    comment = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    delivery_id = models.CharField(max_length=100, blank=True)  # e.g., email_id
    
    # Classification
    @property
    def is_promoter(self):
        return self.score >= 9
    
    @property
    def is_passive(self):
        return 7 <= self.score <= 8
    
    @property
    def is_detractor(self):
        return self.score <= 6

    def clean(self):
        if not (-10 <= self.score <= 10):
            raise ValidationError("NPS score must be between -10 and +10")

    def __str__(self):
        return f"NPS {self.score} for {self.account.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            from automation.utils import emit_event
            
            payload = {
                'response_id': self.id,
                'account_id': self.account_id,
                'score': self.score,
                'comment': self.comment,
                'tenant_id': self.tenant_id
            }
            
            if self.is_detractor:
                emit_event('nps.detractor_submitted', payload)
            elif self.is_promoter:
                emit_event('nps.promoter_submitted', payload)
            elif self.is_passive:
                emit_event('nps.passive_submitted', payload)


class NpsDetractorAlert(TenantModel):
    """
    Alert for NPS detractors requiring follow-up.
    """
    response = models.OneToOneField(NpsResponse, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')],
        default='open'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Detractor Alert for {self.response.account.name}"


class NpsTrendSnapshot(TenantModel):
    """
    Daily snapshot of NPS for trend analysis.
    """
    date = models.DateField()
    nps_score = models.FloatField()
    total_responses = models.IntegerField()
    promoters = models.IntegerField()
    passives = models.IntegerField()
    detractors = models.IntegerField()
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)

    class Meta:
        unique_together = [('date', 'tenant_id')]


class NpsAbTest(TenantModel):
    """
    A/B test for NPS surveys.
    """
    survey = models.ForeignKey(NpsSurvey, on_delete=models.CASCADE, related_name='ab_tests')
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    winner_variant = models.ForeignKey('NpsAbVariant', on_delete=models.SET_NULL, null=True, blank=True)
    auto_winner = models.BooleanField(default=True)
    min_responses = models.IntegerField(default=100)  # min total responses
    confidence_level = models.FloatField(default=0.95)  # 95% confidence

    def __str__(self):
        return f"{self.survey.name} - {self.name}"


class NpsAbVariant(TenantModel):
    """
    Variant for A/B test.
    """
    VARIANT_CHOICES = [('A', 'Variant A'), ('B', 'Variant B')]
    
    ab_test = models.ForeignKey(NpsAbTest, on_delete=models.CASCADE, related_name='variants')
    variant = models.CharField(max_length=1, choices=VARIANT_CHOICES)
    question_text = models.TextField(blank=True)
    follow_up_question = models.TextField(blank=True)
    delivery_delay_hours = models.IntegerField(default=0)  # delay after trigger
    assignment_rate = models.FloatField(default=0.5)  # 0.0–1.0


class NpsAbResponse(TenantModel):
    """
    Tracks which variant a response came from.
    """
    response = models.OneToOneField(NpsResponse, on_delete=models.CASCADE)
    ab_variant = models.ForeignKey(NpsAbVariant, on_delete=models.CASCADE)