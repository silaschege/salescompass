# apps/crm_settings/forms.py
from django import forms
from .models import (
    TeamMember, Setting, CustomField, ModuleLabel, AssignmentRule, PipelineStage, APIKey, Webhook,
    BehavioralScoringRule, DemographicScoringRule, ScoreDecayConfig
)

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = [
            'user', 'role', 'manager', 'territory', 
            'phone', 'hire_date', 'status',
            'quota_amount', 'quota_period'
        ]
        widgets = { 
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(),  # We handle this manually in the template
        }

class DynamicSettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Add field based on setting type
            if self.instance.setting_type == 'boolean':
                self.fields['value'] = forms.BooleanField(
                    label=self.instance.name,
                    required=False,
                    initial=self.instance.value_boolean
                )
            elif self.instance.setting_type == 'select':
                self.fields['value'] = forms.ChoiceField(
                    label=self.instance.name,
                    choices=[(opt, opt) for opt in self.instance.options],
                    initial=self.instance.value_text
                )
            else:
                self.fields['value'] = forms.CharField(
                    label=self.instance.name,
                    initial=self.instance.get_value(),
                    widget=forms.Textarea() if self.instance.setting_type == 'json' else forms.TextInput()
                )

    def save(self, commit=True):
        setting = super().save(commit=False)
        value = self.cleaned_data['value']
        setting.set_value(value)
        if commit:
            setting.save()
        return setting

class TenantSettingsForm(forms.ModelForm):
    class Meta:
        from tenants.models import Tenant
        model = Tenant
        fields = ['name', 'domain', 'logo', 'primary_color', 'secondary_color', 
                  'business_hours', 'default_currency', 'date_format', 'time_zone']
        widgets = {
            'logo': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            }),
            'primary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control'
            }),
            'secondary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control'
            }),
            'business_hours': forms.Textarea(attrs={
                'rows': 10,
                'class': 'form-control json-editor',
                'placeholder': '{"monday": {"open": "09:00", "close": "17:00"}}'
            }),
            'default_currency': forms.Select(attrs={'class': 'form-control'}),
            'time_zone': forms.Select(attrs={'class': 'form-control'}),
        }

class LeadStatusForm(forms.ModelForm):
    class Meta:
        from leads.models import LeadStatus
        model = LeadStatus
        fields = ['label', 'name', 'color', 'is_active', 'is_qualified', 'is_closed', 'order']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

class LeadSourceForm(forms.ModelForm):
    class Meta:
        from leads.models import LeadSource
        model = LeadSource
        fields = ['label', 'name', 'color', 'is_active', 'conversion_rate_target', 'order']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

class OpportunityStageForm(forms.ModelForm):
    class Meta:
        from opportunities.models import OpportunityStage
        model = OpportunityStage
        fields = ['name', 'order', 'probability', 'is_won', 'is_lost']

class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = ['model_name', 'field_name', 'field_label', 'field_type', 'is_required', 
                  'options', 'default_value', 'help_text', 'order', 'is_active']
        widgets = {
            'model_name': forms.Select(attrs={'class': 'form-control'}),
            'field_name': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[a-z_][a-z0-9_]*',
                'placeholder': 'e.g., industry_sector'
            }),
            'field_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Industry Sector'
            }),
            'field_type': forms.RadioSelect(),
            'options': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Enter each option on a new line'
            }),
            'help_text': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control'
            }),
            'default_value': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ModuleLabelForm(forms.ModelForm):
    class Meta:
        model = ModuleLabel
        fields = ['module_key', 'custom_label', 'custom_label_plural']

class AssignmentRuleForm(forms.ModelForm):
    class Meta:
        model = AssignmentRule
        fields = ['name', 'module', 'rule_type', 'criteria', 'assignees', 
                  'priority', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Assign US Leads to US Team'
            }),
            'module': forms.Select(attrs={'class': 'form-control'}),
            'rule_type': forms.RadioSelect(),
            'criteria': forms.Textarea(attrs={
                'rows': 8,
                'class': 'form-control json-editor',
                'placeholder': '{"country": "US", "industry": "Technology"}'
            }),
            'assignees': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '10'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control priority-input',
                'min': 0,
                'max': 100
            }),
        }

class PipelineStageForm(forms.ModelForm):
    class Meta:
        model = PipelineStage
        fields = ['pipeline_type', 'name', 'order', 'probability', 'required_fields',
                  'approval_required', 'is_closed', 'is_won', 'color', 'is_active']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'required_fields': forms.Textarea(attrs={'rows': 2, 'placeholder': '["field1", "field2"]'}),
        }

class APIKeyForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ['name', 'scopes', 'expires_at']
        widgets = {
            'scopes': forms.Textarea(attrs={'rows': 3, 'placeholder': '["accounts:read", "leads:write"]'}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class WebhookForm(forms.ModelForm):
    class Meta:
        model = Webhook
        fields = ['name', 'url', 'events', 'is_active']
        widgets = {
            'events': forms.Textarea(attrs={'rows': 3, 'placeholder': '["lead.created", "opportunity.won"]'}),
        }

class TeamRoleForm(forms.ModelForm):
    class Meta:
        from .models import TeamRole
        model = TeamRole
        fields = ['name', 'description', 'base_permissions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'base_permissions': forms.HiddenInput(),
        }


# Lead Scoring Forms
class BehavioralScoringRuleForm(forms.ModelForm):
    class Meta:
        model = BehavioralScoringRule
        fields = ['name', 'action_type', 'points', 'frequency_cap', 'priority', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Email Open Scoring'}),
            'action_type': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': -100, 'max': 100}),
            'frequency_cap': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }


class DemographicScoringRuleForm(forms.ModelForm):
    class Meta:
        model = DemographicScoringRule
        fields = ['name', 'field_name', 'operator', 'field_value', 'points', 'priority', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Enterprise Company Scoring'}),
            'field_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., job_title, industry'}),
            'operator': forms.Select(attrs={'class': 'form-control'}),
            'field_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Manager, Technology'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': -100, 'max': 100}),
            'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }


class ScoreDecayConfigForm(forms.ModelForm):
    class Meta:
        model = ScoreDecayConfig
        fields = ['decay_enabled', 'decay_rate', 'decay_period_days', 'min_score']
        widgets = {
            'decay_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.1}),
            'decay_period_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'min_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }