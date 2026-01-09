from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from tenants.models import Tenant, TenantAwareModel
from accounts.models import User 
from core.models import TimeStampedModel

# --- 1. SURVEY CONFIGURATION MODELS ---


class NpsSurvey(TenantAwareModel):
    """
    NPS survey configuration.
    """
    nps_survey_name = models.CharField(max_length=255)
    nps_survey_description = models.TextField(blank=True)
    nps_survey_is_active = models.BooleanField(default=True)

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
            ('user.onboarded', 'User Onboarded'),
            ('case.closed', 'Case Closed'),
            ('renewal.completed', 'Renewal Completed'),
            ('manual', 'Manual'),
        ],
        default='manual'
    )
    
    # Scheduling
    scheduled_start_date = models.DateTimeField(null=True, blank=True)
    scheduled_end_date = models.DateTimeField(null=True, blank=True)
    
    # Advanced follow-up logic
    enable_follow_up_logic = models.BooleanField(default=False)
     
    # Delivery targeting
    target_roles = models.ManyToManyField('tenants.TenantRole', blank=True)
    target_territories = models.ManyToManyField('tenants.TenantTerritory', blank=True)

    def __str__(self):
        return self.nps_survey_name

    @property
    def is_currently_active(self):
        if not self.nps_survey_is_active:
            return False
        now = timezone.now()
        if self.scheduled_start_date and now < self.scheduled_start_date:
            return False
        if self.scheduled_end_date and now > self.scheduled_end_date:
            return False
        return True


class NpsConditionalFollowUp(TenantAwareModel):
    """
    Conditional follow-up questions based on NPS score thresholds.
    """
    survey = models.ForeignKey(NpsSurvey, on_delete=models.CASCADE, related_name='conditional_follow_ups')
    score_threshold = models.IntegerField(
        choices=[(i, str(i)) for i in range(0, 11)],
        help_text="Show this question when score is greater than or equal to this value"
    )
    conditional_question_text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['score_threshold', 'order']
        unique_together = ['survey', 'score_threshold']

    def __str__(self):
        return f"Follow-up for {self.survey.nps_survey_name} (score >= {self.score_threshold})"


# --- 2. RESPONSE MODELS ---


class NpsResponse(TenantAwareModel, TimeStampedModel):
    """
    Individual NPS response and core automation logic.
    """
    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nps_responses')
    contact_email = models.EmailField(blank=True)
    survey = models.ForeignKey(NpsSurvey, on_delete=models.CASCADE, related_name='responses')
    score = models.IntegerField()  # 0-10
    comment = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    delivery_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"NPS {self.score} for {self.account.email}"


    @property
    def is_promoter(self): return self.score >= 9
    
    @property
    def is_passive(self): return 7 <= self.score <= 8
    
    @property
    def is_detractor(self): return self.score <= 6

    def clean(self):
        if not (0 <= self.score <= 10):
            raise ValidationError("NPS score must be between 0 and 10")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Import utilities here to prevent circular imports
            from automation.utils import emit_event
            from cases.models import Case
            from cases.utils import escalate_case, calculate_sla_due_date
            from tenants.models import TenantMember
            from tasks.models import Task
            from .utils import apply_escalation_rules, create_promoter_referral_request
            
            payload = {
                'response_id': self.id,
                'account_id': self.account_id,
                'score': self.score,
                'comment': self.comment,
                'tenant_id': self.tenant_id
            }
            
            # 1. Apply Dynamic Escalation Rules
            apply_escalation_rules(self)
            
            # 2. Score-based Hardcoded Logic
            if self.is_detractor:
                emit_event('nps.detractor_submitted', payload)
                
                case_subject = f"NPS Detractor Follow-up: {self.survey.nps_survey_name}"
                case_description = f"NPS score: {self.score}\nComment: {self.comment}"
                
                case, created = Case.objects.get_or_create(
                    account=self.account,
                    subject=case_subject,
                    defaults={
                        'case_description': case_description,
                        'priority': 'high',
                        'tenant_id': self.tenant_id,
                        'sla_response_hours': 4,
                        'assigned_team': 'Support'
                    }
                )
                
                if created:
                    # Assign Owner
                    owner = TenantMember.objects.filter(tenant=self.tenant, user=self.account.owner).first()
                    if not owner and self.account.owner:
                        # Fallback to any member
                        owner = TenantMember.objects.filter(tenant=self.tenant).first()
                        
                    case.owner = owner.user if owner else None
                    case.sla_due = calculate_sla_due_date(case.priority)
                    case.save()
                    
                    # Level 1 Escalation
                    escalate_case(case.id, 'level_1', self.account.tenant.owner_id)
            
            elif self.is_promoter:
                emit_event('nps.promoter_submitted', payload)
                if self.score == 10 and self.comment:
                    create_promoter_referral_request(self.id)
                    Task.objects.create(
                        account=self.account,
                        task_title=f"Promoter Referral Follow-up: {self.account.email}",
                        task_type='nps_promoter_referral',
                        due_date=timezone.now() + timedelta(days=2),
                        tenant=self.tenant,
                        priority='medium'
                    )
            
            elif self.is_passive:
                emit_event('nps.passive_submitted', payload)
                Task.objects.create(
                    account=self.account,
                    task_title=f"Passive Follow-up: {self.account.email}",
                    task_type='nps_passive_followup',
                    due_date=timezone.now() + timedelta(days=3),
                    tenant=self.tenant,
                    priority='low'
                )


