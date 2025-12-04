# apps/crm_settings/
# ├── __init__.py
# ├── admin.py
# ├── apps.py
# ├── forms.py
# ├── models.py
# ├── urls.py
# ├── views.py
# ├── utils.py
# └── templates/crm_settings/
#     ├── crm_settings_list.html
#     ├── crm_settings_form.html
#     ├── team_list.html
#     ├── team_form.html
#     ├── territory_list.html
#     ├── territory_form.html
#     ├── quota_form.html
#     └── automation_rules.html

# # Company settings
# COMPANY_NAME = "SalesCompass"
# SITE_URL = "https://your-salescompass-instance.com"

# # Email settings
# DEFAULT_FROM_EMAIL = "noreply@salescompass.com"
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

from django.db import models
from core.models import TenantModel
from core.models import User

SETTING_TYPES = [
    ('text', 'Text'),
    ('number', 'Number'),
    ('boolean', 'Boolean'),
    ('select', 'Dropdown'),
    ('json', 'JSON'),
]

class SettingGroup(TenantModel):
    """
    Group of related settings (e.g., "Pipeline", "ESG", "Automation").
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Setting(TenantModel):
    """
    Individual CRM setting.
    """
    key = models.CharField(max_length=100, unique=True)  # e.g., "pipeline.stages"
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    group = models.ForeignKey(SettingGroup, on_delete=models.CASCADE, related_name='settings')
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='text')
    
    # Values
    value_text = models.TextField(blank=True, null=True)
    value_number = models.FloatField(blank=True, null=True)
    value_boolean = models.BooleanField(default=False)
    value_json = models.JSONField(default=dict, blank=True)
    
    # Options for 'select' type
    options = models.JSONField(default=list, blank=True)
    
    # Metadata
    is_system = models.BooleanField(default=False)  # Cannot be deleted
    is_active = models.BooleanField(default=True)
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_value(self):
        """Get the actual value based on type."""
        if self.setting_type == 'number':
            return self.value_number
        elif self.setting_type == 'boolean':
            return self.value_boolean
        elif self.setting_type == 'json':
            return self.value_json
        else:
            return self.value_text

    def set_value(self, value):
        """Set value based on type."""
        if self.setting_type == 'number':
            self.value_number = float(value) if value else None
        elif self.setting_type == 'boolean':
            self.value_boolean = bool(value)
        elif self.setting_type == 'json':
            self.value_json = value if isinstance(value, dict) else {}
        else:
            self.value_text = str(value) if value else ""


class SettingChangeLog(TenantModel):
    """
    Audit log of setting changes.
    """
    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    change_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.setting.name} changed by {self.changed_by}"


# Customization Models
class CustomField(TenantModel):
    """
    Define custom fields for various models (Accounts, Leads, Opportunities, etc.).
    """
    MODEL_CHOICES = [
        ('Account', 'Account'),
        ('Lead', 'Lead'),
        ('Opportunity', 'Opportunity'),
        ('Product', 'Product'),
        ('Case', 'Case'),
    ]
    
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Checkbox'),
        ('select', 'Dropdown'),
        ('textarea', 'Text Area'),
    ]
    
    model_name = models.CharField(max_length=50, choices=MODEL_CHOICES)
    field_name = models.CharField(max_length=100, help_text="Internal field name (e.g., 'industry_sector')")
    field_label = models.CharField(max_length=255, help_text="Display label (e.g., 'Industry Sector')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    is_required = models.BooleanField(default=False)
    options = models.JSONField(default=list, blank=True, help_text="Options for select/dropdown fields")
    default_value = models.TextField(blank=True)
    help_text = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [('tenant_id', 'model_name', 'field_name')]
        ordering = ['model_name', 'order']
    
    def __str__(self):
        return f"{self.model_name}.{self.field_name}"


class ModuleLabel(TenantModel):
    """
    Custom module/app labels per tenant for white-labeling.
    """
    MODULE_CHOICES = [
        ('leads', 'Leads'),
        ('accounts', 'Accounts'),
        ('opportunities', 'Opportunities'),
        ('cases', 'Cases'),
        ('proposals', 'Proposals'),
        ('products', 'Products'),
        ('tasks', 'Tasks'),
        ('dashboard', 'Dashboard'),
        ('reports', 'Reports'),
        ('commissions', 'Commissions'),
    ]
    
    module_key = models.CharField(max_length=50, choices=MODULE_CHOICES)
    custom_label = models.CharField(max_length=100, help_text="e.g., 'Prospects' instead of 'Leads'")
    custom_label_plural = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = [('tenant_id', 'module_key')]
    
    def __str__(self):
        return f"{self.module_key} → {self.custom_label}"


# Team Management Models
TEAM_ROLE_CHOICES = [
    ('sales_rep', 'Sales Representative'),
    ('account_exec', 'Account Executive'),
    ('customer_success', 'Customer Success Manager'),
    ('support_agent', 'Support Agent'),
    ('manager', 'Manager'),
    ('admin', 'Admin'),
]

TERRITORY_CHOICES = [
    ('north_america', 'North America'),
    ('emea', 'EMEA'),
    ('apac', 'APAC'),
    ('latam', 'Latin America'),
]

class TeamRole(TenantModel):
    """
    Custom team roles with permissions.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    base_permissions = models.JSONField(default=list)  # e.g., ["accounts:read", "opportunities:write"]
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Territory(TenantModel):
    """
    Sales territories for team members.
    """
    name = models.CharField(max_length=100, choices=TERRITORY_CHOICES)
    description = models.TextField(blank=True)
    country_codes = models.JSONField(default=list)  # e.g., ["US", "CA"]
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_name_display()


