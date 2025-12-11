from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from marketing.models import EmailProvider

# Legacy choices - kept for backward compatibility during migration
SETTING_TYPES = [
    ('text', 'Text'),
    ('number', 'Number'),
    ('boolean', 'Boolean'),
    ('select', 'Dropdown'),
    ('json', 'JSON'),
]

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

TEAM_ROLE_CHOICES = [
    ('sales_rep', 'Sales Representative'),
    ('sales_manager', 'Sales Manager'),
    ('account_manager', 'Account Manager'),
    ('sales_director', 'Sales Director'),
    ('ceo', 'CEO'),
    ('admin', 'Administrator'),
]

TERRITORY_CHOICES = [
    ('north_america', 'North America'),
    ('emea', 'EMEA'),
    ('apac', 'APAC'),
    ('latam', 'Latin America'),
]

STATUS_CHOICES = [
    ('active', 'Active'),
    ('onboarding', 'Onboarding'),
    ('leave', 'On Leave'),
    ('terminated', 'Terminated'),
]

QUOTA_PERIOD_CHOICES = [
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('yearly', 'Yearly'),
]

MODULE_CHOICES_ASSIGNMENT = [
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

PIPELINE_TYPE_CHOICES = [
    ('sales', 'Sales Pipeline'),
    ('support', 'Support Pipeline'),
    ('onboarding', 'Customer Onboarding'),
    ('renewal', 'Renewal Process'),
]

PROVIDER_CHOICES = [
    ('gmail', 'Gmail'),
    ('outlook', 'Outlook/Office 365'),
]

ACTION_TYPE_CHOICES = [
    ('email_open', 'Email Open'),
    ('link_click', 'Link Click'),
    ('web_visit', 'Website Visit'),
    ('form_submit', 'Form Submission'),
    ('content_download', 'Content Download'),
    ('landing_page_visit', 'Landing Page Visit'),
]

OPERATOR_CHOICES = [
    ('equals', 'Equals'),
    ('contains', 'Contains'),
    ('in', 'In List'),
    ('gt', 'Greater Than'),
    ('lt', 'Less Than'),
]

BUSINESS_IMPACT_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]


