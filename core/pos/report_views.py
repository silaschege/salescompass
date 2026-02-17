from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncHour
from tenants.views import TenantAwareViewMixin
from .models import POSSession, POSTransaction, POSPayment, POSRefund

class XReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Mid-day summary report (non-resetting)."""
    template_name = 'pos/report_x.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get current active session for the user
        session = POSSession.objects.filter(
            cashier=self.request.user, 
            status='active'
        ).select_related('terminal').first()
        
        if not session:
            context['no_session'] = True
            return context
            
        context['session'] = session
        context['report_date'] = timezone.now()
        
        # Transactions in this session
        transactions = POSTransaction.objects.filter(
            session=session,
            status='completed'
        )
        
        # Summaries
        context['total_sales'] = transactions.aggregate(t=Sum('total_amount'))['t'] or 0
        context['transaction_count'] = transactions.count()
        context['total_tax'] = transactions.aggregate(t=Sum('tax_amount'))['t'] or 0
        context['total_discount'] = transactions.aggregate(t=Sum('discount_amount'))['t'] or 0
        
        # Breakdowns
        context['payment_methods'] = POSPayment.objects.filter(
            transaction__session=session,
            status='completed'
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Hourly breakdown
        context['hourly_sales'] = transactions.annotate(
            hour=TruncHour('completed_at')
        ).values('hour').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('hour')
        
        return context


class ZReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """End-of-day report (resets counters)."""
    template_name = 'pos/report_z.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # For Z-Report, we might look at the most recently CLOSED session 
        # OR the current active session if we are about to close it.
        # Let's show the current active session as a "Preview" or the last closed one.
        # Typically Z-Report is printed AT CLOSING.
        
        # Let's prefer the active session to show what will be closed.
        session = POSSession.objects.filter(
            cashier=self.request.user,
            status='active'
        ).select_related('terminal').first()
        
        if not session:
            # Fallback to last closed session for re-printing
            session = POSSession.objects.filter(
                cashier=self.request.user,
                status='closed'
            ).order_by('-closed_at').first()
            
        if not session:
             context['no_session'] = True
             return context

        context['session'] = session
        context['report_type'] = 'Z-Report'
        context['generated_at'] = timezone.now()
        
        transactions = POSTransaction.objects.filter(session=session)
        completed_txns = transactions.filter(status='completed')
        
        # Financials
        context['net_sales'] = completed_txns.aggregate(t=Sum('total_amount'))['t'] or 0 - (completed_txns.aggregate(t=Sum('tax_amount'))['t'] or 0)
        context['tax_collected'] = completed_txns.aggregate(t=Sum('tax_amount'))['t'] or 0
        context['gross_sales'] = completed_txns.aggregate(t=Sum('total_amount'))['t'] or 0
        
        # Returns/Voids
        context['voids_count'] = transactions.filter(status='voided').count()
        context['returns_count'] = POSRefund.objects.filter(original_transaction__session=session).count()
        context['total_returns'] = POSRefund.objects.filter(original_transaction__session=session).aggregate(t=Sum('refund_amount'))['t'] or 0
        
        # Payments
        context['payment_methods'] = POSPayment.objects.filter(
            transaction__session=session,
            status='completed'
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Cash Reconciliation (if closed)
        if session.status == 'closed':
            context['expected_cash'] = session.expected_cash
            context['actual_cash'] = session.closing_cash
            context['variance'] = session.cash_difference
            
        return context
