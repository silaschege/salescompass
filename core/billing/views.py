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
import logging
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta

from .models import PlanFeatureAccess, PlanModuleAccess
# Import engagement tracking
from engagement.utils import log_engagement_event

logger = logging.getLogger(__name__)

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from access_control.views import SecureViewMixin
from access_control.utils import access_required

class BillingDashboardView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/dashboard.html'
    required_access = 'billing.dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add access control utilities to context
        context['can_manage_plans'] = self.can_access('billing.plans', 'manage')
        context['can_manage_subscriptions'] = self.can_access('billing.subscriptions', 'manage')
        context['can_manage_payments'] = self.can_access('billing.payments', 'manage')
        
        return context

# For function-based views
@access_required('billing.reports.view')
def billing_reports_view(request):
    # View logic here
    return render(request, 'billing/reports.html')
class UpgradeRequiredView(LoginRequiredMixin, TemplateView):
    template_name = 'billing/upgrade_required.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_name'] = self.request.GET.get('module', 'Premium Feature')
        return context

class PlanTierListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = PlanTier
    template_name = 'billing/plan_tier_list.html'
    context_object_name = 'plan_tiers'
    required_access = 'billing.admin.config'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class PlanTierCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = PlanTier
    form_class = PlanTierForm
    template_name = 'billing/plan_tier_form.html'
    success_url = reverse_lazy('billing:plan_tier_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Plan tier created successfully.')
        return super().form_valid(form)


class PlanTierUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PlanTier
    form_class = PlanTierForm
    template_name = 'billing/plan_tier_form.html'
    success_url = reverse_lazy('billing:plan_tier_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        messages.success(self.request, 'Plan tier updated successfully.')
        return super().form_valid(form)


class PlanTierDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = PlanTier
    template_name = 'billing/plan_tier_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_tier_list')
    required_access = 'billing.admin.config'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Plan tier deleted successfully.')
        return super().delete(request, *args, **kwargs)


class SubscriptionStatusListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = SubscriptionStatus
    template_name = 'billing/subscription_status_list.html'
    context_object_name = 'subscription_statuses'
    required_access = 'billing.admin.config'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class SubscriptionStatusCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = SubscriptionStatus
    form_class = SubscriptionStatusForm
    template_name = 'billing/subscription_status_form.html'
    success_url = reverse_lazy('billing:subscription_status_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Subscription status created successfully.')
        return super().form_valid(form)


class SubscriptionStatusUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = SubscriptionStatus
    form_class = SubscriptionStatusForm
    template_name = 'billing/subscription_status_form.html'
    success_url = reverse_lazy('billing:subscription_status_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        messages.success(self.request, 'Subscription status updated successfully.')
        return super().form_valid(form)


class SubscriptionStatusDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = SubscriptionStatus
    template_name = 'billing/subscription_status_confirm_delete.html'
    success_url = reverse_lazy('billing:subscription_status_list')
    required_access = 'billing.admin.config'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Subscription status deleted successfully.')
        return super().delete(request, *args, **kwargs)


class AdjustmentTypeListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = AdjustmentType
    template_name = 'billing/adjustment_type_list.html'
    context_object_name = 'adjustment_types'
    required_access = 'billing.admin.config'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class AdjustmentTypeCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = AdjustmentType
    form_class = AdjustmentTypeForm
    template_name = 'billing/adjustment_type_form.html'
    success_url = reverse_lazy('billing:adjustment_type_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Adjustment type created successfully.')
        return super().form_valid(form)


class AdjustmentTypeUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = AdjustmentType
    form_class = AdjustmentTypeForm
    template_name = 'billing/adjustment_type_form.html'
    success_url = reverse_lazy('billing:adjustment_type_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        messages.success(self.request, 'Adjustment type updated successfully.')
        return super().form_valid(form)


class AdjustmentTypeDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = AdjustmentType
    template_name = 'billing/adjustment_type_confirm_delete.html'
    success_url = reverse_lazy('billing:adjustment_type_list')
    required_access = 'billing.admin.config'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Adjustment type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentProviderListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = PaymentProvider
    template_name = 'billing/payment_provider_list.html'
    context_object_name = 'payment_providers'
    required_access = 'billing.admin.config'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class PaymentProviderCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = PaymentProvider
    form_class = PaymentProviderForm
    template_name = 'billing/payment_provider_form.html'
    success_url = reverse_lazy('billing:payment_provider_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment provider created successfully.')
        return super().form_valid(form)


class PaymentProviderUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PaymentProvider
    form_class = PaymentProviderForm
    template_name = 'billing/payment_provider_form.html'
    success_url = reverse_lazy('billing:payment_provider_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment provider updated successfully.')
        return super().form_valid(form)


class PaymentProviderDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = PaymentProvider
    template_name = 'billing/payment_provider_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_provider_list')
    required_access = 'billing.admin.config'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment provider deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentTypeListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = PaymentType
    template_name = 'billing/payment_type_list.html'
    context_object_name = 'payment_types'
    required_access = 'billing.admin.config'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class PaymentTypeCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = 'billing/payment_type_form.html'
    success_url = reverse_lazy('billing:payment_type_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment type created successfully.')
        return super().form_valid(form)


class PaymentTypeUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = 'billing/payment_type_form.html'
    success_url = reverse_lazy('billing:payment_type_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment type updated successfully.')
        return super().form_valid(form)


class PaymentTypeDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = PaymentType
    template_name = 'billing/payment_type_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_type_list')
    required_access = 'billing.admin.config'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment type deleted successfully.')
        return super().delete(request, *args, **kwargs)




class PlanListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = Plan
    template_name = 'billing/plan_list.html'
    context_object_name = 'plans'
    required_access = 'billing.admin.plans'
    
    def get_queryset(self):
        return Plan.objects.filter(is_active=True)



class PlanCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_form.html'
    success_url = reverse_lazy('billing:plan_list')
    required_access = 'billing.admin.plans'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Plan created successfully.')
        return super().form_valid(form)



class PlanUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_form.html'
    success_url = reverse_lazy('billing:plan_list')
    required_access = 'billing.admin.plans'
    pk_url_kwarg = 'plan_id'  # Added this to match the URL parameter name
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Plan updated successfully.')
        return super().form_valid(form)



class PlanDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = Plan
    template_name = 'billing/plan_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_list')
    required_access = 'billing.admin.plans'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Plan deleted successfully.')
        return super().delete(request, *args, **kwargs)




class SubscriptionListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = Subscription
    template_name = 'billing/subscription_list.html'
    context_object_name = 'subscriptions'
    paginate_by = 20  # Optional: add pagination
    required_access = 'billing.admin.subscriptions'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # For superusers, show all subscriptions; for regular users, filter by their tenant
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'tenant_id'):
                queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        
        # Handle search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                user__email__icontains=search_query
            )
        
        # Handle status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Prefetch related objects for better performance
        queryset = queryset.select_related('subscription_plan', 'user', 'status_ref')
        
        return queryset.order_by('-subscription_created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        # Define status choices for the template
        context['status_choices'] = [
            ('active', 'Active'),
            ('trialing', 'Trialing'),
            ('canceled', 'Canceled'),
            ('past_due', 'Past Due'),
            ('incomplete', 'Incomplete'),
        ]
        return context




class SubscriptionCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'billing/subscription_form.html'
    success_url = reverse_lazy('billing:subscription_list')
    required_access = 'billing.admin.subscriptions'
     
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        # For superusers or staff, set tenant_id from the selected user
        if self.request.user.is_superuser or self.request.user.is_staff:
            selected_user = form.cleaned_data.get('user')
            if selected_user and hasattr(selected_user, 'tenant_id'):
                form.instance.tenant_id = selected_user.tenant_id
        else:
            # For regular users, set tenant_id to their own tenant
            if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
                form.instance.tenant_id = self.request.user.tenant_id
            
        response = super().form_valid(form)

        # Log engagement event for subscription created
        try:
            log_engagement_event(
                tenant_id=form.instance.tenant_id,
                event_type='subscription_created',
                description=f"Subscription created: {self.object.subscription_plan} ({self.object.user})",
                title="Subscription Created",
                metadata={
                    'subscription_id': self.object.id,
                    'plan': str(self.object.subscription_plan),
                    'user': str(self.object.user),
                    'amount': float(self.object.subscription_plan.price) if self.object.subscription_plan else 0
                },
                engagement_score=5,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")

        messages.success(self.request, 'Subscription created successfully.')
        return response




class SubscriptionUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'billing/subscription_form.html'
    success_url = reverse_lazy('billing:subscription_list')
    required_access = 'billing.admin.subscriptions'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        # For superusers or staff, ensure tenant_id is set correctly if user changes
        if self.request.user.is_superuser or self.request.user.is_staff:
            selected_user = form.cleaned_data.get('user')
            if selected_user and hasattr(selected_user, 'tenant_id'):
                form.instance.tenant_id = selected_user.tenant_id
        
        # Log engagement event for subscription updated
        try:
            log_engagement_event(
                tenant_id=form.instance.tenant_id,
                event_type='subscription_updated',
                description=f"Subscription updated: {self.object.subscription_plan} ({self.object.user})",
                title="Subscription Updated",
                metadata={
                    'subscription_id': self.object.id,
                    'plan': str(self.object.subscription_plan),
                    'user': str(self.object.user),
                    'status': self.object.status
                },
                engagement_score=2,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        messages.success(self.request, 'Subscription updated successfully.')
        return super().form_valid(form)


class SubscriptionDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = Subscription
    template_name = 'billing/subscription_confirm_delete.html'
    success_url = reverse_lazy('billing:subscription_list')
    required_access = 'billing.admin.subscriptions'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Subscription deleted successfully.')
        return super().delete(request, *args, **kwargs)


class InvoiceListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    required_access = 'billing.admin.invoices'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # For superusers, show all invoices; for regular users, filter by their tenant
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'tenant_id'):
                queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        
        # Apply filters if provided
        tenant_id = self.request.GET.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            from django.utils.dateparse import parse_date
            from_date = parse_date(date_from)
            if from_date:
                queryset = queryset.filter(due_date__gte=from_date)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            from django.utils.dateparse import parse_date
            to_date = parse_date(date_to)
            if to_date:
                queryset = queryset.filter(due_date__lte=to_date)
        
        # Prefetch related objects for better performance
        queryset = queryset.select_related('subscription', 'subscription__user')
        
        return queryset.order_by('-invoice_created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create a form instance with GET parameters for the search form
        from django import forms
        from tenants.models import Tenant as TenantModel
        
        class InvoiceSearchForm(forms.Form):
            if self.request.user.is_superuser or self.request.user.is_staff:
                tenant_id = forms.ModelChoiceField(
                    queryset=TenantModel.objects.all(),
                    required=False,
                    label="Tenant"
                )
            status = forms.ChoiceField(
                choices=[('', 'All Statuses')] + Invoice.STATUS_CHOICES,
                required=False,
                label="Status"
            )
            date_from = forms.DateField(
                required=False,
                label="From Date",
                widget=forms.DateInput(attrs={'type': 'date'})
            )
            date_to = forms.DateField(
                required=False,
                label="To Date",
                widget=forms.DateInput(attrs={'type': 'date'})
            )
        
        # Initialize the form with GET parameters
        search_form = InvoiceSearchForm(self.request.GET)
        context['search_form'] = search_form
        
        return context

class InvoiceCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_create.html'
    success_url = reverse_lazy('billing:invoice_list')
    required_access = 'billing.admin.invoices'
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
            
        response = super().form_valid(form)
        

        # Log engagement event for invoice generated
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='invoice_generated',
                description=f"Invoice generated: {self.object.invoice_number}",
                title="Invoice Generated",
                metadata={
                    'invoice_id': self.object.id,
                    'invoice_number': self.object.invoice_number,
                    'amount': float(self.object.amount) if self.object.amount else 0,  # Changed from amount_due to amount
                    'due_date': self.object.due_date.isoformat() if self.object.due_date else None
                },
                engagement_score=2,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")

            
        messages.success(self.request, 'Invoice created successfully.')
        return response


class InvoiceUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_create.html'
    success_url = reverse_lazy('billing:invoice_list')
    required_access = 'billing.admin.invoices'
    
    def form_valid(self, form):
        messages.success(self.request, 'Invoice updated successfully.')
        return super().form_valid(form)


class InvoiceDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'billing/invoice_confirm_delete.html'
    success_url = reverse_lazy('billing:invoice_list')
    required_access = 'billing.admin.invoices'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Invoice deleted successfully.')
        return super().delete(request, *args, **kwargs)


class CreditAdjustmentListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = CreditAdjustment
    template_name = 'billing/credit_adjustment_list.html'
    context_object_name = 'credit_adjustments'
    required_access = 'billing.admin.adjustments'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('subscription', 'invoice', 'adjustment_type_ref')


class CreditAdjustmentCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = CreditAdjustment
    form_class = CreditAdjustmentForm
    template_name = 'billing/credit_adjustment_form.html'
    success_url = reverse_lazy('billing:credit_adjustment_list')
    required_access = 'billing.admin.adjustments'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Credit adjustment created successfully.')
        return super().form_valid(form)

class CreditAdjustmentUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = CreditAdjustment
    form_class = CreditAdjustmentForm
    template_name = 'billing/credit_adjustment_form.html'
    success_url = reverse_lazy('billing:credit_adjustment_list')
    required_access = 'billing.admin.adjustments'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Credit adjustment updated successfully.')
        return super().form_valid(form)


class CreditAdjustmentDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = CreditAdjustment
    template_name = 'billing/credit_adjustment_confirm_delete.html'
    success_url = reverse_lazy('billing:credit_adjustment_list')
    required_access = 'billing.admin.adjustments'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Credit adjustment deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentProviderConfigListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = PaymentProviderConfig
    template_name = 'billing/payment_provider_config_list.html'
    context_object_name = 'payment_configs'
    required_access = 'billing.admin.config'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('name_ref')


class PaymentProviderConfigCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_provider_config_form.html'
    success_url = reverse_lazy('billing:payment_provider_config_list')
    required_access = 'billing.admin.config'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment provider configuration created successfully.')
        return super().form_valid(form)

class PaymentProviderConfigUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_provider_config_form.html'
    success_url = reverse_lazy('billing:payment_provider_config_list')
    required_access = 'billing.admin.config'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment provider configuration updated successfully.')
        return super().form_valid(form)


class PaymentProviderConfigDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = PaymentProviderConfig
    template_name = 'billing/payment_provider_config_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_provider_config_list')
    required_access = 'billing.admin.config'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment provider configuration deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentMethodListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = PaymentMethod
    template_name = 'billing/payment_method_list.html'
    context_object_name = 'payment_methods'
    required_access = 'billing.payment_method.view'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('user', 'type_ref', 'provider')


class PaymentMethodCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'billing/payment_method_form.html'
    success_url = reverse_lazy('billing:payment_method_list')
    required_access = 'billing.payment_method.manage'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Payment method created successfully.')
        return super().form_valid(form)

class PaymentMethodUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'billing/payment_method_form.html'
    success_url = reverse_lazy('billing:payment_method_list')
    required_access = 'billing.payment_method.manage'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment method updated successfully.')
        return super().form_valid(form)


class PaymentMethodDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = PaymentMethod
    template_name = 'billing/payment_method_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_method_list')
    required_access = 'billing.payment_method.manage'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment method deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PaymentListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'billing/payment_list.html'
    context_object_name = 'payments'
    required_access = 'billing.admin.payments'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('invoice', 'payment_method')


class PaymentCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'billing/payment_form.html'
    success_url = reverse_lazy('billing:payment_list')
    required_access = 'billing.admin.payments'
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
            
        response = super().form_valid(form)
        
        # Log engagement event for payment received
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='payment_received',
                description=f"Payment received: {self.object.amount}",
                title="Payment Received",
                metadata={
                    'payment_id': self.object.id,
                    'amount': float(self.object.amount) if self.object.amount else 0,
                    'payment_method': str(self.object.payment_method)
                },
                engagement_score=5,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
            
        messages.success(self.request, 'Payment created successfully.')
        return response


class PaymentUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'billing/payment_form.html'
    success_url = reverse_lazy('billing:payment_list')
    required_access = 'billing.admin.payments'
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment updated successfully.')
        return super().form_valid(form)


class PaymentDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = Payment
    template_name = 'billing/payment_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_list')
    required_access = 'billing.admin.payments'
    
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
        # Use the correct field name for label in the values call
        choices = model_class.objects.filter(tenant_id=tenant_id).values('id', 'label')
        return JsonResponse(list(choices), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



# === Additional Views Referenced in urls.py ===

class BillingPortalView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Tenant billing portal landing page."""
    template_name = 'billing/portal.html'
    required_access = 'billing.portal'


# Revenue Dashboard Views
class RevenueOverviewView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Revenue overview dashboard."""
    template_name = 'billing/revenue_overview.html'
    required_access = 'billing.admin.revenue'
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = Subscription.objects.filter(subscription_is_active=True, tenant_id=self.request.user.tenant_id)[:10]
        return context



class MRRAnalyticsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Monthly Recurring Revenue analytics."""
    template_name = 'billing/mrr_analytics.html'
    required_access = 'billing.admin.revenue'


class ARRAnalyticsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Annual Recurring Revenue analytics."""
    template_name = 'billing/arr_analytics.html'
    required_access = 'billing.admin.revenue'


class ChurnRatesView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Churn rates analytics."""
    template_name = 'billing/churn_rates.html'
    required_access = 'billing.admin.revenue'


class RevenueForecastView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Revenue forecast view."""
    template_name = 'billing/revenue_forecast.html'
    required_access = 'billing.admin.revenue'


# Invoice Management Views
class InvoiceDetailView(SecureViewMixin, LoginRequiredMixin, DetailView):
    """Invoice detail view."""
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    pk_url_kwarg = 'invoice_id'
    required_access = 'billing.admin.invoices'


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


class PaidInvoicesView(SecureViewMixin, LoginRequiredMixin, ListView):
    """List paid invoices."""
    model = Invoice
    template_name = 'billing/invoice_paid_list.html'
    context_object_name = 'invoices'
    required_access = 'billing.admin.invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='paid')


class OverdueInvoicesView(SecureViewMixin, LoginRequiredMixin, ListView):
    """List overdue invoices."""
    model = Invoice
    template_name = 'billing/invoice_overdue_list.html'
    context_object_name = 'invoices'
    required_access = 'billing.admin.invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='overdue')


class VoidInvoicesView(SecureViewMixin, LoginRequiredMixin, ListView):
    """List void invoices."""
    model = Invoice
    template_name = 'billing/invoice_void_list.html'
    context_object_name = 'invoices'
    required_access = 'billing.admin.invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='void')


class ReconciliationView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Invoice reconciliation view."""
    template_name = 'billing/reconciliation.html'
    required_access = 'billing.admin.invoices'


# Invoicing Engine Views

class InvoiceGenerationView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Invoice generation view."""
    template_name = 'billing/invoice_generation.html'
    required_access = 'billing.admin.dunning'
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get subscriptions that need invoices (active subscriptions) for the current tenant
        subscriptions_needing_invoices = Subscription.objects.filter(
            subscription_is_active=True,
            tenant_id=self.request.user.tenant_id
        ).select_related('subscription_plan')
        
        context['subscriptions_needing_invoices'] = subscriptions_needing_invoices
        context['subscriptions_count'] = subscriptions_needing_invoices.count()
        return context

    

    def post(self, request, *args, **kwargs):
        # Get active subscriptions that need invoices for the current tenant
        subscriptions = Subscription.objects.filter(
            subscription_is_active=True,
            tenant_id=request.user.tenant_id
        ).select_related('subscription_plan')
        
        generated_count = 0
        
        # Generate invoices for each subscription
        for subscription in subscriptions:
            try:
                # Create a new invoice for the subscription
                from django.db.models import Max
                last_invoice = Invoice.objects.filter(tenant=subscription.tenant).aggregate(Max('invoice_number'))
                last_number = last_invoice['invoice_number__max']
                
                if last_number:
                    import re
                    match = re.search(r'(\d+)$', str(last_number))
                    if match:
                        next_number = int(match.group(1)) + 1
                    else:
                        next_number = 1
                else:
                    next_number = 1
                
                invoice_number = f"INV-{next_number:06d}"
                

                # Calculate amount from plan price
                amount = subscription.subscription_plan.price  # Changed from price_monthly to price

                
                # Set due date (7 days from now)
                due_date = timezone.now().date() + timedelta(days=7)
                
                # Create the invoice
                invoice = Invoice.objects.create(
                    invoice_number=invoice_number,
                    subscription=subscription,
                    amount=amount,
                    due_date=due_date,
                    status='open',
                    tenant_id=subscription.tenant_id
                )
                
                generated_count += 1
            except Exception as e:
                # Log error but continue with other subscriptions
                print(f"Error generating invoice for subscription {subscription.id}: {e}")
        
        messages.success(request, f'Successfully generated {generated_count} invoices.')
        return redirect('billing:invoice_generation')




class DunningManagementView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Dunning management view."""
    template_name = 'billing/dunning_management.html'
    required_access = 'billing.admin.dunning'


class FailedPaymentsView(SecureViewMixin, LoginRequiredMixin, ListView):
    """View failed payments."""
    model = Payment
    template_name = 'billing/failed_payments.html'
    context_object_name = 'payments'
    required_access = 'billing.admin.payments'
    
    def get_queryset(self):
        return Payment.objects.filter(status='failed')


# Plan Views

class PlanDetailView(SecureViewMixin, LoginRequiredMixin, DetailView):
    """Plan detail view."""
    model = Plan
    template_name = 'billing/plan_detail.html'
    context_object_name = 'plan'
    pk_url_kwarg = 'plan_id'
    required_access = 'billing.admin.plans'







class PricingConfigView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Plan pricing configuration."""
    template_name = 'billing/pricing_config.html'
    required_access = 'billing.admin.plans'



class PlanToggleActiveView(LoginRequiredMixin, View):
    """Toggle plan active status."""
    def post(self, request, plan_id):
        plan = get_object_or_404(Plan, pk=plan_id)
        plan.is_active = not plan.is_active  # Use the correct field name
        plan.save()
        status = 'activated' if plan.is_active else 'deactivated'
        messages.success(request, f'Plan {plan.name} {status}.')  # Use the correct field name
        return redirect('billing:plan_list')



 
class PlanLimitsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Plan limits configuration."""
    template_name = 'billing/plan_limits.html'
    required_access = 'billing.admin.plans'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all plans for the tenant (or all plans if this is a global view)
        context['plans'] = Plan.objects.all().order_by('-price')
        return context

# Subscription Views
class SubscriptionDetailView(SecureViewMixin, LoginRequiredMixin, DetailView):
    """Subscription detail view."""
    model = Subscription
    template_name = 'billing/subscription_detail.html'
    pk_url_kwarg = 'subscription_id'
    required_access = 'billing.subscription.view'


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




class UpgradeDowngradeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Upgrade/downgrade subscription view."""
    template_name = 'billing/upgrade_downgrade.html'
    
    def test_func(self):
        # Allow superusers to upgrade/downgrade any tenant
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # For superusers, get all subscriptions
        if self.request.user.is_superuser:
            context['subscriptions'] = Subscription.objects.select_related('subscription_plan').all()
        else:
            # For regular users, get only their tenant's subscriptions
            context['subscriptions'] = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).select_related('subscription_plan')
        
        # Get all available plans
        context['plans'] = Plan.objects.filter(is_active=True)
        return context

    def post(self, request, *args, **kwargs):
        subscription_id = request.POST.get('subscription_id')
        new_plan_id = request.POST.get('new_plan_id')
        
        if not subscription_id or not new_plan_id:
            messages.error(request, 'Please select both a subscription and a new plan.')
            return redirect('billing:upgrade_downgrade')
        
        try:
            subscription = Subscription.objects.get(id=subscription_id)
            new_plan = Plan.objects.get(id=new_plan_id)
            
            # Verify the user has permission to modify this subscription
            if not request.user.is_superuser and subscription.tenant_id != request.user.tenant_id:
                messages.error(request, 'You do not have permission to modify this subscription.')
                return redirect('billing:upgrade_downgrade')
            
            # Store old plan for reference
            old_plan = subscription.subscription_plan
            
            # Update the subscription plan
            subscription.subscription_plan = new_plan
            subscription.save()
            
            # Log the change
            messages.success(
                request, 
                f'Subscription successfully changed from {old_plan.name} to {new_plan.name}.'
            )
            
            # Redirect to the same page to show updated information
            return redirect('billing:upgrade_downgrade')
            
        except Subscription.DoesNotExist:
            messages.error(request, 'Subscription not found.')
        except Plan.DoesNotExist:
            messages.error(request, 'Plan not found.')
        except Exception as e:
            messages.error(request, f'Error updating subscription: {str(e)}')
        
        return redirect('billing:upgrade_downgrade')



