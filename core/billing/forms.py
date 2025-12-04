from django import forms
from .models import Plan, Subscription, CreditAdjustment, Invoice

class PlanForm(forms.ModelForm):
    """Form for creating and editing subscription plans"""
    class Meta:
        model = Plan
        fields = [
            'name', 'slug', 'tier', 'price_monthly', 'price_yearly',
            'max_users', 'max_leads', 'max_storage_gb', 'features', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'tier': forms.Select(attrs={'class': 'form-select'}),
            'price_monthly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_yearly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_users': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_leads': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_storage_gb': forms.NumberInput(attrs={'class': 'form-control'}),
            'features': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SubscriptionUpdateForm(forms.ModelForm):
    """Form for updating subscription details"""
    class Meta:
        model = Subscription
        fields = ['plan', 'status', 'billing_email']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'billing_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class CreditAdjustmentForm(forms.ModelForm):
    """Form for applying credit adjustments"""
    class Meta:
        model = CreditAdjustment
        fields = ['tenant_id', 'adjustment_type', 'amount', 'reason']
        widgets = {
            'tenant_id': forms.TextInput(attrs={'class': 'form-control'}),
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InvoiceSearchForm(forms.Form):
    """Form for searching invoices"""
    tenant_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by tenant ID'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Invoice.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class ProrationForm(forms.Form):
    """Form for calculating proration"""
    subscription_id = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    new_plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
