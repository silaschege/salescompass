from django import forms
from django.contrib.auth import get_user_model
from .models import Tenant

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
        fields = ['logo', 'primary_color', 'secondary_color']
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
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
    """Form for general tenant settings"""
    class Meta:
        model = Tenant
        fields = ['time_zone', 'default_currency', 'date_format', 'business_hours']
        widgets = {
            'time_zone': forms.Select(attrs={'class': 'form-select'}),
            'default_currency': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 3}),
            'date_format': forms.TextInput(attrs={'class': 'form-control'}),
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

