from django import forms
from core.forms import DynamicChoiceWidget
from .models import Opportunity, OpportunityStage, WinLossAnalysis, DealSizeCategory
from tenants.models import TenantAwareModel as TenantModel


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['opportunity_name', 'account', 'amount', 'stage', 'close_date', 'probability', 
                  'esg_tagged', 'esg_impact_description', 'owner', 'tenant_id']
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
        fields = ['opportunity_stage_name', 'order', 'probability', 'is_won', 'is_lost']


class DealSizeCategoryForm(forms.ModelForm):
    class Meta:
        model = DealSizeCategory
        fields = ['category_name', 'label', 'order', 'category_is_active', 'is_system']