class ProrationCalculatorView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Proration calculator view."""
    template_name = 'billing/proration_calculator.html'
    required_access = 'billing.admin.subscriptions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # For superusers, get all subscriptions; for regular users, get only their tenant's subscriptions
        if self.request.user.is_superuser:
            subscriptions = Subscription.objects.select_related('subscription_plan', 'user').all()
        else:
            subscriptions = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).select_related('subscription_plan', 'user')
        
        # Get all active plans
        plans = Plan.objects.filter(is_active=True)
        
        context['subscriptions'] = subscriptions
        context['plans'] = plans
        
        # Process form data if provided
        subscription_id = self.request.GET.get('subscription_id')
        new_plan_id = self.request.GET.get('new_plan_id')
        
        if subscription_id and new_plan_id:
            try:
                subscription = Subscription.objects.select_related('subscription_plan').get(id=subscription_id)
                new_plan = Plan.objects.get(id=new_plan_id)
                
                # Verify permission - superusers can access any subscription, regular users only their tenant's
                if not self.request.user.is_superuser and subscription.tenant_id != self.request.user.tenant_id:
                    context['error'] = 'You do not have permission to access this subscription.'
                    return context
                
                # Calculate proration
                proration_amount = self.calculate_proration(subscription, new_plan)
                
                context['subscription'] = subscription
                context['new_plan'] = new_plan
                context['proration_amount'] = proration_amount
                
            except Subscription.DoesNotExist:
                context['error'] = 'Subscription not found.'
            except Plan.DoesNotExist:
                context['error'] = 'Plan not found.'
        
        return context

  
    
    
    def calculate_proration(self, subscription, new_plan):
        """
        Calculate proration amount for changing from current plan to new plan
        Positive value means customer pays, negative means customer gets credit
        """
        from datetime import datetime
        
        # Get the current plan price
        current_price = subscription.price_monthly  # Using the property that returns the plan price
        
        # Get new plan price
        new_price = new_plan.price if new_plan else 0
        
        # Calculate the difference
        price_difference = new_price - current_price
        
        # Calculate proration based on remaining days in billing cycle
        # Using the current period end date from the subscription
        today = timezone.now().date()
        current_period_end = subscription.current_period_end.date()  # Convert to date
        
        # Calculate days remaining in billing cycle
        if current_period_end > today:
            days_remaining = (current_period_end - today).days
        else:
            days_remaining = 0  # If billing cycle has ended
        
        # Calculate daily rate for the price difference
        # Calculate based on the total billing period (default 30 days)
        billing_period_days = 30
        
        # Calculate prorated amount
        if billing_period_days > 0:
            daily_rate = price_difference / billing_period_days
            prorated_amount = daily_rate * days_remaining
        else:
            prorated_amount = 0  # Avoid division by zero
        
        return round(prorated_amount, 2)




class LifecycleEventsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Subscription lifecycle events."""
    template_name = 'billing/lifecycle_events.html'
    required_access = 'billing.admin.lifecycle'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # For superusers, get all subscriptions; for regular users, get only their tenant's subscriptions
        if self.request.user.is_superuser:
            subscriptions = Subscription.objects.select_related('subscription_plan', 'user').all()
        else:
            subscriptions = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).select_related('subscription_plan', 'user')
        
        context['subscriptions'] = subscriptions
        return context




