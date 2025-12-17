from django import forms
from django.forms.widgets import Select
from core.models import User
from .models import Lead, LeadSource, LeadStatus, Industry, MarketingChannel, AssignmentRule, ActionType, OperatorType, BehavioralScoringRule, DemographicScoringRule, WebToLeadForm
from settings_app.models import AssignmentRuleType
from tenants.models import Tenant as TenantModel


class DynamicChoiceWidget(Select):
    """Custom widget for dynamic choices that loads choices from the database"""
    def __init__(self, choice_model, *args, **kwargs):
        self.choice_model = choice_model
        super().__init__(*args, **kwargs)
    
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # Add data attributes for JavaScript to load choices dynamically
        attrs['data-dynamic-choice-model'] = self.choice_model._meta.label_lower
        return attrs


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'company', 
            'job_title', 'country', 'lead_description', 'title',
            'lead_source', 'status', 'lead_score', 'company_size',
            'annual_revenue', 'funding_stage', 'business_type',
            'source_ref', 'status_ref', 'industry_ref', 'account', 'owner',
            # New CAC fields
            'cac_cost', 'marketing_channel', 'marketing_channel_ref', 'campaign_source', 'lead_acquisition_date'
        ]
        widgets = {
            'lead_source': DynamicChoiceWidget(choice_model=LeadSource),
            'status': DynamicChoiceWidget(choice_model=LeadStatus),
            'industry': DynamicChoiceWidget(choice_model=Industry),
            'marketing_channel_ref': DynamicChoiceWidget(choice_model=MarketingChannel),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            # Update source_ref choices
            self.fields['source_ref'].queryset = LeadSource.objects.filter(tenant_id=self.tenant.id)
            # Update status_ref choices
            self.fields['status_ref'].queryset = LeadStatus.objects.filter(tenant_id=self.tenant.id)
            # Update industry_ref choices
            self.fields['industry_ref'].queryset = Industry.objects.filter(tenant_id=self.tenant.id)
            # Update marketing_channel_ref choices
            self.fields['marketing_channel_ref'].queryset = MarketingChannel.objects.filter(tenant_id=self.tenant.id)
        else:
            # Default to empty querysets if no tenant provided
            self.fields['source_ref'].queryset = LeadSource.objects.none()
            self.fields['status_ref'].queryset = LeadStatus.objects.none()
            self.fields['industry_ref'].queryset = Industry.objects.none()
            self.fields['marketing_channel_ref'].queryset = MarketingChannel.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure backward compatibility by checking both old and new fields
        source_choice = cleaned_data.get('lead_source')
        source_ref = cleaned_data.get('source_ref')
        
        if not source_choice and not source_ref:
            raise forms.ValidationError("Please select either a lead source or a dynamic lead source.")
        
        status_choice = cleaned_data.get('status')
        status_ref = cleaned_data.get('status_ref')
        
        if not status_choice and not status_ref:
            raise forms.ValidationError("Please select either a status or a dynamic status.")
        
        industry_choice = cleaned_data.get('industry')
        industry_ref = cleaned_data.get('industry_ref')
        
        if not industry_choice and not industry_ref:
            raise forms.ValidationError("Please select either an industry or a dynamic industry.")
        
        # Validate marketing channel fields
        marketing_channel_choice = cleaned_data.get('marketing_channel')
        marketing_channel_ref = cleaned_data.get('marketing_channel_ref')
        
        if not marketing_channel_choice and not marketing_channel_ref:
            # This is optional for now, but we could make it required if needed
            pass
        
        return cleaned_data


class LeadSourceForm(forms.ModelForm):
    class Meta:
        model = LeadSource
        fields = ['source_name', 'label', 'order', 'color', 'icon', 'source_is_active', 'is_system']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class LeadStatusForm(forms.ModelForm):
    class Meta:
        model = LeadStatus
        fields = ['status_name', 'label', 'order', 'color', 'icon', 'status_is_active', 'is_system', 
                  'is_qualified', 'is_closed']


class IndustryForm(forms.ModelForm):
    class Meta:
        model = Industry
        fields = ['industry_name', 'label', 'order', 'industry_is_active', 'is_system']


class AssignmentRuleForm(forms.ModelForm):
    class Meta:
        model = AssignmentRule
        fields = ['assignment_rule_name', 'rule_type', 'rule_type_ref', 'criteria', 'assigned_to', 'rule_is_active', 'priority']
        widgets = {
            'criteria': forms.Textarea(attrs={'rows': 3, 'placeholder': 'JSON format: {"country": "US"}'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'rule_type_ref': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
             if 'rule_type_ref' in self.fields:
                 self.fields['rule_type_ref'].queryset = AssignmentRuleType.objects.filter(tenant_id=self.tenant.id)
        else:
             if 'rule_type_ref' in self.fields:
                self.fields['rule_type_ref'].queryset = AssignmentRuleType.objects.none()


class ActionTypeForm(forms.ModelForm):
    class Meta:
        model = ActionType
        fields = ['action_type_name', 'label', 'order', 'action_type_is_active', 'is_system']


class OperatorTypeForm(forms.ModelForm):
    class Meta:
        model = OperatorType
        fields = ['operator_name', 'label', 'order', 'operator_is_active', 'is_system']


class BehavioralScoringRuleForm(forms.ModelForm):
    class Meta:
        model = BehavioralScoringRule
        fields = ['behavioral_scoring_rule_name', 'action_type', 'action_type_ref', 'points', 'time_decay_factor', 'business_impact', 'business_impact_ref', 'rule_is_active']
        widgets = {
            'action_type_ref': DynamicChoiceWidget(choice_model=ActionType),
            'business_impact_ref': forms.Select(attrs={'class': 'form-select'}), # Self-referencing might need care
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            if 'action_type_ref' in self.fields:
                self.fields['action_type_ref'].queryset = ActionType.objects.filter(tenant_id=self.tenant.id)
            if 'business_impact_ref' in self.fields:
                # Assuming business_impact_ref points to BehavioralScoringRule (self)
                self.fields['business_impact_ref'].queryset = BehavioralScoringRule.objects.filter(tenant_id=self.tenant.id)
        else:
            if 'action_type_ref' in self.fields:
                self.fields['action_type_ref'].queryset = ActionType.objects.none()
            if 'business_impact_ref' in self.fields:
                self.fields['business_impact_ref'].queryset = BehavioralScoringRule.objects.none()


class DemographicScoringRuleForm(forms.ModelForm):
    class Meta:
        model = DemographicScoringRule
        fields = ['demographic_scoring_rule_name', 'field_name', 'operator', 'operator_ref', 'field_value', 'points', 'rule_is_active']
        widgets = {
            'operator_ref': DynamicChoiceWidget(choice_model=OperatorType),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            if 'operator_ref' in self.fields:
                self.fields['operator_ref'].queryset = OperatorType.objects.filter(tenant_id=self.tenant.id)
        else:
            if 'operator_ref' in self.fields:
                self.fields['operator_ref'].queryset = OperatorType.objects.none()


class MarketingChannelForm(forms.ModelForm):
    class Meta:
        model = MarketingChannel
        fields = ['channel_name', 'label', 'order', 'color', 'icon', 'channel_is_active', 'is_system']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class WebToLeadForm(forms.ModelForm):
    class Meta:
        model = WebToLeadForm
        fields = [
            'form_name', 'form_description', 'form_is_active', 'success_redirect_url',
            'include_first_name', 'include_last_name', 'include_email', 'include_phone',
            'include_company', 'include_job_title', 'include_industry',
            'assign_to', 'assign_to_role'
        ]
        widgets = {
            'form_description': forms.Textarea(attrs={'rows': 3}),
            'assign_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            # Filter users by tenant (if User model has tenant link, usually user.tenant_id or similar)
            # Assuming User is available globally but we want to restrict to tenant users if possible
            # For now, simplistic approach or just pass
            pass

