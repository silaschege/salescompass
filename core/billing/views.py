from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.urls import reverse_lazy
from datetime import timedelta
from decimal import Decimal

from .models import Subscription, Plan, Invoice, Payment,  CreditAdjustment
from .forms import PlanForm, SubscriptionUpdateForm, CreditAdjustmentForm, InvoiceSearchForm, ProrationForm


# Base mixin for billing views
class BillingStaffMixin(UserPassesTestMixin):
    """Restrict billing views to staff users"""
    def test_func(self):
        return self.request.user.is_staff


class BillingPortalView(LoginRequiredMixin, TemplateView):
    template_name = 'billing/portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        if tenant_id:
            # Get active subscription
            context['subscription'] = Subscription.objects.filter(
                tenant_id=tenant_id, 
                status__in=['active', 'trialing']
            ).select_related('plan').first()
            
            # Get all plans for upgrade/downgrade
            context['plans'] = Plan.objects.filter(is_active=True)
            
            # Get invoices
            context['invoices'] = Invoice.objects.filter(tenant_id=tenant_id).order_by('-created_at')[:10]
        
        return context

    def post(self, request, *args, **kwargs):
        # Handle plan change or cancellation
        action = request.POST.get('action')
        plan_id = request.POST.get('plan_id')
        
        if action == 'change_plan' and plan_id:
            new_plan = Plan.objects.get(id=plan_id)
            tenant_id = getattr(request.user, 'tenant_id', None)
            sub = Subscription.objects.filter(tenant_id=tenant_id).first()
            if sub:
                sub.upgrade_to(new_plan)
                messages.success(request, f"Plan changed to {new_plan.name}")
                
        elif action == 'cancel':
             tenant_id = getattr(request.user, 'tenant_id', None)
             sub = Subscription.objects.filter(tenant_id=tenant_id).first()
             if sub:
                 sub.cancel()
                 messages.warning(request, "Subscription will be canceled at period end.")
                 
        return redirect('billing:portal')


# Revenue Dashboard Views
class RevenueOverviewView(BillingStaffMixin, TemplateView):
    template_name = 'billing/revenue_overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate MRR
        active_subs = Subscription.objects.filter(status='active').select_related('plan')
        mrr = sum(sub.plan.price_monthly for sub in active_subs)
        context['mrr'] = mrr
        
        # Calculate ARR
        context['arr'] = mrr * 12
        
        # Active subscriptions
        context['active_subscriptions'] = active_subs.count()
        
        # Trial subscriptions
        context['trial_subscriptions'] = Subscription.objects.filter(status='trialing').count()
        
        # Recent revenue (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        context['recent_revenue'] = Invoice.objects.filter(
            status='paid',
            paid_at__gte=thirty_days_ago
        ).aggregate(total=Sum('total'))['total'] or 0
        
        return context


class MRRAnalyticsView(BillingStaffMixin, TemplateView):
    template_name = 'billing/mrr_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # MRR breakdown by plan
        plans = Plan.objects.filter(is_active=True)
        mrr_by_plan = []
        
        for plan in plans:
            subs_count = Subscription.objects.filter(plan=plan, status='active').count()
            mrr = subs_count * float(plan.price_monthly)
            mrr_by_plan.append({
                'plan': plan,
                'subscribers': subs_count,
                'mrr': mrr
            })
        
        context['mrr_by_plan'] = mrr_by_plan
        context['total_mrr'] = sum(item['mrr'] for item in mrr_by_plan)
        
        return context


class ARRAnalyticsView(BillingStaffMixin, TemplateView):
    template_name = 'billing/arr_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate ARR
        active_subs = Subscription.objects.filter(status='active').select_related('plan')
        mrr = sum(sub.plan.price_monthly for sub in active_subs)
        context['arr'] = mrr * 12
        context['mrr'] = mrr
        
        return context


