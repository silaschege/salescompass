from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Plan, Subscription, Invoice, CreditAdjustment, PaymentProviderConfig, PaymentMethod, Payment, PlanTier, SubscriptionStatus, AdjustmentType, PaymentProvider, PaymentType
from .forms import PlanForm, SubscriptionForm, InvoiceForm, CreditAdjustmentForm, PaymentProviderConfigForm, PaymentMethodForm, PaymentForm, PlanTierForm, SubscriptionStatusForm, AdjustmentTypeForm, PaymentProviderForm, PaymentTypeForm
from tenants.models import Tenant as TenantModel


class PlanTierListView(ListView):
    model = PlanTier
    template_name = 'billing/plan_tier_list.html'
    context_object_name = 'plan_tiers'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class PlanTierCreateView(CreateView):
    model = PlanTier
    form_class = PlanTierForm
    template_name = 'billing/plan_tier_form.html'
    success_url = reverse_lazy('billing:plan_tier_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Plan tier created successfully.')
        return super().form_valid(form)


class PlanTierUpdateView(UpdateView):
    model = PlanTier
    form_class = PlanTierForm
    template_name = 'billing/plan_tier_form.html'
    success_url = reverse_lazy('billing:plan_tier_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Plan tier updated successfully.')
        return super().form_valid(form)


class PlanTierDeleteView(DeleteView):
    model = PlanTier
    template_name = 'billing/plan_tier_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_tier_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Plan tier deleted successfully.')
        return super().delete(request, *args, **kwargs)


class SubscriptionStatusListView(ListView):
    model = SubscriptionStatus
    template_name = 'billing/subscription_status_list.html'
    context_object_name = 'subscription_statuses'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class SubscriptionStatusCreateView(CreateView):
    model = SubscriptionStatus
    form_class = SubscriptionStatusForm
    template_name = 'billing/subscription_status_form.html'
    success_url = reverse_lazy('billing:subscription_status_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Subscription status created successfully.')
        return super().form_valid(form)


class SubscriptionStatusUpdateView(UpdateView):
    model = SubscriptionStatus
    form_class = SubscriptionStatusForm
    template_name = 'billing/subscription_status_form.html'
    success_url = reverse_lazy('billing:subscription_status_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Subscription status updated successfully.')
        return super().form_valid(form)


class SubscriptionStatusDeleteView(DeleteView):
    model = SubscriptionStatus
    template_name = 'billing/subscription_status_confirm_delete.html'
    success_url = reverse_lazy('billing:subscription_status_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Subscription status deleted successfully.')
        return super().delete(request, *args, **kwargs)


class AdjustmentTypeListView(ListView):
    model = AdjustmentType
    template_name = 'billing/adjustment_type_list.html'
    context_object_name = 'adjustment_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class AdjustmentTypeCreateView(CreateView):
    model = AdjustmentType
    form_class = AdjustmentTypeForm
    template_name = 'billing/adjustment_type_form.html'
    success_url = reverse_lazy('billing:adjustment_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Adjustment type created successfully.')
        return super().form_valid(form)


class AdjustmentTypeUpdateView(UpdateView):
    model = AdjustmentType
    form_class = AdjustmentTypeForm
    template_name = 'billing/adjustment_type_form.html'
    success_url = reverse_lazy('billing:adjustment_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Adjustment type updated successfully.')
        return super().form_valid(form)


