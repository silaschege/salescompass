from django import forms
from .models import FixedAsset, AssetCategory, AssetImpairment, AssetRevaluation

class AssetForm(forms.ModelForm):
    class Meta:
        model = FixedAsset
        fields = [
            'asset_number', 'name', 'category', 'purchase_date', 
            'purchase_cost', 'salvage_value', 'location', 
            'assigned_to', 'component_of', 'is_leased', 
            'lease_term_months', 'is_intangible'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = AssetCategory.objects.filter(tenant=tenant)
            from core.models import User
            self.fields['assigned_to'].queryset = User.objects.filter(tenant=tenant)
            self.fields['component_of'].queryset = FixedAsset.objects.filter(tenant=tenant)

class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = [
            'name', 'depreciation_method', 'useful_life_years',
            'asset_account', 'depreciation_account', 
            'accumulated_depreciation_account', 'impairment_account',
            'revaluation_surplus_account'
        ]

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from accounting.models import ChartOfAccount
            for field in ['asset_account', 'depreciation_account', 'accumulated_depreciation_account', 'impairment_account', 'revaluation_surplus_account']:
                self.fields[field].queryset = ChartOfAccount.objects.filter(tenant=tenant)

class AssetImpairmentForm(forms.ModelForm):
    class Meta:
        model = AssetImpairment
        fields = ['date', 'impairment_loss', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class AssetRevaluationForm(forms.ModelForm):
    class Meta:
        model = AssetRevaluation
        fields = ['date', 'new_fair_value']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
