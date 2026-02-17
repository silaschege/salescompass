from django import forms
from core.forms import DynamicChoiceWidget
from core.forms import DynamicChoiceWidget
from .models import Opportunity, OpportunityStage, WinLossAnalysis, DealSizeCategory, AssignmentRule, PipelineType
from settings_app.models import AssignmentRuleType
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['opportunity_name', 'account', 'amount', 'stage', 'close_date', 'probability', 
                  'esg_tagged', 'esg_impact_description', 'owner']
        widgets = {
            'stage': DynamicChoiceWidget(choice_model=OpportunityStage),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'opportunity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'probability': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esg_impact_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'
        
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
            'opportunity': forms.Select(attrs={'class': 'form-select'}),
            'win_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'loss_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'competitor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sales_cycle_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_won': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'
        
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
            'pipeline_type_ref': DynamicChoiceWidget(choice_model=PipelineType),
            'stage_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'opportunity_stage_name': forms.TextInput(attrs={'class': 'form-control'}),
            'pipeline_type': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'probability': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_won': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_lost': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'
        
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
        widgets = {
            'pipeline_type_name': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'pipeline_type_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'


class DealSizeCategoryForm(forms.ModelForm):
    class Meta:
        model = DealSizeCategory
        fields = ['category_name', 'label', 'order', 'category_is_active', 'is_system']
        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'category_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'


class AssignmentRuleForm(forms.ModelForm):
    class Meta:
        model = AssignmentRule
        fields = ['assignment_rule_name', 'rule_type', 'rule_type_ref', 'criteria', 'assigned_to', 'rule_is_active', 'priority']
        widgets = {
            'criteria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'JSON format: {"stage": "negotiation"}'}),
            'assigned_to': DynamicChoiceWidget(choice_model=User),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'rule_type_ref': DynamicChoiceWidget(choice_model=AssignmentRuleType),
            'assignment_rule_name': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'rule_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                    field.widget.attrs['class'] = 'form-select'
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-control'
        
        # Load dynamic choices based on tenant
        if self.tenant:
             if 'rule_type_ref' in self.fields:
                 self.fields['rule_type_ref'].queryset = AssignmentRuleType.objects.filter(tenant_id=self.tenant.id)
             if 'assigned_to' in self.fields:
                 self.fields['assigned_to'].queryset = User.objects.filter(tenant_id=self.tenant.id)
        else:
             if 'rule_type_ref' in self.fields:
                self.fields['rule_type_ref'].queryset = AssignmentRuleType.objects.none()
             if 'assigned_to' in self.fields:
                self.fields['assigned_to'].queryset = User.objects.none()