class ChurnRatesView(BillingStaffMixin, TemplateView):
    template_name = 'billing/churn_rates.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate churn (simplified)
        total_subs = Subscription.objects.count()
        canceled_subs = Subscription.objects.filter(status='canceled').count()
        
        if total_subs > 0:
            churn_rate = (canceled_subs / total_subs) * 100
        else:
            churn_rate = 0
            
        context['churn_rate'] = round(churn_rate, 2)
        context['total_subscriptions'] = total_subs
        context['canceled_subscriptions'] = canceled_subs
        
        return context


class RevenueForecastView(BillingStaffMixin, TemplateView):
    template_name = 'billing/revenue_forecast.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Simple forecast based on current MRR
        active_subs = Subscription.objects.filter(status='active').select_related('plan')
        current_mrr = sum(float(sub.plan.price_monthly) for sub in active_subs)
        
        # Project next 6 months (assuming 5% growth)
        forecasts = []
        for month in range(1, 7):
            projected_mrr = current_mrr * (1.05 ** month)
            forecasts.append({
                'month': month,
                'projected_mrr': round(projected_mrr, 2)
            })
        
        context['forecasts'] = forecasts
        context['current_mrr'] = current_mrr
        
        return context


# Invoice Management Views
class InvoiceListView(BillingStaffMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Invoice.objects.select_related('subscription').order_by('-created_at')
        
        # Apply filters
        form = InvoiceSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('tenant_id'):
                queryset = queryset.filter(tenant_id__icontains=form.cleaned_data['tenant_id'])
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(due_date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(due_date__lte=form.cleaned_data['date_to'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = InvoiceSearchForm(self.request.GET)
        return context


class PaidInvoicesView(BillingStaffMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_paid.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        return Invoice.objects.filter(status='paid').select_related('subscription').order_by('-paid_at')


class OverdueInvoicesView(BillingStaffMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_overdue.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        today = timezone.now().date()
        return Invoice.objects.filter(
            Q(status='open') | Q(status='overdue'),
            due_date__lt=today
        ).select_related('subscription').order_by('due_date')


class VoidInvoicesView(BillingStaffMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_void.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        return Invoice.objects.filter(status='void').select_related('subscription').order_by('-created_at')


class ReconciliationView(BillingStaffMixin, TemplateView):
    template_name = 'billing/reconciliation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Summary statistics
        context['total_invoices'] = Invoice.objects.count()
        context['paid_invoices'] = Invoice.objects.filter(status='paid').count()
        context['outstanding'] = Invoice.objects.filter(status__in=['open', 'overdue']).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        return context


# Invoice Detail and Actions
class InvoiceDetailView(BillingStaffMixin, TemplateView):
    template_name = 'billing/invoice_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_id = self.kwargs.get('invoice_id')
        context['invoice'] = get_object_or_404(
            Invoice.objects.select_related('subscription', 'subscription__plan').prefetch_related('line_items', 'payments'),
            id=invoice_id
        )
        return context


class InvoiceCreateView(BillingStaffMixin, TemplateView):
    template_name = 'billing/invoice_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = Subscription.objects.filter(status='active').select_related('plan')
        return context
    
    def post(self, request, *args, **kwargs):
        subscription_id = request.POST.get('subscription_id')
        subscription = get_object_or_404(Subscription, id=subscription_id)
        
        # Create invoice from subscription
        invoice = Invoice.create_from_subscription(subscription)
        invoice.finalize()  # Make it open
        
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
        return redirect('billing:invoice_detail', invoice_id=invoice.id)


class InvoiceMarkPaidView(BillingStaffMixin, View):
    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        try:
            invoice.mark_paid()
            messages.success(request, f'Invoice {invoice.invoice_number} marked as paid.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('billing:invoice_detail', invoice_id=invoice.id)


class InvoiceVoidView(BillingStaffMixin, View):
    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        try:
            invoice.void()
            messages.success(request, f'Invoice {invoice.invoice_number} voided.')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('billing:invoice_detail', invoice_id=invoice.id)


# Invoicing Engine Views
class InvoiceGenerationView(BillingStaffMixin, TemplateView):
    template_name = 'billing/invoice_generation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Active subscriptions that are due for invoicing (current_period_end has passed)
        now = timezone.now()
        subscriptions_due = Subscription.objects.filter(
            status='active',
            current_period_end__lte=now
        ).select_related('plan')
        
        context['subscriptions_needing_invoices'] = subscriptions_due
        context['subscriptions_count'] = subscriptions_due.count()
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Batch generate invoices for subscriptions with billing period ended
        now = timezone.now()
        subscriptions = Subscription.objects.filter(
            status='active',
            current_period_end__lte=now
        ).select_related('plan')
        
        generated = 0
        skipped = 0
        errors = []
        
        for subscription in subscriptions:
            try:
                # Check if invoice already exists for current period
                existing = Invoice.objects.filter(
                    subscription=subscription,
                    created_at__gte=subscription.current_period_start,
                    created_at__lte=subscription.current_period_end
                ).exists()
                
                if not existing:
                    Invoice.create_from_subscription(subscription)
                    generated += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append(f"{subscription.tenant_id}: {str(e)}")
        
        # Provide detailed feedback
        if generated > 0:
            messages.success(request, f'Generated {generated} invoice(s) successfully.')
        if skipped > 0:
            messages.info(request, f'Skipped {skipped} subscription(s) - invoices already exist.')
        if errors:
            messages.warning(request, f'Errors: {", ".join(errors[:3])}')
        
        return redirect('billing:invoice_generation')


class DunningManagementView(BillingStaffMixin, TemplateView):
    template_name = 'billing/dunning_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get overdue invoices
        today = timezone.now().date()
        overdue = Invoice.objects.filter(
            status='open',
            due_date__lt=today
        ).select_related('subscription').order_by('due_date')
        
        context['overdue_invoices'] = overdue
        context['total_overdue_amount'] = sum(inv.total for inv in overdue)
        
        return context
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        invoice_id = request.POST.get('invoice_id')
        
        if not invoice_id:
            messages.error(request, 'No invoice specified.')
            return redirect('billing:dunning_management')
        
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            
            if action == 'send_reminder':
                # Mock sending reminder email
                reminder_note = f"Payment reminder sent on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                invoice.notes = f"{invoice.notes}\n{reminder_note}" if invoice.notes else reminder_note
                invoice.save()
                messages.success(request, f'Reminder sent for invoice {invoice.invoice_number}')
                
            elif action == 'retry_payment':
                # Mock payment retry
                from decimal import Decimal
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.total,
                    status='pending',
                    payment_method='auto_retry'
                )
                
                # Simulate payment attempt (70% success rate for demo)
                import random
                if random.random() > 0.3:
                    payment.status = 'succeeded'
                    payment.save()
                    invoice.mark_paid()
                    messages.success(request, f'Payment retry successful for {invoice.invoice_number}!')
                else:
                    payment.status = 'failed'
                    payment.error_message = 'Insufficient funds / Card declined'
                    payment.save()
                    messages.warning(request, f'Payment retry failed for {invoice.invoice_number}.')
            else:
                messages.error(request, 'Invalid action.')
                
        except Invoice.DoesNotExist:
            messages.error(request, 'Invoice not found.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('billing:dunning_management')


class FailedPaymentsView(BillingStaffMixin, ListView):
    model = Payment
    template_name = 'billing/failed_payments.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        return Payment.objects.filter(status='failed').select_related('invoice').order_by('-created_at')
    
    def post(self, request, *args, **kwargs):
        payment_id = request.POST.get('payment_id')
        
        if not payment_id:
            messages.error(request, 'No payment specified.')
            return redirect('billing:failed_payments')
        
        try:
            payment = Payment.objects.get(id=payment_id, status='failed')
            invoice = payment.invoice
            
            # Create new payment attempt
            import random
            new_payment = Payment.objects.create(
                invoice=invoice,
                amount=payment.amount,
                status='pending',
                payment_method='retry'
            )
            
            # Simulate retry (60% success rate for demo)
            if random.random() > 0.4:
                new_payment.status = 'succeeded'
                new_payment.save()
                
                # Mark invoice as paid if total payments >= invoice total
                total_paid = sum(p.amount for p in invoice.payments.filter(status='succeeded'))
                if total_paid >= invoice.total:
                    invoice.mark_paid()
                    messages.success(request, f'Payment retry successful! Invoice {invoice.invoice_number} is now paid.')
                else:
                    messages.success(request, f'Partial payment successful (${new_payment.amount}).')
            else:
                new_payment.status = 'failed'
                new_payment.error_message = 'Payment declined - please update payment method'
                new_payment.save()
                messages.warning(request, 'Payment retry failed. Please check payment method.')
                
        except Payment.DoesNotExist:
            messages.error(request, 'Payment not found.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('billing:failed_payments')


# Subscription Plans Views
class PlanListView(BillingStaffMixin, ListView):
    model = Plan
    template_name = 'billing/plan_list.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        return Plan.objects.all().order_by('tier', 'price_monthly')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add subscriber counts for each plan
        plans_with_metrics = []
        for plan in context['plans']:
            active_subs = Subscription.objects.filter(plan=plan, status='active').count()
            trial_subs = Subscription.objects.filter(plan=plan, status='trialing').count()
            mrr = active_subs * float(plan.price_monthly)
            
            plans_with_metrics.append({
                'plan': plan,
                'active_subscribers': active_subs,
                'trial_subscribers': trial_subs,
                'monthly_revenue': mrr
            })
        
        context['plans_with_metrics'] = plans_with_metrics
        return context


class PlanDetailView(BillingStaffMixin, TemplateView):
    template_name = 'billing/plan_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        plan = get_object_or_404(Plan, id=plan_id)
        
        context['plan'] = plan
        
        # Get subscriptions for this plan
        context['active_subscriptions'] = Subscription.objects.filter(
            plan=plan, status='active'
        ).select_related('plan')
        
        context['trial_subscriptions'] = Subscription.objects.filter(
            plan=plan, status='trialing'
        ).select_related('plan')
        
        # Calculate metrics
        context['total_subscribers'] = Subscription.objects.filter(plan=plan).count()
        context['active_count'] = context['active_subscriptions'].count()
        context['trial_count'] = context['trial_subscriptions'].count()
        context['monthly_revenue'] = context['active_count'] * float(plan.price_monthly)
        context['annual_revenue'] = context['monthly_revenue'] * 12
        
        return context


class PlanCreateView(BillingStaffMixin, CreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_create.html'
    success_url = reverse_lazy('billing:plan_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Plan "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class PlanEditView(BillingStaffMixin, UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/plan_edit.html'
    pk_url_kwarg = 'plan_id'
    
    def get_success_url(self):
        return reverse_lazy('billing:plan_detail', kwargs={'plan_id': self.object.id})
    
    def form_valid(self, form):
        messages.success(self.request, f'Plan "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class PricingConfigView(BillingStaffMixin, UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'billing/pricing_config.html'
    success_url = reverse_lazy('billing:plan_list')
    pk_url_kwarg = 'plan_id'
    
    def form_valid(self, form):
        messages.success(self.request, 'Pricing updated successfully.')
        return super().form_valid(form)


class PlanLimitsView(BillingStaffMixin, TemplateView):
    template_name = 'billing/plan_limits.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.all()
        return context


class PlanToggleActiveView(BillingStaffMixin, View):
    """Toggle plan active status"""
    def post(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)
        plan.is_active = not plan.is_active
        plan.save()
        
        status = "activated" if plan.is_active else "deactivated"
        messages.success(request, f'Plan "{plan.name}" {status} successfully.')
        
        return redirect('billing:plan_detail', plan_id=plan.id)


# Subscription Management Views
class SubscriptionListView(BillingStaffMixin, ListView):
    model = Subscription
    template_name = 'billing/subscription_list.html'
    context_object_name = 'subscriptions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Subscription.objects.select_related('plan').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Search by tenant_id
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(tenant_id__icontains=search)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Subscription.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class SubscriptionDetailView(BillingStaffMixin, TemplateView):
    template_name = 'billing/subscription_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription_id = self.kwargs.get('subscription_id')
        context['subscription'] = get_object_or_404(
            Subscription.objects.select_related('plan').prefetch_related('invoices', 'adjustments'),
            id=subscription_id
        )
        context['all_plans'] = Plan.objects.filter(is_active=True).exclude(id=context['subscription'].plan.id)
        
        # Calculate proration for each plan
        prorations = {}
        for plan in context['all_plans']:
            prorations[plan.id] = context['subscription'].calculate_proration(plan)
        context['prorations'] = prorations
        
        return context


class UpgradeDowngradeView(BillingStaffMixin, TemplateView):
    template_name = 'billing/upgrade_downgrade.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = Subscription.objects.filter(status__in=['active', 'trialing']).select_related('plan')
        context['plans'] = Plan.objects.filter(is_active=True)
        return context
    
    def post(self, request, *args, **kwargs):
        subscription_id = request.POST.get('subscription_id')
        new_plan_id = request.POST.get('new_plan_id')
        
        subscription = get_object_or_404(Subscription, id=subscription_id)
        new_plan = get_object_or_404(Plan, id=new_plan_id)
        
        old_plan = subscription.plan
        proration = subscription.calculate_proration(new_plan)
        
        subscription.upgrade_to(new_plan)
        
        messages.success(
            request,
            f'Subscription upgraded from {old_plan.name} to {new_plan.name}. Proration: ${proration}'
        )
        return redirect('billing:subscription_detail', subscription_id=subscription.id)


class SubscriptionCancelView(BillingStaffMixin, View):
    def post(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, id=subscription_id)
        immediate = request.POST.get('immediate') == 'true'
        
        subscription.cancel(immediate=immediate)
        
        if immediate:
            messages.warning(request, f'Subscription for {subscription.tenant_id} canceled immediately.')
        else:
            messages.info(request, f'Subscription for {subscription.tenant_id} will cancel at period end.')
       
        return redirect('billing:subscription_detail', subscription_id=subscription.id)


class SubscriptionReactivateView(BillingStaffMixin, View):
    def post(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, id=subscription_id)
        
        try:
            subscription.reactivate()
            messages.success(request, f'Subscription for {subscription.tenant_id} reactivated successfully.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('billing:subscription_detail', subscription_id=subscription.id)


class ProrationCalculatorView(BillingStaffMixin, TemplateView):
    template_name = 'billing/proration_calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = Subscription.objects.filter(status__in=['active', 'trialing']).select_related('plan')
        context['plans'] = Plan.objects.filter(is_active=True)
        return context


class LifecycleEventsView(BillingStaffMixin, TemplateView):
    template_name = 'billing/lifecycle_events.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriptions'] = Subscription.objects.select_related('plan').order_by('-updated_at')[:20]
        return context


class RenewalTrackingView(BillingStaffMixin, TemplateView):
    template_name = 'billing/renewal_tracking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Subscriptions renewing in next 30 days
        thirty_days_from_now = timezone.now() + timedelta(days=30)
        context['upcoming_renewals'] = Subscription.objects.filter(
            status='active',
            current_period_end__lte=thirty_days_from_now
        ).select_related('plan').order_by('current_period_end')
        
        return context


class CancellationManagementView(BillingStaffMixin, TemplateView):
    template_name = 'billing/cancellation_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['canceled_subscriptions'] = Subscription.objects.filter(
            status='canceled'
        ).select_related('plan').order_by('-updated_at')
        context['pending_cancellations'] = Subscription.objects.filter(
            cancel_at_period_end=True
        ).select_related('plan')
        return context


# Tenant Billing Views
class TenantBillingSearchView(BillingStaffMixin, TemplateView):
    template_name = 'billing/tenant_billing_search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Provide plans for the filter dropdown
        context['plans'] = Plan.objects.filter(is_active=True)
        
        # Get search parameters
        tenant_id = self.request.GET.get('tenant_id')
        status = self.request.GET.get('status')
        plan_id = self.request.GET.get('plan')
        
        # Filter subscriptions based on search criteria
        subscriptions = Subscription.objects.select_related('plan')
        
        if tenant_id:
            subscriptions = subscriptions.filter(tenant_id__icontains=tenant_id)
        if status:
            subscriptions = subscriptions.filter(status=status)
        if plan_id:
            subscriptions = subscriptions.filter(plan_id=plan_id)
        
        # Only show results if at least one filter is applied
        if tenant_id or status or plan_id:
            context['subscriptions'] = subscriptions.order_by('-created_at')[:50]  # Limit to 50 results
        
        return context


class BillingHistoryView(BillingStaffMixin, TemplateView):
    template_name = 'billing/billing_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        tenant_id = self.kwargs.get('tenant_id')
        context['tenant_id'] = tenant_id
        context['invoices'] = Invoice.objects.filter(tenant_id=tenant_id).order_by('-created_at')
        context['payments'] = Payment.objects.filter(invoice__tenant_id=tenant_id).select_related('invoice').order_by('-created_at')
        
        return context


class CreditAdjustmentManagementView(BillingStaffMixin, FormView):
    template_name = 'billing/credit_adjustment.html'
    form_class = CreditAdjustmentForm
    success_url = reverse_lazy('billing:revenue_overview')
    
    def form_valid(self, form):
        adjustment = form.save(commit=False)
        adjustment.created_by = self.request.user
        adjustment.save()
        
        messages.success(self.request, f'{adjustment.adjustment_type.title()} of ${adjustment.amount} applied successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_adjustments'] = CreditAdjustment.objects.select_related('created_by').order_by('-created_at')[:10]
        return context


# ============================================================================
# Payment Provider Management Views (Three-Tier Architecture)
# ============================================================================

from .models import PaymentProviderConfig, TenantPaymentConfig, PaymentMethod
from .payment_providers import get_available_providers


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Restrict views to superusers only"""
    def test_func(self):
        return self.request.user.is_superuser


# --- Platform Level (Superadmin) ---

class PaymentGatewayListView(SuperuserRequiredMixin, ListView):
    """Superadmin view to manage payment provider configurations"""
    model = PaymentProviderConfig
    template_name = 'billing/payment_gateway_list.html'
    context_object_name = 'providers'
    
    def get_queryset(self):
        return PaymentProviderConfig.objects.all().order_by('name')


class PaymentGatewayConfigView(SuperuserRequiredMixin, UpdateView):
    """Superadmin view to configure a specific payment provider"""
    model = PaymentProviderConfig
    template_name = 'billing/payment_gateway_form.html'
    fields = ['display_name', 'is_active', 'config', 'supported_currencies', 
              'supports_subscriptions', 'supports_one_time', 'logo_url', 'description']
    success_url = reverse_lazy('billing:payment_gateway_list')
    pk_url_kwarg = 'provider_id'
    
    def form_valid(self, form):
        messages.success(self.request, f'Payment provider "{form.instance.display_name}" updated successfully.')
        return super().form_valid(form)


class PaymentGatewayCreateView(SuperuserRequiredMixin, CreateView):
    """Superadmin view to add a new payment provider"""
    model = PaymentProviderConfig
    template_name = 'billing/payment_gateway_form.html'
    fields = ['name', 'display_name', 'is_active', 'config', 'supported_currencies',
              'supports_subscriptions', 'supports_one_time', 'logo_url', 'description']
    success_url = reverse_lazy('billing:payment_gateway_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Payment provider "{form.instance.display_name}" created successfully.')
        return super().form_valid(form)


# --- Tenant Level (Tenant Admin) ---

class TenantPaymentConfigView(BillingStaffMixin, TemplateView):
    """Tenant admin view to configure which payment providers to use"""
    template_name = 'billing/tenant_payment_config.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Get all active platform providers
        platform_providers = PaymentProviderConfig.objects.filter(is_active=True)
        
        # Get tenant's current configurations
        tenant_configs = {
            tc.provider_id: tc
            for tc in TenantPaymentConfig.objects.filter(tenant_id=tenant_id).select_related('provider')
        }
        
        # Combine data
        providers_with_config = []
        for provider in platform_providers:
            tenant_config = tenant_configs.get(provider.id)
            providers_with_config.append({
                'provider': provider,
                'tenant_config': tenant_config,
                'is_enabled_for_subscription': tenant_config.is_enabled_for_subscription if tenant_config else False,
                'is_enabled_for_customers': tenant_config.is_enabled_for_customers if tenant_config else False,
            })
        
        context['providers'] = providers_with_config
        context['tenant_id'] = tenant_id
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle enabling/disabling providers"""
        tenant_id = getattr(request.user, 'tenant_id', None)
        provider_id = request.POST.get('provider_id')
        action = request.POST.get('action')
        
        try:
            provider = PaymentProviderConfig.objects.get(id=provider_id, is_active=True)
            tenant_config, created = TenantPaymentConfig.objects.get_or_create(
                tenant_id=tenant_id,
                provider=provider
            )
            
            if action == 'toggle_subscription':
                tenant_config.is_enabled_for_subscription = not tenant_config.is_enabled_for_subscription
                tenant_config.save()
                status = "enabled" if tenant_config.is_enabled_for_subscription else "disabled"
                messages.success(request, f'{provider.display_name} {status} for subscription billing.')
                
            elif action == 'toggle_customers':
                tenant_config.is_enabled_for_customers = not tenant_config.is_enabled_for_customers
                tenant_config.save()
                status = "enabled" if tenant_config.is_enabled_for_customers else "disabled"
                messages.success(request, f'{provider.display_name} {status} for customer checkout.')
                
        except PaymentProviderConfig.DoesNotExist:
            messages.error(request, 'Payment provider not found.')
        
        return redirect('billing:tenant_payment_config')


class PaymentMethodListView(LoginRequiredMixin, ListView):
    """View for tenant admin to manage their payment methods"""
    model = PaymentMethod
    template_name = 'billing/payment_method_list.html'
    context_object_name = 'payment_methods'
    
    def get_queryset(self):
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        return PaymentMethod.objects.filter(
            tenant_id=tenant_id,
            is_active=True
        ).select_related('provider').order_by('-is_default', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Get available providers for this tenant
        context['available_providers'] = get_available_providers(tenant_id=tenant_id)
        
        return context


class PaymentMethodCreateView(LoginRequiredMixin, TemplateView):
    """View to add a new payment method"""
    template_name = 'billing/payment_method_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Get available providers
        context['available_providers'] = get_available_providers(tenant_id=tenant_id)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle payment method creation"""
        tenant_id = getattr(request.user, 'tenant_id', None)
        provider_name = request.POST.get('provider')
        payment_type = request.POST.get('type')
        
        try:
            provider = PaymentProviderConfig.objects.get(name=provider_name, is_active=True)
            
            # In a real implementation, you would:
            # 1. Tokenize the payment method with the provider's SDK
            # 2. Store the token securely
            # For now, we'll create a mock payment method
            
            payment_method = PaymentMethod.objects.create(
                tenant_id=tenant_id,
                provider=provider,
                type=payment_type,
                display_info=request.POST.get('display_info', '**** ****'),
                provider_payment_method_id=f"pm_{provider_name}_{tenant_id}",
                is_default=not PaymentMethod.objects.filter(tenant_id=tenant_id).exists()
            )
            
            messages.success(request, f'Payment method added successfully.')
            return redirect('billing:payment_method_list')
            
        except PaymentProviderConfig.DoesNotExist:
            messages.error(request, 'Invalid payment provider.')
            return redirect('billing:payment_method_create')


class PaymentMethodDeleteView(LoginRequiredMixin, View):
    """Delete a payment method"""
    def post(self, request, method_id):
        tenant_id = getattr(request.user, 'tenant_id', None)
        
        try:
            payment_method = PaymentMethod.objects.get(
                id=method_id,
                tenant_id=tenant_id
            )
            payment_method.delete()
            messages.success(request, 'Payment method removed successfully.')
        except PaymentMethod.DoesNotExist:
            messages.error(request, 'Payment method not found.')
        
        return redirect('billing:payment_method_list')

