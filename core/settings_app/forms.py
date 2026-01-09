from django import forms
from .models import Setting, CustomField, ModuleLabel, AssignmentRule, PipelineStage, EmailIntegration, BehavioralScoringRule, DemographicScoringRule, SettingType, ModelChoice, FieldType, ModuleChoice, AssignmentRuleType, PipelineType, EmailProvider, ActionType, OperatorType
from tenants.models import Tenant as TenantModel
from core.forms import DynamicChoiceWidget

class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['group', 'setting_name', 'setting_label', 'setting_description', 'setting_type', 
                  'value_text', 'value_number', 'value_boolean', 'is_required', 'is_visible', 'order']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['setting_type_ref'].queryset = SettingType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['setting_type_ref'].queryset = SettingType.objects.none()



class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = ['model_name', 'field_name', 'field_label', 'field_type', 'field_options', 
                  'is_required', 'is_visible', 'order', 'help_text']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['model_name_ref'].queryset = ModelChoice.objects.filter(tenant_id=self.tenant.id)
            self.fields['field_type_ref'].queryset = FieldType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['model_name_ref'].queryset = ModelChoice.objects.none()
            self.fields['field_type_ref'].queryset = FieldType.objects.none()


class ModuleLabelForm(forms.ModelForm):
    class Meta:
        model = ModuleLabel
        fields = ['module_key', 'custom_label', 'module_label_is_active']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['module_key_ref'].queryset = ModuleChoice.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['module_key_ref'].queryset = ModuleChoice.objects.none()





class AssignmentRuleForm(forms.ModelForm):
    class Meta:
        model = AssignmentRule
        fields = ['assignment_rule_name', 'module', 'rule_type', 'criteria', 'assigned_to', 'rule_is_active', 'priority']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['module_ref'].queryset = ModuleChoice.objects.filter(tenant_id=self.tenant.id)
            self.fields['rule_type_ref'].queryset = AssignmentRuleType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['module_ref'].queryset = ModuleChoice.objects.none()
            self.fields['rule_type_ref'].queryset = AssignmentRuleType.objects.none()


class PipelineStageForm(forms.ModelForm):
    class Meta:
        model = PipelineStage
        fields = ['pipeline_type', 'pipeline_stage_name', 'stage_description', 'order', 'probability', 
                  'is_won_stage', 'is_lost_stage']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['pipeline_type_ref'].queryset = PipelineType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['pipeline_type_ref'].queryset = PipelineType.objects.none()


class EmailIntegrationForm(forms.ModelForm):
    class Meta:
        model = EmailIntegration
        fields = ['user', 'provider', 'email_address', 'api_key', 'integration_is_active']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['provider_ref'].queryset = EmailProvider.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['provider_ref'].queryset = EmailProvider.objects.none()


class BehavioralScoringRuleForm(forms.ModelForm):
    class Meta:
        model = BehavioralScoringRule
        fields = ['behavioral_scoring_rule_name', 'action_type', 'points', 'time_decay_factor', 
                  'business_impact', 'rule_is_active']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['action_type_ref'].queryset = ActionType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['action_type_ref'].queryset = ActionType.objects.none()


class DemographicScoringRuleForm(forms.ModelForm):
    class Meta:
        model = DemographicScoringRule
        fields = ['demographic_scoring_rule_name', 'field_name', 'operator', 'field_value', 'points', 'rule_is_active']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['operator_ref'].queryset = OperatorType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['operator_ref'].queryset = OperatorType.objects.none()


class SettingTypeForm(forms.ModelForm):
    class Meta:
        model = SettingType
        fields = ['setting_type_name', 'label', 'order', 'setting_type_is_active', 'is_system']


class ModelChoiceForm(forms.ModelForm):
    class Meta:
        model = ModelChoice
        fields = ['model_choice_name', 'label', 'order', 'model_choice_is_active', 'is_system']


class FieldTypeForm(forms.ModelForm):
    class Meta:
        model = FieldType
        fields = ['field_type_name', 'label', 'order', 'field_type_is_active', 'is_system']


class ModuleChoiceForm(forms.ModelForm):
    class Meta:
        model = ModuleChoice
        fields = ['module_choice_name', 'label', 'order', 'module_choice_is_active', 'is_system']








class AssignmentRuleTypeForm(forms.ModelForm):
    class Meta:
        model = AssignmentRuleType
        fields = ['rule_type_name', 'label', 'order', 'rule_type_is_active', 'is_system']


class PipelineTypeForm(forms.ModelForm):
    class Meta:
        model = PipelineType
        fields = ['pipeline_type_name', 'label', 'order', 'pipeline_type_is_active', 'is_system']


class EmailProviderForm(forms.ModelForm):
    class Meta:
        model = EmailProvider
        fields = ['provider_name', 'label', 'order', 'provider_is_active', 'is_system']


class ActionTypeForm(forms.ModelForm):
    class Meta:
        model = ActionType
        fields = ['action_type_name', 'label', 'order', 'action_type_is_active', 'is_system']


class OperatorTypeForm(forms.ModelForm):
    class Meta:
        model = OperatorType
        fields = ['operator_name', 'label', 'order', 'operator_is_active', 'is_system']