class TeamMember(TenantModel):
    """
    Team member profile linked to Django User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_member')
    role = models.ForeignKey(TeamRole, on_delete=models.SET_NULL, null=True, blank=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    territory = models.ForeignKey(Territory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('onboarding', 'Onboarding'),
        ('leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='onboarding')
    
    # Performance
    quota_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    quota_period = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
        default='quarterly'
    )

    def __str__(self):
        return f"{self.user.email} ({self.get_status_display()})"

    @property
    def is_active(self):
        return self.status in ['active', 'onboarding']


class Quota(TenantModel):
    """
    Historical quota records for performance tracking.
    """
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='quotas')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    actual_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    achieved_percent = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.team_member.user.email} - {self.period_start} to {self.period_end}"


class AssignmentRule(TenantModel):
    """
    Automated assignment rules for distributing leads, cases, or opportunities.
    """
    MODULE_CHOICES = [
        ('leads', 'Leads'),
        ('cases', 'Cases'),
        ('opportunities', 'Opportunities'),
    ]
    
    RULE_TYPE_CHOICES = [
        ('round_robin', 'Round Robin'),
        ('territory', 'Territory-Based'),
        ('load_balanced', 'Load Balanced'),
        ('criteria', 'Criteria-Based'),
    ]
    
    name = models.CharField(max_length=200)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    criteria = models.JSONField(default=dict, blank=True, help_text="Matching criteria, e.g., {'country': 'US', 'industry': 'Tech'}")
    assignees = models.ManyToManyField(User, related_name='assignment_rules', help_text="Users to distribute records to")
    priority = models.IntegerField(default=0, help_text="Higher priority rules are evaluated first")
    is_active = models.BooleanField(default=True)
    
    # For round-robin tracking
    last_assigned_index = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
    
    def get_next_assignee(self):
        """Get the next assignee based on rule type."""
        assignees_list = list(self.assignees.filter(is_active=True))
        
        if not assignees_list:
            return None
            
        if self.rule_type == 'round_robin':
            # Round-robin assignment
            assignee = assignees_list[self.last_assigned_index % len(assignees_list)]
            self.last_assigned_index += 1
            self.save(update_fields=['last_assigned_index'])
            return assignee
        elif self.rule_type == 'load_balanced':
            # Assign to user with fewest open records
            # This would require counting active leads/cases per user
            # For simplicity, return first for now
            return assignees_list[0]
        else:
            # Default to first assignee
            return assignees_list[0]


class PipelineStage(TenantModel):
    """
    Configurable pipeline stages for various business processes.
    """
    PIPELINE_TYPE_CHOICES = [
        ('sales', 'Sales Pipeline'),
        ('support', 'Support Pipeline'),
        ('onboarding', 'Customer Onboarding'),
        ('renewal', 'Renewal Process'),
    ]
    
    pipeline_type = models.CharField(max_length=50, choices=PIPELINE_TYPE_CHOICES)
    name = models.CharField(max_length=100, help_text="Stage name, e.g., 'Discovery', 'Negotiation', 'Closed Won'")
    order = models.IntegerField(default=0, help_text="Display order in the pipeline")
    probability = models.IntegerField(default=0, help_text="Win probability percentage (0-100)")
    required_fields = models.JSONField(default=list, blank=True, help_text="Fields that must be filled before moving to this stage")
    approval_required = models.BooleanField(default=False, help_text="Requires manager approval to enter this stage")
    is_closed = models.BooleanField(default=False, help_text="Marks the end of the pipeline (won/lost)")
    is_won = models.BooleanField(default=False, help_text="Indicates a successful outcome")
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color for visual representation")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [('tenant_id', 'pipeline_type', 'name')]
        ordering = ['pipeline_type', 'order']
    
    def __str__(self):
        return f"{self.get_pipeline_type_display()}: {self.name}"


# Communication and Integration Models
class EmailIntegration(TenantModel):
    """
    OAuth-based email integration for Gmail/Outlook sync.
    """
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook/Office 365'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_integrations')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    email_address = models.EmailField()
    access_token = models.TextField(help_text="Encrypted OAuth access token")
    refresh_token = models.TextField(help_text="Encrypted OAuth refresh token")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)
    sync_calendar = models.BooleanField(default=False, help_text="Sync calendar events")
    sync_contacts = models.BooleanField(default=False, help_text="Sync contacts")
    
    class Meta:
        unique_together = [('user', 'provider', 'email_address')]
    
    def __str__(self):
        return f"{self.user.email} - {self.email_address} ({self.get_provider_display()})"


class APIKey(TenantModel):
    """
    API keys for external integrations and programmatic access.
    """
    name = models.CharField(max_length=200, help_text="Descriptive name for this API key")
    key_prefix = models.CharField(max_length=8, help_text="First 8 characters of the key for identification")
    key_hash = models.CharField(max_length=64, help_text="SHA-256 hash of the full key")
    scopes = models.JSONField(default=list, help_text="List of allowed permissions, e.g., ['accounts:read', 'leads:write']")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys_created')
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"
    
    @staticmethod
    def generate_key():
        """Generate a secure random API key."""
        import secrets
        return f"sk_{secrets.token_urlsafe(32)}"
    
    def set_key(self, key):
        """Hash and store the API key."""
        import hashlib
        self.key_prefix = key[:8]
        self.key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    def verify_key(self, key):
        """Verify a provided key against the stored hash."""
        import hashlib
        return self.key_hash == hashlib.sha256(key.encode()).hexdigest()


class Webhook(TenantModel):
    """
    Webhooks for sending event notifications to external systems.
    """
    name = models.CharField(max_length=200)
    url = models.URLField(help_text="Endpoint URL to POST events to")
    events = models.JSONField(default=list, help_text="Event types to subscribe to, e.g., ['lead.created', 'opportunity.won']")
    secret = models.CharField(max_length=64, help_text="Secret for HMAC signature verification")
    is_active = models.BooleanField(default=True)
    
    # Stats
    last_triggered = models.DateTimeField(null=True, blank=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} → {self.url}"
    
    @staticmethod
    def generate_secret():
        """Generate a secure webhook secret."""
        import secrets
        return secrets.token_hex(32)


# Lead Scoring Models
class BehavioralScoringRule(TenantModel):
    """
    Define scoring rules for behavioral actions (email opens, clicks, etc.).
    """
    ACTION_TYPE_CHOICES = [
        ('email_open', 'Email Open'),
        ('link_click', 'Link Click'),
        ('web_visit', 'Website Visit'),
        ('form_submit', 'Form Submission'),
        ('content_download', 'Content Download'),
        ('landing_page_visit', 'Landing Page Visit'),
    ]
    
    name = models.CharField(max_length=200, help_text="Rule name, e.g., 'Email Open Scoring'")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    points = models.IntegerField(help_text="Points to award for this action")
    frequency_cap = models.IntegerField(
        default=0, 
        help_text="Max times this action scores per lead per day (0 = unlimited)"
    )
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority rules are evaluated first")
    
    class Meta:
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_action_type_display()}: {self.points} pts)"


class DemographicScoringRule(TenantModel):
    """
    Define scoring rules based on demographic/firmographic data.
    """
    OPERATOR_CHOICES = [
        ('equals', 'Equals'),
        ('contains', 'Contains'),
        ('in', 'In List'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
    ]
    
    name = models.CharField(max_length=200, help_text="Rule name, e.g., 'Enterprise Company Scoring'")
    field_name = models.CharField(
        max_length=100, 
        help_text="Field to evaluate, e.g., 'job_title', 'industry', 'company_size'"
    )
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES, default='equals')
    field_value = models.CharField(max_length=500, help_text="Value to match against")
    points = models.IntegerField(help_text="Points to award if condition matches")
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority rules are evaluated first")
    
    class Meta:
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.field_name} {self.operator} '{self.field_value}': {self.points} pts)"
    
    def evaluate(self, lead_data):
        """
        Evaluate if this rule matches the lead data.
        
        Args:
            lead_data: Dictionary of lead attributes
            
        Returns:
            True if rule matches, False otherwise
        """
        actual_value = lead_data.get(self.field_name)
        if actual_value is None:
            return False
        
        if self.operator == 'equals':
            return str(actual_value).lower() == str(self.field_value).lower()
        elif self.operator == 'contains':
            return str(self.field_value).lower() in str(actual_value).lower()
        elif self.operator == 'in':
            values_list = [v.strip() for v in self.field_value.split(',')]
            return str(actual_value) in values_list
        elif self.operator == 'gt':
            try:
                return float(actual_value) > float(self.field_value)
            except (ValueError, TypeError):
                return False
        elif self.operator == 'lt':
            try:
                return float(actual_value) < float(self.field_value)
            except (ValueError, TypeError):
                return False
        
        return False


class ScoreDecayConfig(TenantModel):
    """
    Configuration for automatic score decay over time.
    Only one config per tenant.
    """
    decay_enabled = models.BooleanField(default=False, help_text="Enable automatic score decay")
    decay_rate = models.FloatField(
        default=5.0, 
        help_text="Percentage to decay per period (e.g., 5 = 5% decay)"
    )
    decay_period_days = models.IntegerField(
        default=30, 
        help_text="Days between decay applications"
    )
    min_score = models.IntegerField(
        default=0, 
        help_text="Minimum score floor (decay stops here)"
    )
    last_decay_run = models.DateTimeField(null=True, blank=True, help_text="Last time decay was applied")
    
    class Meta:
        verbose_name = "Score Decay Configuration"
        verbose_name_plural = "Score Decay Configurations"
    
    def __str__(self):
        status = "Enabled" if self.decay_enabled else "Disabled"
        return f"Score Decay Config ({status}: {self.decay_rate}% every {self.decay_period_days} days)"