class AdjustmentTypeDeleteView(DeleteView):
    model = AdjustmentType
    template_name = 'billing/adjustment_type_confirm_delete.html'
    success_url = reverse_lazy('billing:adjustment_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Adjustment type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentProviderListView(ListView):
    model = PaymentProvider
    template_name = 'billing/payment_provider_list.html'
    context_object_name = 'payment_providers'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class PaymentProviderCreateView(CreateView):
    model = PaymentProvider
    form_class = PaymentProviderForm
    template_name = 'billing/payment_provider_form.html'
    success_url = reverse_lazy('billing:payment_provider_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment provider created successfully.')
        return super().form_valid(form)


class PaymentProviderUpdateView(UpdateView):
    model = PaymentProvider
    form_class = PaymentProviderForm
    template_name = 'billing/payment_provider_form.html'
    success_url = reverse_lazy('billing:payment_provider_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment provider updated successfully.')
        return super().form_valid(form)


class PaymentProviderDeleteView(DeleteView):
    model = PaymentProvider
    template_name = 'billing/payment_provider_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_provider_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment provider deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentTypeListView(ListView):
    model = PaymentType
    template_name = 'billing/payment_type_list.html'
    context_object_name = 'payment_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class PaymentTypeCreateView(CreateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = 'billing/payment_type_form.html'
    success_url = reverse_lazy('billing:payment_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment type created successfully.')
        return super().form_valid(form)


class PaymentTypeUpdateView(UpdateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = 'billing/payment_type_form.html'
    success_url = reverse_lazy('billing:payment_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment type updated successfully.')
        return super().form_valid(form)


class PaymentTypeDeleteView(DeleteView):
    model = PaymentType
    template_name = 'billing/payment_type_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PlanListView(ListView):
    model = Plan
    template_name = 'billing/plan_list.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('tier_ref')


class PlanCreateView(CreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_form.html'
    success_url = reverse_lazy('billing:plan_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Plan created successfully.')
        return super().form_valid(form)


class PlanUpdateView(UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_form.html'
    success_url = reverse_lazy('billing:plan_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Plan updated successfully.')
        return super().form_valid(form)


class PlanDeleteView(DeleteView):
    model = Plan
    template_name = 'billing/plan_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Plan deleted successfully.')
        return super().delete(request, *args, **kwargs)


class SubscriptionListView(ListView):
    model = Subscription
    template_name = 'billing/subscription_list.html'
    context_object_name = 'subscriptions'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('subscription_plan', 'user', 'status_ref')


class SubscriptionCreateView(CreateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'billing/subscription_form.html'
    success_url = reverse_lazy('billing:subscription_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Subscription created successfully.')
        return super().form_valid(form)


class SubscriptionUpdateView(UpdateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'billing/subscription_form.html'
    success_url = reverse_lazy('billing:subscription_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Subscription updated successfully.')
        return super().form_valid(form)


class SubscriptionDeleteView(DeleteView):
    model = Subscription
    template_name = 'billing/subscription_confirm_delete.html'
    success_url = reverse_lazy('billing:subscription_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Subscription deleted successfully.')
        return super().delete(request, *args, **kwargs)


class InvoiceListView(ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('subscription')


class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_form.html'
    success_url = reverse_lazy('billing:invoice_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Invoice created successfully.')
        return super().form_valid(form)


class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_form.html'
    success_url = reverse_lazy('billing:invoice_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Invoice updated successfully.')
        return super().form_valid(form)


class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'billing/invoice_confirm_delete.html'
    success_url = reverse_lazy('billing:invoice_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Invoice deleted successfully.')
        return super().delete(request, *args, **kwargs)


class CreditAdjustmentListView(ListView):
    model = CreditAdjustment
    template_name = 'billing/credit_adjustment_list.html'
    context_object_name = 'credit_adjustments'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('subscription', 'invoice', 'adjustment_type_ref')


class CreditAdjustmentCreateView(CreateView):
    model = CreditAdjustment
    form_class = CreditAdjustmentForm
    template_name = 'billing/credit_adjustment_form.html'
    success_url = reverse_lazy('billing:credit_adjustment_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Credit adjustment created successfully.')
        return super().form_valid(form)


class CreditAdjustmentUpdateView(UpdateView):
    model = CreditAdjustment
    form_class = CreditAdjustmentForm
    template_name = 'billing/credit_adjustment_form.html'
    success_url = reverse_lazy('billing:credit_adjustment_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Credit adjustment updated successfully.')
        return super().form_valid(form)


class CreditAdjustmentDeleteView(DeleteView):
    model = CreditAdjustment
    template_name = 'billing/credit_adjustment_confirm_delete.html'
    success_url = reverse_lazy('billing:credit_adjustment_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Credit adjustment deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentProviderConfigListView(ListView):
    model = PaymentProviderConfig
    template_name = 'billing/payment_provider_config_list.html'
    context_object_name = 'payment_configs'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('name_ref')


class PaymentProviderConfigCreateView(CreateView):
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_provider_config_form.html'
    success_url = reverse_lazy('billing:payment_provider_config_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment provider configuration created successfully.')
        return super().form_valid(form)


class PaymentProviderConfigUpdateView(UpdateView):
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_provider_config_form.html'
    success_url = reverse_lazy('billing:payment_provider_config_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment provider configuration updated successfully.')
        return super().form_valid(form)


class PaymentProviderConfigDeleteView(DeleteView):
    model = PaymentProviderConfig
    template_name = 'billing/payment_provider_config_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_provider_config_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment provider configuration deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentMethodListView(ListView):
    model = PaymentMethod
    template_name = 'billing/payment_method_list.html'
    context_object_name = 'payment_methods'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('user', 'type_ref', 'provider')


class PaymentMethodCreateView(CreateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'billing/payment_method_form.html'
    success_url = reverse_lazy('billing:payment_method_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment method created successfully.')
        return super().form_valid(form)


class PaymentMethodUpdateView(UpdateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'billing/payment_method_form.html'
    success_url = reverse_lazy('billing:payment_method_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment method updated successfully.')
        return super().form_valid(form)


class PaymentMethodDeleteView(DeleteView):
    model = PaymentMethod
    template_name = 'billing/payment_method_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_method_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment method deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentListView(ListView):
    model = Payment
    template_name = 'billing/payment_list.html'
    context_object_name = 'payments'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('invoice', 'payment_method')


class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'billing/payment_form.html'
    success_url = reverse_lazy('billing:payment_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment created successfully.')
        return super().form_valid(form)


class PaymentUpdateView(UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'billing/payment_form.html'
    success_url = reverse_lazy('billing:payment_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment updated successfully.')
        return super().form_valid(form)


class PaymentDeleteView(DeleteView):
    model = Payment
    template_name = 'billing/payment_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def get_billing_dynamic_choices(request, model_name):
    """
    API endpoint to fetch dynamic choices for billing models
    """
    tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
    
    if not tenant_id:
        return JsonResponse({'error': 'No tenant associated with user'}, status=400)
    
    # Map model names to actual models
    model_map = {
        'plantier': PlanTier,
        'subscriptionstatus': SubscriptionStatus,
        'adjustmenttype': AdjustmentType,
        'paymentprovider': PaymentProvider,
        'paymenttype': PaymentType,
    }
    
    model_class = model_map.get(model_name.lower())
    
    if not model_class:
        return JsonResponse({'error': 'Invalid choice model'}, status=400)
    
    try:
        choices = model_class.objects.filter(tenant_id=tenant_id).values('id', 'name', 'label')
        return JsonResponse(list(choices), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# === Additional Views Referenced in urls.py ===

class BillingPortalView(LoginRequiredMixin, TemplateView):
    """Tenant billing portal landing page."""
    template_name = 'billing/portal.html'


# Revenue Dashboard Views
class RevenueOverviewView(LoginRequiredMixin, TemplateView):
    """Revenue overview dashboard."""
    template_name = 'billing/revenue_overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = Subscription.objects.filter(subscription_is_active=True)[:10]
        return context


class MRRAnalyticsView(LoginRequiredMixin, TemplateView):
    """Monthly Recurring Revenue analytics."""
    template_name = 'billing/mrr_analytics.html'


class ARRAnalyticsView(LoginRequiredMixin, TemplateView):
    """Annual Recurring Revenue analytics."""
    template_name = 'billing/arr_analytics.html'


class ChurnRatesView(LoginRequiredMixin, TemplateView):
    """Churn rates analytics."""
    template_name = 'billing/churn_rates.html'


class RevenueForecastView(LoginRequiredMixin, TemplateView):
    """Revenue forecast view."""
    template_name = 'billing/revenue_forecast.html'


# Invoice Management Views
class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """Invoice detail view."""
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    pk_url_kwarg = 'invoice_id'


class InvoiceMarkPaidView(LoginRequiredMixin, View):
    """Mark invoice as paid."""
    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        invoice.status = 'paid'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} marked as paid.')
        return redirect('billing:invoice_list')


class InvoiceVoidView(LoginRequiredMixin, View):
    """Void an invoice."""
    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        invoice.status = 'void'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} voided.')
        return redirect('billing:invoice_list')


class PaidInvoicesView(LoginRequiredMixin, ListView):
    """List paid invoices."""
    model = Invoice
    template_name = 'billing/invoice_paid_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='paid')


class OverdueInvoicesView(LoginRequiredMixin, ListView):
    """List overdue invoices."""
    model = Invoice
    template_name = 'billing/invoice_overdue_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='overdue')


class VoidInvoicesView(LoginRequiredMixin, ListView):
    """List void invoices."""
    model = Invoice
    template_name = 'billing/invoice_void_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='void')


class ReconciliationView(LoginRequiredMixin, TemplateView):
    """Invoice reconciliation view."""
    template_name = 'billing/reconciliation.html'


# Invoicing Engine Views
class InvoiceGenerationView(LoginRequiredMixin, TemplateView):
    """Invoice generation view."""
    template_name = 'billing/invoice_generation.html'


class DunningManagementView(LoginRequiredMixin, TemplateView):
    """Dunning management view."""
    template_name = 'billing/dunning_management.html'


class FailedPaymentsView(LoginRequiredMixin, ListView):
    """View failed payments."""
    model = Payment
    template_name = 'billing/failed_payments.html'
    context_object_name = 'payments'
    
    def get_queryset(self):
        return Payment.objects.filter(status='failed')


# Plan Views
class PlanDetailView(LoginRequiredMixin, DetailView):
    """Plan detail view."""
    model = Plan
    template_name = 'billing/plan_detail.html'
    pk_url_kwarg = 'plan_id'


class PlanEditView(LoginRequiredMixin, UpdateView):
    """Edit plan."""
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_edit.html'
    pk_url_kwarg = 'plan_id'
    success_url = reverse_lazy('billing:plan_list')


class PricingConfigView(LoginRequiredMixin, TemplateView):
    """Plan pricing configuration."""
    template_name = 'billing/pricing_config.html'


class PlanToggleActiveView(LoginRequiredMixin, View):
    """Toggle plan active status."""
    def post(self, request, plan_id):
        plan = get_object_or_404(Plan, pk=plan_id)
        plan.plan_is_active = not plan.plan_is_active
        plan.save()
        status = 'activated' if plan.plan_is_active else 'deactivated'
        messages.success(request, f'Plan {plan.plan_name} {status}.')
        return redirect('billing:plan_list')


class PlanLimitsView(LoginRequiredMixin, TemplateView):
    """Plan limits configuration."""
    template_name = 'billing/plan_limits.html'


# Subscription Views
class SubscriptionDetailView(LoginRequiredMixin, DetailView):
    """Subscription detail view."""
    model = Subscription
    template_name = 'billing/subscription_detail.html'
    pk_url_kwarg = 'subscription_id'


class SubscriptionCancelView(LoginRequiredMixin, View):
    """Cancel subscription."""
    def get(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, pk=subscription_id)
        return render(request, 'billing/subscription_cancel_confirm.html', {'subscription': subscription})
    
    def post(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, pk=subscription_id)
        subscription.status = 'canceled'
        subscription.subscription_is_active = False
        subscription.save()
        messages.success(request, 'Subscription cancelled.')
        return redirect('billing:subscription_list')


class SubscriptionReactivateView(LoginRequiredMixin, View):
    """Reactivate subscription."""
    def post(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, pk=subscription_id)
        subscription.status = 'active'
        subscription.subscription_is_active = True
        subscription.save()
        messages.success(request, 'Subscription reactivated.')
        return redirect('billing:subscription_list')


class UpgradeDowngradeView(LoginRequiredMixin, TemplateView):
    """Upgrade/downgrade subscription view."""
    template_name = 'billing/upgrade_downgrade.html'


class ProrationCalculatorView(LoginRequiredMixin, TemplateView):
    """Proration calculator view."""
    template_name = 'billing/proration_calculator.html'


class LifecycleEventsView(LoginRequiredMixin, TemplateView):
    """Subscription lifecycle events."""
    template_name = 'billing/lifecycle_events.html'


class RenewalTrackingView(LoginRequiredMixin, TemplateView):
    """Subscription renewal tracking."""
    template_name = 'billing/renewal_tracking.html'


class CancellationManagementView(LoginRequiredMixin, TemplateView):
    """Cancellation management view."""
    template_name = 'billing/cancellation_management.html'


# Tenant Billing Views
class TenantBillingSearchView(LoginRequiredMixin, TemplateView):
    """Search tenant billing."""
    template_name = 'billing/tenant_billing_search.html'


class BillingHistoryView(LoginRequiredMixin, TemplateView):
    """Tenant billing history."""
    template_name = 'billing/billing_history.html'


class CreditAdjustmentManagementView(LoginRequiredMixin, TemplateView):
    """Credit adjustment management."""
    template_name = 'billing/credit_adjustment_management.html'


# Payment Gateway Views
class PaymentGatewayListView(LoginRequiredMixin, ListView):
    """List payment gateways."""
    model = PaymentProviderConfig
    template_name = 'billing/payment_gateway_list.html'
    context_object_name = 'gateways'


class PaymentGatewayCreateView(LoginRequiredMixin, CreateView):
    """Create payment gateway."""
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_gateway_form.html'
    success_url = reverse_lazy('billing:payment_gateway_list')


class PaymentGatewayConfigView(LoginRequiredMixin, UpdateView):
    """Configure payment gateway."""
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_gateway_config.html'
    pk_url_kwarg = 'provider_id'
    success_url = reverse_lazy('billing:payment_gateway_list')


class TenantPaymentConfigView(LoginRequiredMixin, TemplateView):
    """Tenant payment configuration."""
    template_name = 'billing/tenant_payment_config.html'