class RenewalTrackingView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Subscription renewal tracking."""
    template_name = 'billing/renewal_tracking.html'
    required_access = 'billing.admin.lifecycle'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from django.utils import timezone
        from datetime import timedelta
        
        # Calculate the date 30 days from now
        thirty_days_from_now = timezone.now() + timedelta(days=30)
        
        # For superusers, get all subscriptions; for regular users, get only their tenant's subscriptions
        if self.request.user.is_superuser:
            # Get all active subscriptions that are ending in the next 30 days
            upcoming_renewals = Subscription.objects.filter(
                subscription_is_active=True
            )
        else:
            # Get only the current tenant's subscriptions
            upcoming_renewals = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id,
                subscription_is_active=True
            )
        
        # Filter for subscriptions that end in the next 30 days
        # Use the current_period_end property to get the actual end date
        filtered_renewals = []
        for sub in upcoming_renewals:
            if sub.current_period_end and sub.current_period_end <= thirty_days_from_now:
                filtered_renewals.append(sub)
        
        context['upcoming_renewals'] = filtered_renewals
        return context




class CancellationManagementView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Cancellation management view."""
    template_name = 'billing/cancellation_management.html'
    required_access = 'billing.admin.lifecycle'


# Tenant Billing Views
class TenantBillingSearchView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Search tenant billing."""
    template_name = 'billing/tenant_billing_search.html'
    required_access = 'billing.admin.tenant_search'


class BillingHistoryView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Tenant billing history."""
    template_name = 'billing/billing_history.html'
    required_access = 'billing.history.view'