class SettingType(TenantModel):
    """
    Dynamic setting type values - allows tenant-specific setting type tracking.
    """
    setting_type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'text', 'number'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Text', 'Number'
    order = models.IntegerField(default=0)
    setting_type_is_active = models.BooleanField(default=True, help_text="Whether this setting type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'setting_type_name']
        unique_together = [('tenant_id', 'setting_type_name')]
        verbose_name_plural = 'Setting Types'
    
    def __str__(self):
        return self.label


class ModelChoice(TenantModel):
    """
    Dynamic model choice values - allows tenant-specific model choice tracking.
    """
    model_choice_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'Account', 'Lead'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100) # e.g., 'Account', 'Lead'
    order = models.IntegerField(default=0)
    model_choice_is_active = models.BooleanField(default=True, help_text="Whether this model choice is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'model_choice_name']
        unique_together = [('tenant_id', 'model_choice_name')]
        verbose_name_plural = 'Model Choices'
    
    def __str__(self):
        return self.label


class FieldType(TenantModel):
    """
    Dynamic field type values - allows tenant-specific field type tracking.
    """
    field_type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'text', 'number'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Text', 'Number'
    order = models.IntegerField(default=0)
    field_type_is_active = models.BooleanField(default=True, help_text="Whether this field type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'field_type_name']
        unique_together = [('tenant_id', 'field_type_name')]
        verbose_name_plural = 'Field Types'
    
    def __str__(self):
        return self.label


class ModuleChoice(TenantModel):
    """
    Dynamic module choice values - allows tenant-specific module choice tracking.
    """
    module_choice_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'leads', 'accounts'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Leads', 'Accounts'
    order = models.IntegerField(default=0)
    module_choice_is_active = models.BooleanField(default=True, help_text="Whether this module choice is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'module_choice_name']
        unique_together = [('tenant_id', 'module_choice_name')]
        verbose_name_plural = 'Module Choices'
    
    def __str__(self):
        return self.label


class TeamRole(TenantModel):
    """
    Dynamic team role values - allows tenant-specific team role tracking.
    """
    role_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'sales_rep', 'sales_manager'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Sales Representative', 'Sales Manager'
    order = models.IntegerField(default=0)
    role_is_active = models.BooleanField(default=True, help_text="Whether this role is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'role_name']
        unique_together = [('tenant_id', 'role_name')]
        verbose_name_plural = 'Team Roles'
    
    def __str__(self):
        return self.label


class Territory(TenantModel):
    """
    Dynamic territory values - allows tenant-specific territory tracking.
    """
    territory_name = models.CharField(max_length=100, db_index=True, help_text="e.g., 'north_america', 'emea'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'North America', 'EMEA'
    order = models.IntegerField(default=0)
    territory_is_active = models.BooleanField(default=True, help_text="Whether this territory is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'territory_name']
        unique_together = [('tenant_id', 'territory_name')]
        verbose_name_plural = 'Territories'
    
    def __str__(self):
        return self.label


class AssignmentRuleType(TenantModel):
    """
    Dynamic assignment rule type values - allows tenant-specific rule type tracking.
    """
    rule_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'round_robin', 'territory'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Round Robin', 'Territory-Based'
    order = models.IntegerField(default=0)
    rule_type_is_active = models.BooleanField(default=True, help_text="Whether this rule type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'rule_type_name']
        unique_together = [('tenant_id', 'rule_type_name')]
        verbose_name_plural = 'Assignment Rule Types'
    
    def __str__(self):
        return self.label


class PipelineType(TenantModel):
    """
    Dynamic pipeline type values - allows tenant-specific pipeline type tracking.
    """
    pipeline_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'sales', 'support'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Sales Pipeline', 'Support Pipeline'
    order = models.IntegerField(default=0)
    pipeline_type_is_active = models.BooleanField(default=True, help_text="Whether this pipeline type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'pipeline_type_name']
        unique_together = [('tenant_id', 'pipeline_type_name')]
        verbose_name_plural = 'Pipeline Types'
    
    def __str__(self):
        return self.label


# EmailProvider is now imported from marketing.models to avoid duplication
# class EmailProvider(TenantModel):
#     ... deleted ...



class ActionType(TenantModel):
    """
    Dynamic action type values - allows tenant-specific action type tracking.
    """
    action_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'email_open', 'link_click'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Email Open', 'Link Click'
    order = models.IntegerField(default=0)
    action_type_is_active = models.BooleanField(default=True, help_text="Whether this action type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'action_type_name']
        unique_together = [('tenant_id', 'action_type_name')]
        verbose_name_plural = 'Action Types'
    
    def __str__(self):
        return self.label


class OperatorType(TenantModel):
    """
    Dynamic operator type values - allows tenant-specific operator type tracking.
    """
    operator_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'equals', 'contains'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Equals', 'Contains'
    order = models.IntegerField(default=0)
    operator_is_active = models.BooleanField(default=True, help_text="Whether this operator is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'operator_name']
        unique_together = [('tenant_id', 'operator_name')]
        verbose_name_plural = 'Operator Types'
    
    def __str__(self):
        return self.label


class SettingGroup(TenantModel):
    setting_group_name = models.CharField(max_length=200, unique=True, help_text="Name of the setting group")  # Renamed from 'name' to avoid conflict
    setting_group_description = models.TextField(blank=True, help_text="Description of the setting group")  # Renamed from 'description' to avoid conflict with base class
    setting_group_is_active = models.BooleanField(default=True, help_text="Whether this setting group is active")  # Renamed from 'is_active' to avoid conflict with base class

    def __str__(self):
        return self.setting_group_name


class Setting(TenantModel):
    group = models.ForeignKey(SettingGroup, on_delete=models.CASCADE, related_name='settings')
    setting_name = models.CharField(max_length=200, unique=True)
    setting_label = models.CharField(max_length=200)
    setting_description = models.TextField(blank=True, help_text="Description of the setting")  # Renamed from 'description' to avoid conflict with base class
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='text')
    # New dynamic field
    setting_type_ref = models.ForeignKey(
        SettingType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='settings',
        help_text="Dynamic setting type (replaces setting_type field)"
    )
    value_text = models.TextField(null=True, blank=True)
    value_number = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)
    is_required = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.setting_label


class CustomField(TenantModel):
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
    # New dynamic field
    model_name_ref = models.ForeignKey(
        ModelChoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='custom_fields',
        help_text="Dynamic model name (replaces model_name field)"
    )
    field_name = models.CharField(max_length=100, help_text="Internal field name (e.g., 'industry_sector')")
    field_label = models.CharField(max_length=255, help_text="Display label (e.g., 'Industry Sector')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    # New dynamic field
    field_type_ref = models.ForeignKey(
        FieldType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='custom_fields',
        help_text="Dynamic field type (replaces field_type field)"
    )
    field_options = models.JSONField(default=list, blank=True, help_text="Options for select fields")
    is_required = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    help_text = models.TextField(blank=True, help_text="Help text to display with the field")

    def __str__(self):
        return f"{self.model_name}.{self.field_name}"


class ModuleLabel(TenantModel):
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
    # New dynamic field
    module_key_ref = models.ForeignKey(
        ModuleChoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='module_labels',
        help_text="Dynamic module key (replaces module_key field)"
    )
    custom_label = models.CharField(max_length=100, help_text="e.g., 'Prospects' instead of 'Leads'")
    module_label_is_active = models.BooleanField(default=True, help_text="Whether this module label is active")  # Renamed from 'is_active' to avoid conflict with base class

    def __str__(self):
        return f"{self.module_key}: {self.custom_label}"


class TeamMember(TenantModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_member')
    role = models.CharField(max_length=50, choices=TEAM_ROLE_CHOICES)
    # New dynamic field
    role_ref = models.ForeignKey(
        TeamRole,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='team_members',
        help_text="Dynamic role (replaces role field)"
    )
    territory = models.CharField(max_length=100, choices=TERRITORY_CHOICES, blank=True)
    # New dynamic field
    territory_ref = models.ForeignKey(
        Territory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='team_members',
        help_text="Dynamic territory (replaces territory field)"
    )
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='onboarding')
    # New dynamic field
    status_ref = models.ForeignKey(
        'self',  # Self reference for status - this might need to be a separate model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members_by_status',
        help_text="Dynamic status (replaces status field)"
    )
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    quota_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    quota_period = models.CharField(max_length=20, choices=QUOTA_PERIOD_CHOICES, default='quarterly')
    # New dynamic field
    quota_period_ref = models.ForeignKey(
        'self',  # Self reference for period - this might need to be a separate model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members_by_period',
        help_text="Dynamic quota period (replaces quota_period field)"
    )
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Commission rate (e.g. 10.0 for 10%)")

    # Territory Performance Metrics (added for territory optimization)
    territory_performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                     help_text="Performance score within assigned territory (0-100)")
    territory_quota_attainment = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                    help_text="Percentage of territory quota attained")
    territory_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                   help_text="Lead to opportunity conversion rate in territory (%)")
    territory_revenue_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, 
                                                        help_text="Revenue contribution to assigned territory")

    def __str__(self):
        return f"{self.user.email} - {self.role}"


class AssignmentRule(TenantModel):
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

    assignment_rule_name = models.CharField(max_length=200)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    # New dynamic field
    module_ref = models.ForeignKey(
        ModuleChoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assignment_rules',
        help_text="Dynamic module (replaces module field)"
    )
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE_CHOICES)
    # New dynamic field
    rule_type_ref = models.ForeignKey(
        AssignmentRuleType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assignment_rules',
        help_text="Dynamic rule type (replaces rule_type field)"
    )
    criteria = models.JSONField(default=dict, blank=True, help_text="Matching criteria, e.g., {'country': 'US', 'industry': 'Tech'}")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_rules')
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")  # Renamed from 'is_active' to avoid conflict with base class
    priority = models.IntegerField(default=1, help_text="Priority of the rule (lower numbers = higher priority)")

    def __str__(self):
        return self.assignment_rule_name


class PipelineStage(TenantModel):
    PIPELINE_TYPE_CHOICES = [
        ('sales', 'Sales Pipeline'),
        ('support', 'Support Pipeline'),
        ('onboarding', 'Customer Onboarding'),
        ('renewal', 'Renewal Process'),
    ]

    pipeline_type = models.CharField(max_length=50, choices=PIPELINE_TYPE_CHOICES)
    # New dynamic field
    pipeline_type_ref = models.ForeignKey(
        PipelineType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='pipeline_stages',
        help_text="Dynamic pipeline type (replaces pipeline_type field)"
    )
    pipeline_stage_name = models.CharField(max_length=100, help_text="Stage name, e.g., 'Discovery', 'Negotiation', 'Closed Won'")
    stage_description = models.TextField(blank=True, help_text="Description of the pipeline stage")  # Renamed from 'description' to avoid conflict with base class
    order = models.IntegerField(default=0)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Default probability for this stage (0-100)")
    is_won_stage = models.BooleanField(default=False, help_text="Whether this stage represents a won opportunity")
    is_lost_stage = models.BooleanField(default=False, help_text="Whether this stage represents a lost opportunity")

    def __str__(self):
        return f"{self.pipeline_type}: {self.pipeline_stage_name}"


class EmailIntegration(TenantModel):
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook/Office 365'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_integrations')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    # New dynamic field
    provider_ref = models.ForeignKey(
        EmailProvider,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='email_integrations',
        help_text="Dynamic provider (replaces provider field)"
    )
    email_address = models.EmailField()
    integration_is_active = models.BooleanField(default=True, help_text="Whether this integration is active")  # Renamed from 'is_active' to avoid conflict with base class
    last_sync = models.DateTimeField(null=True, blank=True)
    api_key = models.TextField(blank=True, help_text="API key or access token")
    refresh_token = models.TextField(blank=True, help_text="Refresh token for OAuth")

    def __str__(self):
        return f"{self.email_address} ({self.provider})"


class BehavioralScoringRule(TenantModel):
    ACTION_TYPE_CHOICES = [
        ('email_open', 'Email Open'),
        ('link_click', 'Link Click'),
        ('web_visit', 'Website Visit'),
        ('form_submit', 'Form Submission'),
        ('content_download', 'Content Download'),
        ('landing_page_visit', 'Landing Page Visit'),
    ]

    OPERATOR_CHOICES = [
        ('equals', 'Equals'),
        ('contains', 'Contains'),
        ('in', 'In List'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
    ]

    BUSINESS_IMPACT_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    behavioral_scoring_rule_name = models.CharField(max_length=200, help_text="Rule name, e.g., 'Email Open Scoring'")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    # New dynamic field
    action_type_ref = models.ForeignKey(
        ActionType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='behavioral_scoring_rules',
        help_text="Dynamic action type (replaces action_type field)"
    )
    points = models.IntegerField(help_text="Points to award for this action")
    time_decay_factor = models.FloatField(default=1.0, help_text="Multiplier for time-based decay of this action's value")
    business_impact = models.CharField(max_length=50, choices=BUSINESS_IMPACT_CHOICES)
    # New dynamic field
    business_impact_ref = models.ForeignKey(
        'self',  # Self reference for impact - this might need to be a separate model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='behavioral_scoring_rules_by_impact',
        help_text="Dynamic business impact (replaces business_impact field)"
    )
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")  # Renamed from 'is_active' to avoid conflict with base class

    def __str__(self):
        return self.behavioral_scoring_rule_name


class DemographicScoringRule(TenantModel):
    OPERATOR_CHOICES = [
        ('equals', 'Equals'),
        ('contains', 'Contains'),
        ('in', 'In List'),
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
    ]

    demographic_scoring_rule_name = models.CharField(max_length=200, help_text="Rule name, e.g., 'Job Title Scoring'")
    field_name = models.CharField(max_length=100, help_text="Field to evaluate, e.g., 'job_title', 'industry', 'company_size'")
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES, default='equals')
    # New dynamic field
    operator_ref = models.ForeignKey(
        OperatorType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='demographic_scoring_rules',
        help_text="Dynamic operator (replaces operator field)"
    )
    field_value = models.CharField(max_length=500, help_text="Value to match against")
    points = models.IntegerField(help_text="Points to award when condition is met")
    rule_is_active = models.BooleanField(default=True, help_text="Whether this rule is active")  # Renamed from 'is_active' to avoid conflict with base class

    def __str__(self):
        return self.demographic_scoring_rule_name
