from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from core.views import (
    TenantAwareViewMixin, SalesCompassListView, SalesCompassDetailView,
    SalesCompassCreateView, SalesCompassUpdateView, SalesCompassDeleteView
)
from django.urls import reverse_lazy
from .models import (
    Plan, Subscription, PlanTier, SubscriptionStatus, 
    PlanFeatureAccess, PlanModuleAccess,
    Invoice, Payment, CreditAdjustment, PaymentProviderConfig, 
    PaymentMethod, PaymentProvider, PaymentType, AdjustmentType
)
from .forms import (
    PlanForm, SubscriptionForm, PlanTierForm, SubscriptionStatusForm,
    InvoiceForm, PaymentForm, CreditAdjustmentForm, 
    PaymentProviderConfigForm, PaymentMethodForm, PaymentProviderForm, 
    PaymentTypeForm, AdjustmentTypeForm
)
from tenants.models import Tenant as TenantModel
import logging
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta
from engagement.utils import log_engagement_event

logger = logging.getLogger(__name__)

from access_control.views import SecureViewMixin
from access_control.utils import access_required
from core.event_bus import event_bus

class BillingDashboardView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/dashboard.html'
    required_access = 'billing.dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage_plans'] = self.can_access('billing.plans', 'manage')
        context['can_manage_subscriptions'] = self.can_access('billing.subscriptions', 'manage')
        # Payments now in Invoicing, removed context
        return context

@access_required('billing.reports.view')
def billing_reports_view(request):
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

class PlanListView(SalesCompassListView):
    model = Plan
    template_name = 'billing/plan_list.html'
    context_object_name = 'plans'
    required_access = 'billing.plans'
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class PlanCreateView(SalesCompassCreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_form.html'
    success_url = reverse_lazy('billing:plan_list')
    required_access = 'billing.plans'
    
    def form_valid(self, form):
        messages.success(self.request, 'Plan created successfully.')
        return super().form_valid(form)

class PlanUpdateView(SalesCompassUpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_form.html'
    success_url = reverse_lazy('billing:plan_list')
    required_access = 'billing.plans'
    pk_url_kwarg = 'plan_id'
    
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

class SubscriptionListView(SalesCompassListView):
    model = Subscription
    template_name = 'billing/subscription_list.html'
    context_object_name = 'subscriptions'
    paginate_by = 20
    required_access = 'billing.subscriptions'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(user__email__icontains=search_query)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related('subscription_plan', 'user', 'status_ref').order_by('-subscription_created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['status_choices'] = STATUS_CHOICES = [
            ('active', 'Active'),
            ('trialing', 'Trialing'),
            ('canceled', 'Canceled'),
            ('past_due', 'Past Due'),
            ('incomplete', 'Incomplete'),
        ]
        return context

class SubscriptionCreateView(SalesCompassCreateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'billing/subscription_form.html'
    success_url = reverse_lazy('billing:subscription_list')
    required_access = 'billing.subscriptions'
     
    def form_valid(self, form):
        response = super().form_valid(form)
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
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                kwargs['tenant'] = None
        else:
            kwargs['tenant'] = None
        return kwargs
    
    def form_valid(self, form):
        if self.request.user.is_superuser or self.request.user.is_staff:
            selected_user = form.cleaned_data.get('user')
            if selected_user and hasattr(selected_user, 'tenant_id'):
                form.instance.tenant_id = selected_user.tenant_id
        
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

class PlanDetailView(SecureViewMixin, LoginRequiredMixin, DetailView):
    model = Plan
    template_name = 'billing/plan_detail.html'
    context_object_name = 'plan'
    pk_url_kwarg = 'plan_id'
    required_access = 'billing.admin.plans'

class PricingConfigView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/pricing_config.html'
    required_access = 'billing.admin.plans'

class PlanToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, plan_id):
        plan = get_object_or_404(Plan, pk=plan_id)
        plan.is_active = not plan.is_active
        plan.save()
        status = 'activated' if plan.is_active else 'deactivated'
        messages.success(request, f'Plan {plan.name} {status}.')
        return redirect('billing:plan_list')
 
class PlanLimitsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/plan_limits.html'
    required_access = 'billing.admin.plans'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.all().order_by('-price')
        return context

class SubscriptionDetailView(SecureViewMixin, LoginRequiredMixin, DetailView):
    model = Subscription
    template_name = 'billing/subscription_detail.html'
    pk_url_kwarg = 'subscription_id'
    required_access = 'billing.subscription.view'

class SubscriptionCancelView(LoginRequiredMixin, View):
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
    def post(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, pk=subscription_id)
        subscription.status = 'active'
        subscription.subscription_is_active = True
        subscription.save()
        messages.success(request, 'Subscription reactivated.')
        return redirect('billing:subscription_list')

class UpgradeDowngradeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'billing/upgrade_downgrade.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            context['subscriptions'] = Subscription.objects.select_related('subscription_plan').all()
        else:
            context['subscriptions'] = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).select_related('subscription_plan')
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
            
            if not request.user.is_superuser and subscription.tenant_id != request.user.tenant_id:
                messages.error(request, 'You do not have permission to modify this subscription.')
                return redirect('billing:upgrade_downgrade')
            
            old_plan = subscription.subscription_plan
            subscription.subscription_plan = new_plan
            subscription.save()
            messages.success(
                request, 
                f'Subscription successfully changed from {old_plan.name} to {new_plan.name}.'
            )
            return redirect('billing:upgrade_downgrade')
        except Exception as e:
            messages.error(request, f'Error updating subscription: {str(e)}')
        return redirect('billing:upgrade_downgrade')

class ProrationCalculatorView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/proration_calculator.html'
    required_access = 'billing.admin.subscriptions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            subscriptions = Subscription.objects.select_related('subscription_plan', 'user').all()
        else:
            subscriptions = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).select_related('subscription_plan', 'user')
        
        plans = Plan.objects.filter(is_active=True)
        context['subscriptions'] = subscriptions
        context['plans'] = plans
        
        subscription_id = self.request.GET.get('subscription_id')
        new_plan_id = self.request.GET.get('new_plan_id')
        
        if subscription_id and new_plan_id:
            try:
                subscription = Subscription.objects.select_related('subscription_plan').get(id=subscription_id)
                new_plan = Plan.objects.get(id=new_plan_id)
                
                if not self.request.user.is_superuser and subscription.tenant_id != self.request.user.tenant_id:
                    context['error'] = 'You do not have permission to access this subscription.'
                    return context
                
                proration_amount = self.calculate_proration(subscription, new_plan)
                context['subscription'] = subscription
                context['new_plan'] = new_plan
                context['proration_amount'] = proration_amount
            except Exception as e:
                context['error'] = str(e)
        return context
    
    def calculate_proration(self, subscription, new_plan):
        current_price = subscription.price_monthly
        new_price = new_plan.price if new_plan else 0
        price_difference = new_price - current_price
        
        today = timezone.now().date()
        current_period_end = subscription.current_period_end.date()
        
        if current_period_end > today:
            days_remaining = (current_period_end - today).days
        else:
            days_remaining = 0
        
        billing_period_days = 30
        if billing_period_days > 0:
            daily_rate = price_difference / billing_period_days
            prorated_amount = daily_rate * days_remaining
        else:
            prorated_amount = 0
        
        return round(prorated_amount, 2)

class LifecycleEventsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/lifecycle_events.html'
    required_access = 'billing.admin.lifecycle'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            subscriptions = Subscription.objects.select_related('subscription_plan', 'user').all()
        else:
            subscriptions = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).select_related('subscription_plan', 'user')
        context['subscriptions'] = subscriptions
        return context

class RenewalTrackingView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/renewal_tracking.html'
    required_access = 'billing.admin.lifecycle'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thirty_days_from_now = timezone.now() + timedelta(days=30)
        
        if self.request.user.is_superuser:
            upcoming_renewals = Subscription.objects.filter(subscription_is_active=True)
        else:
            upcoming_renewals = Subscription.objects.filter(
                tenant_id=self.request.user.tenant_id,
                subscription_is_active=True
            )
        
        filtered_renewals = []
        for sub in upcoming_renewals:
            if sub.current_period_end and sub.current_period_end <= thirty_days_from_now:
                filtered_renewals.append(sub)
        
        context['upcoming_renewals'] = filtered_renewals
        return context

class CancellationManagementView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/cancellation_management.html'
    required_access = 'billing.admin.lifecycle'

class BillingPortalView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/portal.html'
    required_access = 'billing.portal'

class RevenueOverviewView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/revenue_overview.html'
    required_access = 'billing.admin.revenue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = Subscription.objects.filter(subscription_is_active=True, tenant_id=self.request.user.tenant_id)[:10]
        return context

class MRRAnalyticsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/mrr_analytics.html'
    required_access = 'billing.admin.revenue'

class ARRAnalyticsView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/arr_analytics.html'
    required_access = 'billing.admin.revenue'

class ChurnRatesView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/churn_rates.html'
    required_access = 'billing.admin.revenue'

class RevenueForecastView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/revenue_forecast.html'
    required_access = 'billing.admin.revenue'

