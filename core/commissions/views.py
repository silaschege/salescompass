from django.views import generic
from django.views.generic import ListView, TemplateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .models import Commission, CommissionPayment
from .utils import get_user_performance, calculate_forecast

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'commissions/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Determine current period (Monthly default)
        start_of_month = today.replace(day=1)
        # Simple end of month calc
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timezone.timedelta(days=1)
            
        performance = get_user_performance(user, start_of_month, end_of_month)
        forecast = calculate_forecast(user, start_of_month, end_of_month)
        
        context['performance'] = performance
        context['forecast'] = forecast
        context['recent_commissions'] = Commission.objects.filter(user=user).order_by('-date_earned')[:5]
        context['period_start'] = start_of_month
        context['period_end'] = end_of_month
        
        return context

class CommissionListView(LoginRequiredMixin, ListView):
    model = Commission
    template_name = 'commissions/commission_list.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        return Commission.objects.filter(user=self.request.user).order_by('-date_earned')

class CommissionPaymentListView(LoginRequiredMixin, ListView):
    model = CommissionPayment
    template_name = 'commissions/payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return CommissionPayment.objects.filter(user=self.request.user).order_by('-period_end')

class CommissionPaymentDetailView(LoginRequiredMixin, generic.DetailView):
    model = CommissionPayment
    template_name = 'commissions/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        # Ensure user can only see their own payments (or add admin logic later)
        return CommissionPayment.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        payment = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve' and payment.status == 'calculated':
            payment.status = 'approved'
            payment.save()
        elif action == 'process' and payment.status == 'approved':
             payment.status = 'processing'
             payment.save()
        elif action == 'pay' and payment.status == 'processing':
            payment.status = 'paid'
            payment.paid_date = timezone.now().date()
            payment.save()
            # Also update related commissions to 'paid'
            payment.commissions.update(status='paid')
            
        return redirect('commissions:payment_detail', pk=payment.pk)
