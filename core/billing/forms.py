from django import forms
from .models import Plan, Subscription, Invoice, CreditAdjustment, PaymentProviderConfig, PaymentMethod, Payment, PlanTier, SubscriptionStatus, AdjustmentType, PaymentProvider, PaymentType
from tenants.models import Tenant as TenantModel


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['plan_name', 'tier', 'tier_ref', 'price_monthly', 'price_annually', 'features', 'plan_is_active']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['tier_ref'].queryset = PlanTier.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['tier_ref'].queryset = PlanTier.objects.none()


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        # Note: start_date is auto_now_add, so it's non-editable
        fields = ['subscription_plan', 'user', 'status', 'status_ref', 'end_date', 
                  'subscription_trial_end_date', 'stripe_subscription_id', 'stripe_customer_id']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['status_ref'].queryset = SubscriptionStatus.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['status_ref'].queryset = SubscriptionStatus.objects.none()


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'subscription', 'status', 'amount', 'due_date', 'stripe_invoice_id', 'pdf_url']


class CreditAdjustmentForm(forms.ModelForm):
    class Meta:
        model = CreditAdjustment
        fields = ['subscription', 'invoice', 'adjustment_type', 'adjustment_type_ref', 'amount', 'adjustment_description']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['adjustment_type_ref'].queryset = AdjustmentType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['adjustment_type_ref'].queryset = AdjustmentType.objects.none()


class PaymentProviderConfigForm(forms.ModelForm):
    class Meta:
        model = PaymentProviderConfig
        fields = ['provider_config_name', 'name_ref', 'display_name', 'api_key', 'secret_key', 'webhook_secret', 'config_is_active']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
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
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['type_ref'].queryset = PaymentType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['type_ref'].queryset = PaymentType.objects.none()


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_method', 'status', 'stripe_payment_intent_id', 
                  'transaction_id', 'processed_at']


class PlanTierForm(forms.ModelForm):
    class Meta:
        model = PlanTier
        fields = ['tier_name', 'label', 'order', 'tier_is_active', 'is_system']


class SubscriptionStatusForm(forms.ModelForm):
    class Meta:
        model = SubscriptionStatus
        fields = ['status_name', 'label', 'order', 'status_is_active', 'is_system']


class AdjustmentTypeForm(forms.ModelForm):
    class Meta:
        model = AdjustmentType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']


class PaymentProviderForm(forms.ModelForm):
    class Meta:
        model = PaymentProvider
        fields = ['provider_name', 'label', 'order', 'provider_is_active', 'is_system']


class PaymentTypeForm(forms.ModelForm):
    class Meta:
        model = PaymentType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']

