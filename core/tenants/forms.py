from django import forms
from django.contrib.auth import get_user_model
from django.forms.widgets import Select
from .models import Tenant, TenantSettings, Setting, SettingGroup, SettingType


User = get_user_model()

class TenantSignupForm(forms.ModelForm):
    company_name = forms.CharField(max_length=255, label="Company Name")
    email = forms.EmailField(label="Work Email")
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        
    def save(self, commit=True):
        # We don't save the user here directly, as we need to create the tenant first
        # This logic will be handled in the view
        return super().save(commit=False)


class TenantBrandingForm(forms.ModelForm):
    """Form for updating tenant branding"""
    class Meta:
        model = Tenant
        fields = ['logo_url', 'primary_color', 'secondary_color']
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'logo_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/logo.png'}),
        }


class TenantDomainForm(forms.ModelForm):
    """Form for managing tenant custom domain"""
    class Meta:
        model = Tenant
        fields = ['domain']
        widgets = {
            'domain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'yourdomain.com'
            })
        }


class TenantSettingsForm(forms.ModelForm):
    """Form for general tenant settings - uses TenantSettings model"""
    class Meta:
        model = TenantSettings
        fields = ['time_zone', 'default_currency', 'date_format', 'business_hours']
        widgets = {
            'time_zone': forms.Select(attrs={'class': 'form-select'}),
            'default_currency': forms.Select(attrs={'class': 'form-select'}),
            'date_format': forms.Select(attrs={'class': 'form-select'}),
            'business_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class FeatureToggleForm(forms.Form):
    """Form for managing feature toggles"""
    feature_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


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


class SettingTypeForm(forms.ModelForm):
    class Meta:
        model = SettingType
        fields = ['setting_type_name', 'label', 'order', 'setting_type_is_active', 'is_system']


class SettingGroupForm(forms.ModelForm):
    class Meta:
        model = SettingGroup
        fields = ['setting_group_name', 'setting_group_description', 'setting_group_is_active']


class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['group', 'setting_name', 'setting_label', 'setting_description', 'setting_type', 
                  'setting_type_ref', 'value_text', 'value_number', 'value_boolean', 
                  'is_required', 'is_visible', 'order']
        widgets = {
            'setting_type_ref': DynamicChoiceWidget(choice_model=SettingType),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.fields['group'].queryset = SettingGroup.objects.filter(tenant_id=self.tenant.id)
            if 'setting_type_ref' in self.fields:
                self.fields['setting_type_ref'].queryset = SettingType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['group'].queryset = SettingGroup.objects.none()
            if 'setting_type_ref' in self.fields:
                self.fields['setting_type_ref'].queryset = SettingType.objects.none()

