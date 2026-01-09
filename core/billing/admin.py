from django.contrib import admin
from .models import Plan, Subscription, Invoice, CreditAdjustment, PaymentProviderConfig, PaymentMethod, Payment, PlanTier, SubscriptionStatus, AdjustmentType, PaymentProvider, PaymentType, PlanModuleAccess, PlanFeatureAccess


class PlanModuleAccessInline(admin.TabularInline):
    model = PlanModuleAccess
    extra = 0

class PlanFeatureAccessInline(admin.TabularInline):
    model = PlanFeatureAccess
    extra = 0

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'max_users', 'storage_limit', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    inlines = [PlanModuleAccessInline, PlanFeatureAccessInline]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_plan', 'status', 'start_date', 'end_date', 'subscription_is_active']
    list_filter = ['status', 'subscription_is_active', 'start_date']
    search_fields = ['user__email', 'stripe_subscription_id', 'stripe_customer_id']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'subscription', 'status', 'amount', 'due_date', 'issued_date']
    list_filter = ['status', 'issued_date']
    search_fields = ['invoice_number', 'stripe_invoice_id']


@admin.register(CreditAdjustment)
class CreditAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'adjustment_type', 'amount', 'applied_date', 'adjustment_is_active']
    list_filter = ['adjustment_type', 'applied_date']
    search_fields = ['adjustment_description']


@admin.register(PaymentProviderConfig)
class PaymentProviderConfigAdmin(admin.ModelAdmin):
    list_display = ['provider_config_name', 'display_name', 'config_is_active', 'config_created_at']
    list_filter = ['provider_config_name', 'config_is_active']
    search_fields = ['display_name', 'provider_config_name']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'display_info', 'payment_method_is_active']
    list_filter = ['type', 'is_default', 'payment_method_is_active']
    search_fields = ['user__email', 'display_info']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'status', 'processed_at', 'payment_is_active']
    list_filter = ['status', 'processed_at']
    search_fields = ['transaction_id', 'stripe_payment_intent_id']


@admin.register(PlanTier)
class PlanTierAdmin(admin.ModelAdmin):
    list_display = ['tier_name', 'label', 'order', 'tier_is_active', 'is_system']
    list_filter = ['tier_is_active', 'is_system']
    search_fields = ['tier_name', 'label']


@admin.register(SubscriptionStatus)
class SubscriptionStatusAdmin(admin.ModelAdmin):
    list_display = ['status_name', 'label', 'order', 'status_is_active', 'is_system']
    list_filter = ['status_is_active', 'is_system']
    search_fields = ['status_name', 'label']


@admin.register(AdjustmentType)
class AdjustmentTypeAdmin(admin.ModelAdmin):
    list_display = ['type_name', 'label', 'order', 'type_is_active', 'is_system']
    list_filter = ['type_is_active', 'is_system']
    search_fields = ['type_name', 'label']


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = ['provider_name', 'label', 'order', 'provider_is_active', 'is_system']
    list_filter = ['provider_is_active', 'is_system']
    search_fields = ['provider_name', 'label']


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ['type_name', 'label', 'order', 'type_is_active', 'is_system']
    list_filter = ['type_is_active', 'is_system']
    search_fields = ['type_name', 'label']