# --- 3. ESCALATION & ACTIONS ---

class NpsEscalationAction(TenantAwareModel):
    """
    Reusable actions (Email, Case, Task) for escalation rules.
    """
    ACTION_TYPE_CHOICES = [
        ('create_case', 'Create Case'),
        ('assign_task', 'Assign Task'),
        ('send_notification', 'Send Notification'),
        ('trigger_workflow', 'Trigger Workflow'),
        ('send_email', 'Send Email'),
        ('update_field', 'Update Field'),
        ('assign_owner', 'Assign Owner'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    action_parameters = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_action_type_display()})"


class NpsEscalationRule(TenantAwareModel):
    """
    Rules to trigger actions based on score and conditions.
    """
    ESCALATION_TYPE_CHOICES = [
        ('detractor', 'Detractor'),
        ('passive', 'Passive'),
        ('promoter', 'Promoter'),
        ('all', 'All Responses'),
    ]
    
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    response_type = models.CharField(max_length=20, choices=ESCALATION_TYPE_CHOICES, default='detractor')
    min_score = models.IntegerField(null=True, blank=True)
    max_score = models.IntegerField(null=True, blank=True)
    requires_comment = models.BooleanField(default=False)
    
    actions = models.ManyToManyField(
        'NpsEscalationAction',
        through='NpsEscalationRuleAction',
        related_name='escalation_rules'
    )
    
    auto_escalate_after_hours = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def applies_to_response(self, nps_response):
        score = nps_response.score
        if self.min_score is not None and score < self.min_score: return False
        if self.max_score is not None and score > self.max_score: return False
        if self.requires_comment and not nps_response.comment: return False
        return True


class NpsEscalationRuleAction(TenantAwareModel):
    """
    M2M helper to handle order of actions per rule.
    """
    escalation_rule = models.ForeignKey(NpsEscalationRule, on_delete=models.CASCADE)
    escalation_action = models.ForeignKey(NpsEscalationAction, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['escalation_rule', 'escalation_action']



class NpsEscalationActionLog(TenantAwareModel, TimeStampedModel):
    """
    Audit log for executed escalation actions.
    """
    STATUS_CHOICES = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')]
    
    escalation_rule = models.ForeignKey(NpsEscalationRule, on_delete=models.CASCADE, related_name='action_logs')
    action = models.ForeignKey(NpsEscalationAction, on_delete=models.CASCADE, related_name='execution_logs')
    nps_response = models.ForeignKey(NpsResponse, on_delete=models.CASCADE, related_name='escalation_actions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    executed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']



# --- 4. ALERTS & REFERRALS ---

class NpsDetractorAlert(TenantAwareModel):
    """
    Specific workflow tracking for Detractors.
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


class NpsPromoterReferral(TenantAwareModel, TimeStampedModel):
    """
    Tracking high-score promoters for referral opportunities.
    """
    STATUS_CHOICES = [('requested', 'Requested'), ('contacted', 'Contacted'), ('converted', 'Converted'), ('not_interested', 'Not Interested'), ('closed', 'Closed')]
    
    promoter_response = models.OneToOneField(NpsResponse, on_delete=models.CASCADE, related_name='referral_request')
    referred_contact_name = models.CharField(max_length=255, blank=True)
    referred_contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    deal_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)


# --- 5. A/B TESTING MODELS ---

# apps/engagement/models.py

class NpsAbTest(TenantAwareModel):
    """
    A/B test for NPS surveys.
    """
    survey = models.ForeignKey('NpsSurvey', on_delete=models.CASCADE, related_name='ab_tests')
    nps_abtest_name = models.CharField(max_length=255)
    nps_abtest_is_active = models.BooleanField(default=True)
    winner_variant = models.ForeignKey('NpsAbVariant', on_delete=models.SET_NULL, null=True, blank=True)
    
    # These fields were likely missing in your previous version:
    auto_winner = models.BooleanField(default=True)
    min_responses = models.IntegerField(default=100)  # min total responses
    confidence_level = models.FloatField(default=0.95)  # e.g., 0.95 for 95%

    def __str__(self):
        return f"{self.survey.nps_survey_name} - {self.nps_abtest_name}"

class NpsAbVariant(TenantAwareModel):
    """
    Variant for A/B test.
    """
    VARIANT_CHOICES = [('A', 'Variant A'), ('B', 'Variant B')]
    
    ab_test = models.ForeignKey(NpsAbTest, on_delete=models.CASCADE, related_name='variants')
    variant = models.CharField(max_length=1, choices=VARIANT_CHOICES)
    question_text = models.TextField(blank=True)
    follow_up_question = models.TextField(blank=True) # Ensure this exists
    delivery_delay_hours = models.IntegerField(default=0)
    assignment_rate = models.FloatField(default=0.5)

    def __str__(self):
        return f"{self.variant} for {self.ab_test.nps_abtest_name}"

class NpsAbResponse(TenantAwareModel):
    response = models.OneToOneField(NpsResponse, on_delete=models.CASCADE)
    ab_variant = models.ForeignKey(NpsAbVariant, on_delete=models.CASCADE)


# --- 6. ANALYTICS ---

class NpsTrendSnapshot(TenantAwareModel):
    date = models.DateField()
    nps_score = models.FloatField()
    total_responses = models.IntegerField()
    promoters = models.IntegerField()
    passives = models.IntegerField()
    detractors = models.IntegerField()

    class Meta:
        unique_together = ['date', 'tenant']