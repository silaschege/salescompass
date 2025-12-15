from django import forms
from core.forms import DynamicChoiceWidget
from core.forms import DynamicChoiceWidget
from .models import Opportunity, OpportunityStage, WinLossAnalysis, DealSizeCategory, AssignmentRule, PipelineType
from settings_app.models import AssignmentRuleType
from tenants.models import TenantAwareModel as TenantModel


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['opportunity_name', 'account', 'amount', 'stage', 'close_date', 'probability', 
                  'esg_tagged', 'esg_impact_description', 'owner']
        widgets = {
            'stage': DynamicChoiceWidget(choice_model=OpportunityStage),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['stage'].queryset = OpportunityStage.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['stage'].queryset = OpportunityStage.objects.none()


class WinLossAnalysisForm(forms.ModelForm):
    class Meta:
        model = WinLossAnalysis
        fields = ['opportunity', 'is_won', 'win_reason', 'loss_reason', 'competitor_name', 
                  'sales_cycle_days', 'deal_size_category_ref']
        widgets = {
            'deal_size_category_ref': DynamicChoiceWidget(choice_model=DealSizeCategory),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['deal_size_category_ref'].queryset = DealSizeCategory.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['deal_size_category_ref'].queryset = DealSizeCategory.objects.none()


class OpportunityStageForm(forms.ModelForm):
    class Meta:
        model = OpportunityStage
        fields = ['opportunity_stage_name', 'pipeline_type', 'pipeline_type_ref', 'stage_description', 'order', 'probability', 'is_won', 'is_lost']
        widgets = {
            'pipeline_type_ref': forms.Select(attrs={'class': 'form-select'}),
            'stage_description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            if 'pipeline_type_ref' in self.fields:
                self.fields['pipeline_type_ref'].queryset = PipelineType.objects.filter(tenant_id=self.tenant.id)
        else:
            if 'pipeline_type_ref' in self.fields:
                self.fields['pipeline_type_ref'].queryset = PipelineType.objects.none()


class PipelineTypeForm(forms.ModelForm):
    class Meta:
        model = PipelineType
        fields = ['pipeline_type_name', 'label', 'order', 'pipeline_type_is_active', 'is_system']


class DealSizeCategoryForm(forms.ModelForm):
    class Meta:
        model = DealSizeCategory
        fields = ['category_name', 'label', 'order', 'category_is_active', 'is_system']


class AssignmentRuleForm(forms.ModelForm):
    class Meta:
        model = AssignmentRule
        fields = ['assignment_rule_name', 'rule_type', 'rule_type_ref', 'criteria', 'assigned_to', 'rule_is_active', 'priority']
        widgets = {
            'criteria': forms.Textarea(attrs={'rows': 3, 'placeholder': 'JSON format: {"stage": "negotiation"}'}),
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

