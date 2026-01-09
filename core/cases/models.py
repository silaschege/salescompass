from django.db import models
from core.models import TimeStampedModel,User
from tenants.models import TenantAwareModel as TenantModel
from accounts.models import Contact
from datetime import timedelta
from django.utils import timezone
from core.managers import VisibilityAwareManager
from settings_app.models import AssignmentRuleType

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

STATUS_CHOICES = [
    ('new', 'New'),
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed'),
]

ESCALATION_LEVEL_CHOICES = [
    ('none', 'None'),
    ('level_1', 'Level 1'),
    ('level_2', 'Level 2'),
    ('executive', 'Executive'),
]

class Case(TenantModel):
    """
    Customer support case with SLA and CSAT.
    """
    subject = models.CharField(max_length=255)
    case_description = models.TextField()
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='cases')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_cases')
    assigned_team = models.CharField(max_length=100, blank=True, help_text="e.g., Support, Billing")
    
    # SLA Configuration
    sla_response_hours = models.IntegerField(default=24, help_text="Expected response time in hours")
    sla_resolution_hours = models.IntegerField(default=72, help_text="Expected resolution time in hours")
    sla_due = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    
    # Escalation Rules
    escalation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Auto-escalation rules, e.g., {'hours_before_escalation': 4, 'escalate_to_role': 'manager'}"
    )
    
    # CSAT
    csat_score = models.IntegerField(null=True, blank=True)  # 1–5
    csat_comment = models.TextField(blank=True)
    
    # Escalation
    escalation_level = models.CharField(
        max_length=20, 
        choices=ESCALATION_LEVEL_CHOICES, 
        default='none'
    )
    escalated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='escalated_cases'
    )
    


    objects = VisibilityAwareManager()

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_escalation_level = 'none'
        
        if not is_new:
            try:
                old_instance = Case.objects.get(pk=self.pk)
                old_escalation_level = old_instance.escalation_level
            except Case.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        from automation.utils import emit_event
        
        if is_new:
            emit_event('cases.created', {
                'case_id': self.id,
                'subject': self.subject,
                'priority': self.priority,
                'status': self.status,
                'owner_id': self.owner_id if self.owner else None,
                'tenant_id': self.tenant_id
            })
            
        # Check for escalation
        if self.escalation_level != 'none' and old_escalation_level == 'none':
             emit_event('cases.escalated', {
                'case_id': self.id,
                'subject': self.subject,
                'priority': self.priority,
                'escalation_level': self.escalation_level,
                'owner_id': self.owner_id if self.owner else None,
                'tenant_id': self.tenant_id
            })

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.sla_due and timezone.now() > self.sla_due and self.status not in ['resolved', 'closed']

    @property
    def sla_remaining_hours(self):
        if not self.sla_due:
            return None
        from django.utils import timezone
        delta = self.sla_due - timezone.now()
        return max(0, int(delta.total_seconds() / 3600))
    
    # Add to Case model
    def create_escalation_task(self):
        """Create escalation task for high-priority cases."""
        from tasks.models import Task
    
        if self.priority in ['high', 'critical']:
            Task.objects.create(
                title=f"Escalation required: {self.subject}",
                case_description=f"High priority case requires immediate attention",
                assigned_to=self.owner,
                case=self,
                priority='critical',
                status='todo',
                task_type='case_escalation',
                due_date=timezone.now() + timedelta(hours=2),
                tenant=self.tenant
            )


class CaseComment(TenantModel):
    """
    Internal or public comments on a case.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False)  # visible only to agents

    def __str__(self):
        return f"Comment on {self.case.subject}"


class CaseAttachment(TenantModel):
    """
    Files attached to a case.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='case_attachments/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.file.name


class KnowledgeBaseArticle(TenantModel):
    """
    Internal knowledge base for support agents.
    """
    TITLE_MAX_LENGTH = 200
    
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    content = models.TextField(help_text="Markdown or HTML content")
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    is_published = models.BooleanField(default=True)
    views = models.IntegerField(default=0)  # internal view count

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_published = False
        
        if not is_new:
            try:
                old_instance = KnowledgeBaseArticle.objects.get(pk=self.pk)
                was_published = old_instance.is_published
            except KnowledgeBaseArticle.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        from automation.utils import emit_event
        
        payload = {
            'article_id': self.id,
            'title': self.title,
            'category': self.category,
            'is_published': self.is_published,
            'tenant_id': self.tenant.id if self.tenant else None
        }
        
        if is_new:
            emit_event('knowledge_base.article_created', payload)
            
        if self.is_published and (is_new or not was_published):
            emit_event('knowledge_base.article_published', payload)
            
        if not is_new:
            emit_event('knowledge_base.article_updated', payload)


class CsatSurvey(TenantModel):
    """
    CSAT survey configuration.
    """
    csat_survey_name = models.CharField(max_length=255)
    csat_survey_description = models.TextField(blank=True)
    csat_survey_is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CsatResponse(TenantModel):
    """
    Individual CSAT response.
    """
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='csat_response')
    score = models.IntegerField()  # 1–5
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"CSAT {self.score} for {self.case.subject}"


class CsatDetractorAlert(TenantModel):
    """
    Alert for CSAT detractors requiring follow-up.
    """
    response = models.OneToOneField(CsatResponse, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')],
        default='open'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Detractor Alert for {self.response.case.subject}"


class SlaPolicy(TenantModel):
    """
    SLA policy configuration.
    """
    sla_policy_name = models.CharField(max_length=255)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    response_hours = models.IntegerField(default=24)
    resolution_hours = models.IntegerField(default=72)
    business_hours_only = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sla_policy_name} ({self.get_priority_display()})"


class AssignmentRule(TenantModel):
    """
    Assignment rules specifically for Cases.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant", 
        on_delete=models.CASCADE, 
        related_name="case_assignment_rules"
    )
    RULE_TYPE_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('territory', 'Territory-Based'),
        ('load_balanced', 'Load Balanced'),
        ('criteria', 'Criteria-Based'),
    ]

    assignment_rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    # Dynamic field reference
    rule_type_ref = models.ForeignKey(
        AssignmentRuleType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='case_assignment_rules',
        help_text="Dynamic rule type (replaces rule_type field)"
    )
    criteria = models.JSONField(default=dict, blank=True, help_text="Matching criteria, e.g., {'priority': 'high', 'type': 'bug'}")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='case_assigned_rules')
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    priority = models.IntegerField(default=1, help_text="Priority of the rule (lower numbers = higher priority)")

    def __str__(self):
        return self.assignment_rule_name