class PlanFeatureAccessListView(SecureViewMixin, LoginRequiredMixin, ListView):
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
    model = PlanFeatureAccess
    fields = ['plan', 'feature_key', 'feature_name', 'feature_category', 'is_available', 'notes']
    template_name = 'billing/plan_feature_access_form.html'
    success_url = reverse_lazy('billing:plan_feature_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Feature access "{form.instance.feature_name}" created successfully.')
        return super().form_valid(form)

class PlanFeatureAccessUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PlanFeatureAccess
    fields = ['plan', 'feature_key', 'feature_name', 'feature_category', 'is_available', 'notes']
    template_name = 'billing/plan_feature_access_form.html'
    success_url = reverse_lazy('billing:plan_feature_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Feature access "{form.instance.feature_name}" updated successfully.')
        return super().form_valid(form)

class PlanFeatureAccessDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = PlanFeatureAccess
    template_name = 'billing/plan_feature_access_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_feature_access_list')
    required_access = 'billing.admin.plans'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Feature access "{self.get_object().feature_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

class PlanModuleAccessListView(SecureViewMixin, LoginRequiredMixin, ListView):
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
    model = PlanModuleAccess
    fields = ['plan', 'module_name', 'module_display_name', 'is_available', 'notes']
    template_name = 'billing/plan_module_access_form.html'
    success_url = reverse_lazy('billing:plan_module_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Module access "{form.instance.module_display_name}" created successfully.')
        return super().form_valid(form)

class PlanModuleAccessUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PlanModuleAccess
    fields = ['plan', 'module_name', 'module_display_name', 'is_available', 'notes']
    template_name = 'billing/plan_module_access_form.html'
    success_url = reverse_lazy('billing:plan_module_access_list')
    required_access = 'billing.admin.plans'
    
    def form_valid(self, form):
        messages.success(self.request, f'Module access "{form.instance.module_display_name}" updated successfully.')
        return super().form_valid(form)

class PlanModuleAccessDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = PlanModuleAccess
    template_name = 'billing/plan_module_access_confirm_delete.html'
    success_url = reverse_lazy('billing:plan_module_access_list')
    required_access = 'billing.admin.plans'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Module access "{self.get_object().module_display_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# === Platform Invoice Views (Moved from Invoicing) ===

