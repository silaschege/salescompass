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
    path('plans/<int:plan_id>/edit/', views.PlanEditView.as_view(), name='plan_edit'),
    path('plans/<int:plan_id>/pricing/', views.PricingConfigView.as_view(), name='pricing_config'),
    path('plans/<int:plan_id>/toggle-active/', views.PlanToggleActiveView.as_view(), name='plan_toggle_active'),
    path('plans/limits/', views.PlanLimitsView.as_view(), name='plan_limits'),
    
    # Subscription Management
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscription_list'),
    path('subscriptions/<int:subscription_id>/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscriptions/<int:subscription_id>/cancel/', views.SubscriptionCancelView.as_view(), name='subscription_cancel'),
    path('subscriptions/<int:subscription_id>/reactivate/', views.SubscriptionReactivateView.as_view(), name='subscription_reactivate'),
    path('subscriptions/upgrade-downgrade/', views.UpgradeDowngradeView.as_view(), name='upgrade_downgrade'),
    path('subscriptions/proration/', views.ProrationCalculatorView.as_view(), name='proration_calculator'),
    path('subscriptions/lifecycle/', views.LifecycleEventsView.as_view(), name='lifecycle_events'),
    path('subscriptions/renewals/', views.RenewalTrackingView.as_view(), name='renewal_tracking'),
    path('subscriptions/cancellations/', views.CancellationManagementView.as_view(), name='cancellation_management'),
    
    # Tenant Billing
    path('tenant/search/', views.TenantBillingSearchView.as_view(), name='tenant_billing_search'),
    path('tenant/<str:tenant_id>/history/', views.BillingHistoryView.as_view(), name='billing_history'),
    path('tenant/credit-adjustment/', views.CreditAdjustmentManagementView.as_view(), name='credit_adjustment'),
    
    # Payment Provider Management (Three-Tier Architecture)
    # Platform Level (Superadmin)
    path('settings/gateways/', views.PaymentGatewayListView.as_view(), name='payment_gateway_list'),
    path('settings/gateways/create/', views.PaymentGatewayCreateView.as_view(), name='payment_gateway_create'),
    path('settings/gateways/<int:provider_id>/', views.PaymentGatewayConfigView.as_view(), name='payment_gateway_config'),
    
    # Tenant Level (Tenant Admin)
    path('settings/payment-config/', views.TenantPaymentConfigView.as_view(), name='tenant_payment_config'),
    
    # Payment Methods (Tenant/Customer)
    path('payment-methods/', views.PaymentMethodListView.as_view(), name='payment_method_list'),
    path('payment-methods/add/', views.PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('payment-methods/<int:method_id>/delete/', views.PaymentMethodDeleteView.as_view(), name='payment_method_delete'),
    
    # Webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe_webhook'),
]

