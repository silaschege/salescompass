from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, LoyaltyTier
from .forms import LoyaltyProgramForm, PointsAdjustmentForm

class LoyaltyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'loyalty/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        context['total_members'] = CustomerLoyalty.objects.filter(tenant=tenant).count()
        context['total_points'] = CustomerLoyalty.objects.filter(tenant=tenant).aggregate(s=Sum('points_balance'))['s'] or 0
        
        # New members this month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['new_members'] = CustomerLoyalty.objects.filter(tenant=tenant, created_at__gte=start_of_month).count()
        
        # IFRS Analytics
        context['total_liability'] = LoyaltyTransaction.objects.filter(
            tenant=tenant,
            transaction_type='earn',
            is_expired=False
        ).aggregate(s=Sum('allocated_revenue'))['s'] or 0
        
        # Breakage Prediction (Expiring in 30 days)
        limit_date = now.date() + timezone.timedelta(days=30)
        context['expiring_soon_points'] = LoyaltyTransaction.objects.filter(
            tenant=tenant,
            transaction_type='earn',
            is_expired=False,
            expiry_date__lte=limit_date
        ).aggregate(s=Sum('points'))['s'] or 0
        
        # Recent activity for feed
        context['recent_transactions'] = LoyaltyTransaction.objects.filter(tenant=tenant).select_related('loyalty_account__customer')[:5]
        
        return context

class LoyaltyProgramListView(SalesCompassListView):
    """
    List of loyalty programs.
    """
    model = LoyaltyProgram
    template_name = 'loyalty/program_list.html'
    context_object_name = 'programs'

class LoyaltyProgramView(SalesCompassUpdateView):
    """
    Singleton-style view for managing the tenant's program.
    If none exists, it creates one.
    """
    model = LoyaltyProgram
    form_class = LoyaltyProgramForm
    template_name = 'loyalty/program_form.html'
    success_url = reverse_lazy('loyalty:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.tenant:
            messages.error(request, "You must be associated with a tenant to manage loyalty programs.")
            return redirect('core:app_selection')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        tenant = self.request.user.tenant
        obj, created = LoyaltyProgram.objects.get_or_create(
            tenant=tenant,
            defaults={'program_name': f"{tenant.name} Rewards"}
        )
        return obj
        
    def form_valid(self, form):
        messages.success(self.request, "Loyalty program settings updated.")
        return super().form_valid(form)

class MemberListView(SalesCompassListView):
    model = CustomerLoyalty
    template_name = 'loyalty/member_list.html'
    context_object_name = 'members'

class MemberDetailView(SalesCompassDetailView):
    model = CustomerLoyalty
    template_name = 'loyalty/member_detail.html'
    context_object_name = 'member'

class PointsAdjustmentView(SalesCompassCreateView):
    model = LoyaltyTransaction
    form_class = PointsAdjustmentForm
    template_name = 'loyalty/adjust_points.html'
    
    def get_initial(self):
        member = get_object_or_404(CustomerLoyalty, pk=self.kwargs['pk'])
        return {'loyalty_account': member}

    def form_valid(self, form):
        member = get_object_or_404(CustomerLoyalty, pk=self.kwargs['pk'])
        form.instance.loyalty_account = member
        form.instance.processed_by = self.request.user
        form.instance.tenant = self.request.user.tenant
        form.instance.transaction_type = 'adjust'
        response = super().form_valid(form)
        messages.success(self.request, "Points adjusted successfully.")
        return response
        
    def get_success_url(self):
        return reverse_lazy('loyalty:member_detail', kwargs={'pk': self.kwargs['pk']})

class LoyaltyTransactionListView(SalesCompassListView):
    """
    View to list all loyalty transactions for the tenant.
    """
    model = LoyaltyTransaction
    template_name = 'loyalty/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        return super().get_queryset().select_related('loyalty_account__customer', 'processed_by').order_by('-created_at')

class TierRulesListView(SalesCompassListView):
    """
    View to manage loyalty tiers.
    """
    model = LoyaltyTier
    template_name = 'loyalty/tier_rules.html'
    context_object_name = 'tiers'
    
    def get_queryset(self):
        return super().get_queryset().order_by('level')