class CreditAdjustmentManagementView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Credit adjustment management."""
    template_name = 'billing/credit_adjustment_management.html'
    required_access = 'billing.admin.adjustments'


# Payment Gateway Views
class PaymentGatewayListView(SecureViewMixin, LoginRequiredMixin, ListView):
    """List payment gateways."""
    model = PaymentProviderConfig
    template_name = 'billing/payment_gateway_list.html'
    context_object_name = 'gateways'
    required_access = 'billing.admin.gateways'


class PaymentGatewayCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    """Create payment gateway."""
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_gateway_form.html'
    success_url = reverse_lazy('billing:payment_gateway_list')
    required_access = 'billing.admin.gateways'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs


class PaymentGatewayConfigView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    """Configure payment gateway."""
    model = PaymentProviderConfig
    form_class = PaymentProviderConfigForm
    template_name = 'billing/payment_gateway_config.html'
    pk_url_kwarg = 'provider_id'
    success_url = reverse_lazy('billing:payment_gateway_list')
    required_access = 'billing.admin.gateways'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs



class TenantPaymentConfigView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Tenant payment configuration."""
    template_name = 'billing/tenant_payment_config.html'
    required_access = 'billing.payment_method.manage'




class PlanFeatureAccessListView(SecureViewMixin, LoginRequiredMixin, ListView):
    """View for listing plan feature access"""
    model = PlanFeatureAccess
    template_name = 'billing/plan_feature_access_list.html'
    context_object_name = 'plan_features'
    paginate_by = 20
    required_access = 'billing.admin.plans'
    
    def get_queryset(self):
        plan_id = self.request.GET.get('plan_id')
        if plan_id:
            return PlanFeatureAccess.objects.filter(plan_id=plan_id).select_related('plan')
        return PlanFeatureAccess.objects.select_related('plan')


class PlanFeatureAccessCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    """View for creating plan feature access"""
    model = PlanFeatureAccess
    fields = ['plan', 'feature_key', 'feature_name', 'feature_category', 'is_available', 'notes']
    template_name = 'billing/plan_feature_access_form.html'
    success_url = reverse_lazy('billing:plan_feature_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Feature access "{form.instance.feature_name}" created successfully.')
        return super().form_valid(form)


class PlanFeatureAccessUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    """View for updating plan feature access"""
    model = PlanFeatureAccess
    fields = ['plan', 'feature_key', 'feature_name', 'feature_category', 'is_available', 'notes']
    template_name = 'billing/plan_feature_access_form.html'
    success_url = reverse_lazy('billing:plan_feature_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Feature access "{form.instance.feature_name}" updated successfully.')
        return super().form_valid(form)


class PlanFeatureAccessDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    """View for deleting plan feature access"""
    model = PlanFeatureAccess
    template_name = 'billing/plan_feature_access_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_feature_access_list')
    required_access = 'billing.admin.plans'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Feature access "{self.get_object().feature_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PlanModuleAccessListView(SecureViewMixin, LoginRequiredMixin, ListView):
    """View for listing plan module access"""
    model = PlanModuleAccess
    template_name = 'billing/plan_module_access_list.html'
    context_object_name = 'plan_modules'
    paginate_by = 20
    required_access = 'billing.admin.plans'
    
    def get_queryset(self):
        plan_id = self.request.GET.get('plan_id')
        if plan_id:
            return PlanModuleAccess.objects.filter(plan_id=plan_id).select_related('plan')
        return PlanModuleAccess.objects.select_related('plan')


class PlanModuleAccessCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    """View for creating plan module access"""
    model = PlanModuleAccess
    fields = ['plan', 'module_name', 'module_display_name', 'is_available', 'notes']
    template_name = 'billing/plan_module_access_form.html'
    success_url = reverse_lazy('billing:plan_module_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Module access "{form.instance.module_display_name}" created successfully.')
        return super().form_valid(form)


class PlanModuleAccessUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    """View for updating plan module access"""
    model = PlanModuleAccess
    fields = ['plan', 'module_name', 'module_display_name', 'is_available', 'notes']
    template_name = 'billing/plan_module_access_form.html'
    success_url = reverse_lazy('billing:plan_module_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Module access "{form.instance.module_display_name}" updated successfully.')
        return super().form_valid(form)


class PlanModuleAccessDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    """View for deleting plan module access"""
    model = PlanModuleAccess
    template_name = 'billing/plan_module_access_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_module_access_list')
    required_access = 'billing.admin.plans'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Module access "{self.get_object().module_display_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)