class InvoiceListView(SalesCompassListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    required_access = 'billing.invoices'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters if provided
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

class InvoiceCreateView(SalesCompassCreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_create.html'
    success_url = reverse_lazy('billing:invoice_list')
    required_access = 'billing.invoices'
    
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
                    'amount': float(self.object.amount) if self.object.amount else 0,
                    'due_date': self.object.due_date.isoformat() if self.object.due_date else None
                },
                engagement_score=2,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
            
        messages.success(self.request, 'Invoice created successfully.')
        return response

class InvoiceUpdateView(SalesCompassUpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_create.html'
    success_url = reverse_lazy('billing:invoice_list')
    required_access = 'billing.invoices'
    
    def form_valid(self, form):
        messages.success(self.request, 'Invoice updated successfully.')
        return super().form_valid(form)


class InvoiceDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'billing/invoice_confirm_delete.html'
    success_url = reverse_lazy('billing:invoice_list')
    required_access = 'billing.invoices'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Invoice deleted successfully.')
        return super().delete(request, *args, **kwargs)


class InvoiceDetailView(SecureViewMixin, LoginRequiredMixin, DetailView):
    """Invoice detail view."""
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    pk_url_kwarg = 'invoice_id'
    required_access = 'billing.invoices'


class InvoiceMarkPaidView(LoginRequiredMixin, View):
    """Mark invoice as paid."""
    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        invoice.status = 'paid'
        invoice.save()
        
        event_bus.emit('invoice.paid', {
            'invoice_id': invoice.id,
            'amount': float(invoice.amount),
            'tenant_id': request.user.tenant_id if hasattr(request.user, 'tenant_id') else None,
            'user': request.user
        })
        
        # Also emit payment.received since it implies payment
        event_bus.emit('payment.received', {
            'invoice_id': invoice.id,
            'amount': float(invoice.amount),
            'source': 'manual_mark_paid',
            'tenant_id': request.user.tenant_id if hasattr(request.user, 'tenant_id') else None,
            'user': request.user
        })
        
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
    required_access = 'billing.invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='paid')


class OverdueInvoicesView(SecureViewMixin, LoginRequiredMixin, ListView):
    """List overdue invoices."""
    model = Invoice
    template_name = 'billing/invoice_overdue_list.html'
    context_object_name = 'invoices'
    required_access = 'billing.invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='overdue')


class VoidInvoicesView(SecureViewMixin, LoginRequiredMixin, ListView):
    """List void invoices."""
    model = Invoice
    template_name = 'billing/invoice_void_list.html'
    context_object_name = 'invoices'
    required_access = 'billing.invoices'
    
    def get_queryset(self):
        return Invoice.objects.filter(status='void')


class ReconciliationView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Invoice reconciliation view."""
    template_name = 'billing/reconciliation.html'
    required_access = 'billing.invoices'


# === Invoicing Engine Views ===

class InvoiceGenerationView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Invoice generation view."""
    template_name = 'billing/invoice_generation.html'
    required_access = 'billing.invoices'
    
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
                amount = subscription.subscription_plan.price
                
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
                
                event_bus.emit('invoice.created', {
                    'invoice_id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'amount': float(invoice.amount),
                    'subscription_id': subscription.id,
                    'tenant_id': subscription.tenant_id,
                    'user': request.user
                })
                
                generated_count += 1
            except Exception as e:
                # Log error but continue with other subscriptions
                logger.error(f"Error generating invoice for subscription {subscription.id}: {e}")
        
        messages.success(request, f'Successfully generated {generated_count} invoices.')
        return redirect('billing:invoice_generation')

class DunningManagementView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Dunning management view."""
    template_name = 'billing/dunning_management.html'
    required_access = 'billing.invoices'


class FailedPaymentsView(SecureViewMixin, LoginRequiredMixin, ListView):
    """View failed payments."""
    model = Payment
    template_name = 'billing/failed_payments.html'
    context_object_name = 'payments'
    required_access = 'billing.payments'
    
    def get_queryset(self):
        return Payment.objects.filter(status='failed')


# === Payment Views ===

class PaymentListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'billing/payment_list.html'
    context_object_name = 'payments'
    required_access = 'billing.payments'
    
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
    required_access = 'billing.payments'
    
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
            
            event_bus.emit('payment.received', {
                'payment_id': self.object.id,
                'amount': float(self.object.amount),
                'invoice_id': self.object.invoice.id if self.object.invoice else None,
                'tenant_id': self.request.user.tenant_id,
                'user': self.request.user
            })
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
            
        messages.success(self.request, 'Payment created successfully.')
        return response


class PaymentUpdateView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'billing/payment_form.html'
    success_url = reverse_lazy('billing:payment_list')
    required_access = 'billing.payments'
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment updated successfully.')
        return super().form_valid(form)


class PaymentDeleteView(SecureViewMixin, LoginRequiredMixin, DeleteView):
    model = Payment
    template_name = 'billing/payment_confirm_delete.html'
    success_url = reverse_lazy('billing:payment_list')
    required_access = 'billing.payments'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment deleted successfully.')
        return super().delete(request, *args, **kwargs)


# === Credit Adjustment Views ===

class CreditAdjustmentListView(SecureViewMixin, LoginRequiredMixin, ListView):
    model = CreditAdjustment
    template_name = 'billing/credit_adjustment_list.html'
    context_object_name = 'credit_adjustments'
    required_access = 'billing.adjustments'
    
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
    required_access = 'billing.adjustments'
    
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
    required_access = 'billing.adjustments'
    
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
    required_access = 'billing.adjustments'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Credit adjustment deleted successfully.')
        return super().delete(request, *args, **kwargs)


class CreditAdjustmentManagementView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    """Credit adjustment management."""
    template_name = 'billing/credit_adjustment_management.html'
    required_access = 'billing.adjustments'


# === Payment Config Views ===

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
        return queryset


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


# === Tenant Billing Search & History Views ===

class TenantBillingSearchView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/tenant_billing_search.html'
    required_access = 'billing.admin.invoices'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add plans for filter dropdown
        context['plans'] = Plan.objects.all()
        
        # Process Search
        tenant_id = self.request.GET.get('tenant_id')
        status = self.request.GET.get('status')
        plan_id = self.request.GET.get('plan')
        
        if tenant_id or status or plan_id:
            subscriptions = Subscription.objects.select_related('subscription_plan').all()
            
            if tenant_id:
                subscriptions = subscriptions.filter(tenant_id__icontains=tenant_id)
            
            if status:
                subscriptions = subscriptions.filter(status=status)
                
            if plan_id:
                subscriptions = subscriptions.filter(subscription_plan_id=plan_id)
                
            context['subscriptions'] = subscriptions
            
        return context

class BillingHistoryView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/billing_history.html'
    required_access = 'billing.admin.invoices'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id_param = self.kwargs.get('tenant_id')
        context['tenant_id'] = tenant_id_param
        
        # Fetch data for this tenant
        context['invoices'] = Invoice.objects.filter(tenant_id=tenant_id_param).order_by('-created_at')
        context['payments'] = Payment.objects.filter(tenant_id=tenant_id_param).select_related('invoice').order_by('-created_at')
        
        return context

# === Payment Gateway & Config Views (Platform Admin) ===

class PaymentGatewayListView(SecureViewMixin, LoginRequiredMixin, ListView):
    """Manage platform-wide payment providers"""
    model = PaymentProvider
    template_name = 'billing/payment_gateway_list.html'
    context_object_name = 'providers'
    required_access = 'billing.admin.config'
    
    def get_queryset(self):
        # Platform providers (no specific tenant)
        return PaymentProvider.objects.filter(tenant__isnull=True)

class PaymentGatewayCreateView(SecureViewMixin, LoginRequiredMixin, CreateView):
    model = PaymentProvider
    form_class = PaymentProviderForm
    template_name = 'billing/payment_gateway_form.html'
    success_url = reverse_lazy('billing:payment_gateway_list')
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        form.instance.tenant_id = None # Ensure it's platform-wide
        messages.success(self.request, 'Payment gateway created successfully.')
        return super().form_valid(form)

class PaymentGatewayConfigView(SecureViewMixin, LoginRequiredMixin, UpdateView):
    model = PaymentProvider
    form_class = PaymentProviderForm
    template_name = 'billing/payment_gateway_form.html'
    success_url = reverse_lazy('billing:payment_gateway_list')
    pk_url_kwarg = 'provider_id'
    required_access = 'billing.admin.config'
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment gateway configuration updated.')
        return super().form_valid(form)

# === Tenant Payment Configuration ===

class TenantPaymentConfigView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'billing/tenant_payment_config.html'
    # Use a tenant-accessible permission
    required_access = 'billing.config' 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        tenant_id = self.request.user.tenant_id if hasattr(self.request.user, 'tenant_id') else None
        
        # Get all active platform providers
        available_providers = PaymentProvider.objects.filter(tenant__isnull=True, is_active=True)
        
        # Get existing configs for this tenant
        existing_configs = {}
        if tenant_id:
            configs = PaymentProviderConfig.objects.filter(tenant_id=tenant_id)
            for conf in configs:
                existing_configs[conf.provider_id] = conf
        
        # Build display list
        provider_list = []
        for provider in available_providers:
            conf = existing_configs.get(provider.id)
            provider_list.append({
                'provider': provider,
                'is_enabled_for_subscription': conf.is_enabled_for_subscription if conf else False,
                'is_enabled_for_customers': conf.is_enabled_for_customers if conf else False,
                'tenant_config': conf
            })
            
        context['providers'] = provider_list
        return context

    def post(self, request, *args, **kwargs):
        tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
        if not tenant_id:
             messages.error(request, "Tenant context required.")
             return redirect('billing:tenant_payment_config')

        provider_id = request.POST.get('provider_id')
        action = request.POST.get('action')
        
        if provider_id and action:
            provider = get_object_or_404(PaymentProvider, id=provider_id)
            
            # Get or create config
            config, created = PaymentProviderConfig.objects.get_or_create(
                tenant_id=tenant_id,
                provider=provider
            )
            
            if action == 'toggle_subscription':
                config.is_enabled_for_subscription = not config.is_enabled_for_subscription
                msg = f"Subscription payment using {provider.display_name} {'enabled' if config.is_enabled_for_subscription else 'disabled'}."
            elif action == 'toggle_customers':
                config.is_enabled_for_customers = not config.is_enabled_for_customers
                msg = f"Customer payment using {provider.display_name} {'enabled' if config.is_enabled_for_customers else 'disabled'}."
            
            config.save()
            messages.success(request, msg)
            
        return redirect('billing:tenant_payment_config')

# === Dynamic Choices (Ajax) ===

@login_required
def get_invoicing_dynamic_choices(request, model_name):
    query = request.GET.get('q', '')
    data = []
    
    # Implement filtering logic based on model_name
    if model_name == 'invoice':
        qs = Invoice.objects.filter(invoice_number__icontains=query)
        if hasattr(request.user, 'tenant_id'):
            qs = qs.filter(tenant_id=request.user.tenant_id)
        data = [{'id': obj.id, 'text': str(obj)} for obj in qs[:20]]
        
    elif model_name == 'subscription':
         qs = Subscription.objects.filter(user__email__icontains=query) # Example search
         if hasattr(request.user, 'tenant_id'):
            qs = qs.filter(tenant_id=request.user.tenant_id)
         data = [{'id': obj.id, 'text': str(obj)} for obj in qs[:20]]

    return JsonResponse({'results': data})

