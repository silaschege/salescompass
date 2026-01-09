from django.urls import path
from django.views.generic import RedirectView
from . import webhooks, views

app_name = 'billing'

urlpatterns = [
    # Default billing page redirects to revenue overview
    path('', RedirectView.as_view(pattern_name='billing:revenue_overview', permanent=False), name='billing_home'),
    
    # Tenant billing portal
    path('portal/', views.BillingPortalView.as_view(), name='portal'),
    
    # Revenue Dashboard
    path('revenue/overview/', views.RevenueOverviewView.as_view(), name='revenue_overview'),
    path('revenue/mrr/', views.MRRAnalyticsView.as_view(), name='mrr_analytics'),
    path('revenue/arr/', views.ARRAnalyticsView.as_view(), name='arr_analytics'),
    path('revenue/churn/', views.ChurnRatesView.as_view(), name='churn_rates'),
    path('revenue/forecast/', views.RevenueForecastView.as_view(), name='revenue_forecast'),
    
    # Invoice Management
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:invoice_id>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:invoice_id>/edit/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:invoice_id>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/<int:invoice_id>/mark-paid/', views.InvoiceMarkPaidView.as_view(), name='invoice_mark_paid'),
    path('invoices/<int:invoice_id>/void/', views.InvoiceVoidView.as_view(), name='invoice_void'),
    path('invoices/paid/', views.PaidInvoicesView.as_view(), name='invoice_paid'),
    path('invoices/overdue/', views.OverdueInvoicesView.as_view(), name='invoice_overdue'),
    path('invoices/void/', views.VoidInvoicesView.as_view(), name='invoice_void_list'),
    path('invoices/reconciliation/', views.ReconciliationView.as_view(), name='reconciliation'),
    
    # Invoicing Engine
    path('invoicing/generation/', views.InvoiceGenerationView.as_view(), name='invoice_generation'),
    path('invoicing/dunning/', views.DunningManagementView.as_view(), name='dunning_management'),
    path('invoicing/failed-payments/', views.FailedPaymentsView.as_view(), name='failed_payments'),
    
    # Subscription Plans
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/create/', views.PlanCreateView.as_view(), name='plan_create'),
    path('plans/<int:plan_id>/', views.PlanDetailView.as_view(), name='plan_detail'),
    path('plans/<int:plan_id>/edit/', views.PlanUpdateView.as_view(), name='plan_update'),
    path('plans/<int:plan_id>/delete/', views.PlanDeleteView.as_view(), name='plan_delete'),
    path('plans/<int:plan_id>/pricing/', views.PricingConfigView.as_view(), name='pricing_config'),
    path('plans/<int:plan_id>/toggle-active/', views.PlanToggleActiveView.as_view(), name='plan_toggle_active'),
    path('plans/limits/', views.PlanLimitsView.as_view(), name='plan_limits'),
     
    # Plan Tiers 
    path('plan-tiers/', views.PlanTierListView.as_view(), name='plan_tier_list'),
    path('plan-tiers/create/', views.PlanTierCreateView.as_view(), name='plan_tier_create'),
    path('plan-tiers/<int:pk>/edit/', views.PlanTierUpdateView.as_view(), name='plan_tier_update'),
    path('plan-tiers/<int:pk>/delete/', views.PlanTierDeleteView.as_view(), name='plan_tier_delete'),
    
    # Subscription Statuses
    path('subscription-statuses/', views.SubscriptionStatusListView.as_view(), name='subscription_status_list'),
    path('subscription-statuses/create/', views.SubscriptionStatusCreateView.as_view(), name='subscription_status_create'),
    path('subscription-statuses/<int:pk>/edit/', views.SubscriptionStatusUpdateView.as_view(), name='subscription_status_update'),
    path('subscription-statuses/<int:pk>/delete/', views.SubscriptionStatusDeleteView.as_view(), name='subscription_status_delete'),
    
    # Adjustment Types
    path('adjustment-types/', views.AdjustmentTypeListView.as_view(), name='adjustment_type_list'),
    path('adjustment-types/create/', views.AdjustmentTypeCreateView.as_view(), name='adjustment_type_create'),
    path('adjustment-types/<int:pk>/edit/', views.AdjustmentTypeUpdateView.as_view(), name='adjustment_type_update'),
    path('adjustment-types/<int:pk>/delete/', views.AdjustmentTypeDeleteView.as_view(), name='adjustment_type_delete'),
    
    # Payment Providers
    path('payment-providers/', views.PaymentProviderListView.as_view(), name='payment_provider_list'),
    path('payment-providers/create/', views.PaymentProviderCreateView.as_view(), name='payment_provider_create'),
    path('payment-providers/<int:pk>/edit/', views.PaymentProviderUpdateView.as_view(), name='payment_provider_update'),
    path('payment-providers/<int:pk>/delete/', views.PaymentProviderDeleteView.as_view(), name='payment_provider_delete'),
    
    # Payment Types
    path('payment-types/', views.PaymentTypeListView.as_view(), name='payment_type_list'),
    path('payment-types/create/', views.PaymentTypeCreateView.as_view(), name='payment_type_create'),
    path('payment-types/<int:pk>/edit/', views.PaymentTypeUpdateView.as_view(), name='payment_type_update'),
    path('payment-types/<int:pk>/delete/', views.PaymentTypeDeleteView.as_view(), name='payment_type_delete'),
    
    # Payment Provider Configs
    path('payment-provider-configs/', views.PaymentProviderConfigListView.as_view(), name='payment_provider_config_list'),
    path('payment-provider-configs/create/', views.PaymentProviderConfigCreateView.as_view(), name='payment_provider_config_create'),
    path('payment-provider-configs/<int:pk>/edit/', views.PaymentProviderConfigUpdateView.as_view(), name='payment_provider_config_update'),
    path('payment-provider-configs/<int:pk>/delete/', views.PaymentProviderConfigDeleteView.as_view(), name='payment_provider_config_delete'),
    
    # Subscription Management
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription_list'),
    path('subscriptions/create/', views.SubscriptionCreateView.as_view(), name='subscription_create'),
    path('subscriptions/<int:subscription_id>/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscriptions/<int:subscription_id>/edit/', views.SubscriptionUpdateView.as_view(), name='subscription_update'),
    path('subscriptions/<int:subscription_id>/delete/', views.SubscriptionDeleteView.as_view(), name='subscription_delete'),
    path('subscriptions/<int:subscription_id>/cancel/', views.SubscriptionCancelView.as_view(), name='subscription_cancel'),
    path('subscriptions/<int:subscription_id>/reactivate/', views.SubscriptionReactivateView.as_view(), name='subscription_reactivate'),
    path('subscriptions/upgrade-downgrade/', views.UpgradeDowngradeView.as_view(), name='upgrade_downgrade'),
    path('subscriptions/proration/', views.ProrationCalculatorView.as_view(), name='proration_calculator'),
    path('subscriptions/lifecycle/', views.LifecycleEventsView.as_view(), name='lifecycle_events'),
    path('subscriptions/renewals/', views.RenewalTrackingView.as_view(), name='renewal_tracking'),
    path('subscriptions/cancellations/', views.CancellationManagementView.as_view(), name='cancellation_management'),
    
    # Credit Adjustments
    path('credit-adjustments/', views.CreditAdjustmentListView.as_view(), name='credit_adjustment_list'),
    path('credit-adjustments/create/', views.CreditAdjustmentCreateView.as_view(), name='credit_adjustment_create'),
    path('credit-adjustments/<int:pk>/edit/', views.CreditAdjustmentUpdateView.as_view(), name='credit_adjustment_update'),
    path('credit-adjustments/<int:pk>/delete/', views.CreditAdjustmentDeleteView.as_view(), name='credit_adjustment_delete'),
    
    # Tenant Billing
    path('tenant/search/', views.TenantBillingSearchView.as_view(), name='tenant_billing_search'),
    path('tenant/<str:tenant_id>/history/', views.BillingHistoryView.as_view(), name='billing_history'),
    path('tenant/credit-adjustment/', views.CreditAdjustmentManagementView.as_view(), name='credit_adjustment'),
    
    # Payment Management
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/edit/', views.PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
    
    # Payment Methods (Tenant/Customer)
    path('payment-methods/', views.PaymentMethodListView.as_view(), name='payment_method_list'),
    path('payment-methods/add/', views.PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('payment-methods/<int:method_id>/delete/', views.PaymentMethodDeleteView.as_view(), name='payment_method_delete'),
    
    # Payment Provider Management (Three-Tier Architecture)
    # Platform Level (Superadmin)
    path('settings/gateways/', views.PaymentGatewayListView.as_view(), name='payment_gateway_list'),
    path('settings/gateways/create/', views.PaymentGatewayCreateView.as_view(), name='payment_gateway_create'),
    path('settings/gateways/<int:provider_id>/', views.PaymentGatewayConfigView.as_view(), name='payment_gateway_config'),
    
    # Tenant Level (Tenant Admin)
    path('settings/payment-config/', views.TenantPaymentConfigView.as_view(), name='tenant_payment_config'),
    
    # Webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe_webhook'),

    
    # Plan feature and module access URLs
    path('plan-feature-access/', views.PlanFeatureAccessListView.as_view(), name='plan_feature_access_list'),
    path('plan-feature-access/create/', views.PlanFeatureAccessCreateView.as_view(), name='plan_feature_access_create'),
    path('plan-feature-access/<int:pk>/edit/', views.PlanFeatureAccessUpdateView.as_view(), name='plan_feature_access_update'),
    path('plan-feature-access/<int:pk>/delete/', views.PlanFeatureAccessDeleteView.as_view(), name='plan_feature_access_delete'),
    
    path('plan-module-access/', views.PlanModuleAccessListView.as_view(), name='plan_module_access_list'),
    path('plan-module-access/create/', views.PlanModuleAccessCreateView.as_view(), name='plan_module_access_create'),
    path('plan-module-access/<int:pk>/edit/', views.PlanModuleAccessUpdateView.as_view(), name='plan_module_access_update'),
    path('plan-module-access/<int:pk>/delete/', views.PlanModuleAccessDeleteView.as_view(), name='plan_module_access_delete'),
    
    path('upgrade-required/', views.UpgradeRequiredView.as_view(), name='upgrade_required'),
]
