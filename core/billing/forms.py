from django import forms
from .models import Plan, Subscription, Invoice, CreditAdjustment, PaymentProviderConfig, PaymentMethod, Payment, PlanTier, SubscriptionStatus, AdjustmentType, PaymentProvider, PaymentType
from tenants.models import Tenant as TenantModel
from core.models import User

 
class PlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Accept and pop the tenant argument to prevent errors
        # The Plan model is global and doesn't require tenant filtering
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Apply consistent styling to form fields
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        self.fields['price'].widget.attrs.update({'class': 'form-control', 'step': '0.01'})
        self.fields['max_users'].widget.attrs.update({'class': 'form-control'})
        self.fields['storage_limit'].widget.attrs.update({'class': 'form-control'})
        self.fields['api_calls_limit'].widget.attrs.update({'class': 'form-control'})
        self.fields['has_reports'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['has_custom_fields'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['has_integrations'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['is_featured'].widget.attrs.update({'class': 'form-check-input'})
 
    class Meta:
        model = Plan
        fields = ['name', 'description', 'price', 'max_users', 'storage_limit', 'api_calls_limit', 
                  'has_reports', 'has_custom_fields', 'has_integrations', 'is_active', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_users': forms.NumberInput(attrs={'class': 'form-control'}),
            'storage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'api_calls_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'has_reports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_custom_fields': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_integrations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        # Note: start_date is auto_now_add, so it's non-editable
        fields = ['subscription_plan', 'user', 'status', 'status_ref', 'end_date', 
                  'subscription_trial_end_date', 'stripe_subscription_id', 'stripe_customer_id']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'subscription_trial_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'stripe_subscription_id': forms.TextInput(attrs={'class': 'form-control'}),
            'stripe_customer_id': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Apply consistent styling to all select fields
        self.fields['subscription_plan'].widget.attrs.update({'class': 'form-select'})
        self.fields['user'].widget.attrs.update({'class': 'form-select'})
        self.fields['status_ref'].widget.attrs.update({'class': 'form-select'})
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['status_ref'].queryset = SubscriptionStatus.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['status_ref'].queryset = SubscriptionStatus.objects.none()



class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'subscription', 'status', 'amount', 'due_date', 'stripe_invoice_id', 'pdf_url']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'stripe_invoice_id': forms.TextInput(attrs={'class': 'form-control'}),
            'pdf_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        # Apply consistent styling to all select fields
        self.fields['subscription'].widget.attrs.update({'class': 'form-select'})
        
        # Filter subscription queryset by tenant if available
        if self.tenant:
            self.fields['subscription'].queryset = Subscription.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['subscription'].queryset = Subscription.objects.none()


class CreditAdjustmentForm(forms.ModelForm):
    class Meta:
        model = CreditAdjustment
        fields = ['subscription', 'invoice', 'adjustment_type', 'adjustment_type_ref', 'amount', 'adjustment_description']
        widgets = {
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'adjustment_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Apply consistent styling to all select fields
        self.fields['subscription'].widget.attrs.update({'class': 'form-select'})
        self.fields['invoice'].widget.attrs.update({'class': 'form-select'})
        self.fields['adjustment_type_ref'].widget.attrs.update({'class': 'form-select'})
        
        # Filter querysets by tenant if available
        if self.tenant:
            self.fields['subscription'].queryset = Subscription.objects.filter(tenant_id=self.tenant.id)
            self.fields['invoice'].queryset = Invoice.objects.filter(tenant_id=self.tenant.id)
            self.fields['adjustment_type_ref'].queryset = AdjustmentType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['subscription'].queryset = Subscription.objects.none()
            self.fields['invoice'].queryset = Invoice.objects.none()
            self.fields['adjustment_type_ref'].queryset = AdjustmentType.objects.none()


class PaymentProviderConfigForm(forms.ModelForm):
    class Meta:
        model = PaymentProviderConfig
        fields = ['provider_config_name', 'name_ref', 'display_name', 'api_key', 'secret_key', 'webhook_secret', 'config_is_active']
        widgets = {
            'provider_config_name': forms.Select(attrs={'class': 'form-select'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'secret_key': forms.TextInput(attrs={'class': 'form-control'}),
            'webhook_secret': forms.TextInput(attrs={'class': 'form-control'}),
            'config_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Apply consistent styling to all select fields
        self.fields['name_ref'].widget.attrs.update({'class': 'form-select'})
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['name_ref'].queryset = PaymentProvider.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['name_ref'].queryset = PaymentProvider.objects.none()


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['user', 'type', 'type_ref', 'display_info', 'provider', 'provider_payment_method_id', 
                  'is_default', 'payment_method_is_active']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'display_info': forms.TextInput(attrs={'class': 'form-control'}),
            'provider_payment_method_id': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_method_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Apply consistent styling to all select fields
        self.fields['user'].widget.attrs.update({'class': 'form-select'})
        self.fields['type_ref'].widget.attrs.update({'class': 'form-select'})
        self.fields['provider'].widget.attrs.update({'class': 'form-select'})
        
        # Filter querysets by tenant if available
        if self.tenant:
            self.fields['user'].queryset = User.objects.filter(tenant_id=self.tenant.id)
            self.fields['type_ref'].queryset = PaymentType.objects.filter(tenant_id=self.tenant.id)
            self.fields['provider'].queryset = PaymentProviderConfig.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['user'].queryset = User.objects.none()
            self.fields['type_ref'].queryset = PaymentType.objects.none()
            self.fields['provider'].queryset = PaymentProviderConfig.objects.none()


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_method', 'status', 'stripe_payment_intent_id', 
                  'transaction_id', 'processed_at']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'stripe_payment_intent_id': forms.TextInput(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'processed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        # Apply consistent styling to all select fields
        self.fields['invoice'].widget.attrs.update({'class': 'form-select'})
        self.fields['payment_method'].widget.attrs.update({'class': 'form-select'})
        
        # Filter querysets by tenant if available
        if self.tenant:
            self.fields['invoice'].queryset = Invoice.objects.filter(tenant_id=self.tenant.id)
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['invoice'].queryset = Invoice.objects.none()
            self.fields['payment_method'].queryset = PaymentMethod.objects.none()


class PlanTierForm(forms.ModelForm):
    class Meta:
        model = PlanTier
        fields = ['tier_name', 'label', 'order', 'tier_is_active', 'is_system']
        widgets = {
            'tier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'tier_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SubscriptionStatusForm(forms.ModelForm):
    class Meta:
        model = SubscriptionStatus
        fields = ['status_name', 'label', 'order', 'status_is_active', 'is_system']
        widgets = {
            'status_name': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'status_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdjustmentTypeForm(forms.ModelForm):
    class Meta:
        model = AdjustmentType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']
        widgets = {
            'type_name': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'type_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaymentProviderForm(forms.ModelForm):
    class Meta:
        model = PaymentProvider
        fields = ['provider_name', 'label', 'order', 'provider_is_active', 'is_system']
        widgets = {
            'provider_name': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'provider_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaymentTypeForm(forms.ModelForm):
    class Meta:
        model = PaymentType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']
        widgets = {
            'type_name': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'type_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }