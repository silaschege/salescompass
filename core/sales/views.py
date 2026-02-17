from django.shortcuts import render, get_object_or_404, redirect
from core.models import User as  Account
from django import forms
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from core.permissions import ObjectPermissionRequiredMixin
from django.urls import reverse_lazy
from .models import Sale, Product, SalesCommission, SalesCommissionRule, TerritoryPerformance, TerritoryAssignmentOptimizer, TeamMemberTerritoryMetrics
from django.db.models import Count, Avg, Sum
from core.utils import get_queryset_for_user
from tenants.models import TenantMember, TenantTerritory
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q


# List View

class SaleListView(ObjectPermissionRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    ordering = ['-sale_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Optimize query by selecting related fields that are used in the template
        return queryset.select_related('account', 'product', 'sales_rep')


# Detail View
class SaleDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'

# Create View


class SaleCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Sale
    fields = ['account', 'sale_type', 'product', 'amount']
    template_name = 'sales/sale_form.html'
    permission_action = 'change'

    def form_valid(self, form):
        account = form.instance.account
        account_name = account.account_name
        messages.success(self.request, f"Sale recorded for {account_name}!")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('sales:sale_detail', kwargs={'pk': self.object.pk})


# Update View
class SaleUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Sale
    fields = ['account', 'sale_type', 'product', 'amount']
    template_name = 'sales/sale_form.html'
    permission_action = 'change'

    def form_valid(self, form):
        messages.success(self.request, "Sale updated!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sales:sale_detail', kwargs={'pk': self.object.pk})

class SalesDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'sales/sale_dashboard.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales = get_queryset_for_user(self.request.user, Sale).select_related('account')
        
        # KPIs
        context['total_revenue'] = sales.aggregate(total=Sum('amount'))['total'] or 0
        context['total_sales'] = sales.count()
        context['avg_deal_size'] = sales.aggregate(avg=Avg('amount'))['avg'] or 0
        
        # IFRS 15 Glimpse
        from .models_contract import PerformanceObligation
        tenant = self.request.user.tenant
        context['unearned_revenue'] = PerformanceObligation.objects.filter(tenant=tenant).exclude(status='fulfilled').aggregate(total=Sum('allocated_amount'))['total'] or 0
        
        # Sales by Type
        sales_by_type = dict(sales.values_list('sale_type').annotate(count=Count('id')))
        type_labels = {'hardware': 'Hardware', 'ship': 'Shipment', 'software': 'Software'}
        context['sales_by_type'] = {type_labels.get(k, k): v for k, v in sales_by_type.items()}

        # Recent Sales
        context['recent_sales'] = sales.order_by('-sale_date')[:10]
        return context

class RevenueDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'sales/dashboard_revenue.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models_contract import PerformanceObligation, RevenueSchedule
        tenant = self.request.user.tenant
        
        obligations = PerformanceObligation.objects.filter(tenant=tenant).select_related('contract')
        
        context['unearned_revenue'] = obligations.exclude(status='fulfilled').aggregate(total=Sum('allocated_amount'))['total'] or 0
        context['mtd_recognized'] = RevenueSchedule.objects.filter(
            tenant=tenant, is_recognized=True, date__month=timezone.now().month, date__year=timezone.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['contract_assets'] = 0 # Placeholder for unbilled recognition
        
        # Obligations for table
        pending = obligations.exclude(status='fulfilled').order_by('-created_at')[:10]
        for ob in pending:
            ob.progress_percent = int((ob.recognized_amount / ob.allocated_amount * 100)) if ob.allocated_amount > 0 else 0
            
        context['pending_obligations'] = pending
        return context



# Commission Views
def commission_dashboard(request):
    """
    Dashboard for sales commissions.
    """
    user = request.user
    
    # Base queryset
    commissions = SalesCommission.objects.select_related('sale', 'sales_rep', 'rule_applied')
    
    # If not admin/manager, only see own commissions
    if not user.is_staff and not user.has_perm('sales.view_all_commissions'):
        commissions = commissions.filter(sales_rep=user)
    
    # KPIs
    total_earned = commissions.aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = commissions.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    paid_amount = commissions.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent commissions
    recent_commissions = commissions.order_by('-date_earned')[:10]
    
    # Top earners (admin only)
    top_earners = []
    if user.is_staff:
        top_earners = SalesCommission.objects.values('sales_rep__email').annotate(
            total=Sum('amount')
        ).order_by('-total')[:5]

    context = {
        'total_earned': total_earned,
        'pending_amount': pending_amount,
        'paid_amount': paid_amount,
        'recent_commissions': recent_commissions,
        'top_earners': top_earners,
        'is_admin': user.is_staff
    }
    return render(request, 'sales/commission_dashboard.html', context)

# Commission Rule Views
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin

class CommissionRuleListView(PermissionRequiredMixin, ListView):
    model = SalesCommissionRule
    template_name = 'sales/commission_rule_list.html'
    context_object_name = 'rules'
    permission_required = 'sales.view_commissionrule'

class CommissionRuleCreateView(PermissionRequiredMixin, CreateView):
    model = SalesCommissionRule
    fields = ['name', 'product_type', 'specific_product', 'percentage', 'flat_amount', 'min_sales_amount', 'start_date', 'end_date', 'is_active']
    template_name = 'sales/commission_rule_form.html'
    success_url = reverse_lazy('sales:rule_list')
    permission_required = 'sales.add_commissionrule'

    def form_valid(self, form):
        messages.success(self.request, "Commission rule created!")
        return super().form_valid(form)

class CommissionRuleUpdateView(PermissionRequiredMixin, UpdateView):
    model = SalesCommissionRule
    fields = ['name', 'product_type', 'specific_product', 'percentage', 'flat_amount', 'min_sales_amount', 'start_date', 'end_date', 'is_active']
    template_name = 'sales/commission_rule_form.html'
    success_url = reverse_lazy('sales:rule_list')
    permission_required = 'sales.change_commissionrule'

    def form_valid(self, form):
        messages.success(self.request, "Commission rule updated!")
        return super().form_valid(form)

class CommissionRuleDeleteView(PermissionRequiredMixin, DeleteView):
    model = SalesCommissionRule
    template_name = 'sales/commission_rule_confirm_delete.html'
    success_url = reverse_lazy('sales:rule_list')
    permission_required = 'sales.delete_commissionrule'


# Territory Performance Dashboard Views
def territory_performance_dashboard(request):
    """
    Dashboard for territory performance metrics
    """
    user = request.user
    
    # Get all territories for the tenant
    territories = TenantTerritory.objects.filter(tenant_id=user.tenant_id)
    
    # Get latest performance data for each territory
    territory_data = []
    for territory in territories:
        try:
            latest_performance = territory.performance_metrics.latest('period_end')
            territory_data.append({
                'territory': territory,
                'performance': latest_performance,
            })
        except TerritoryPerformance.DoesNotExist:
            territory_data.append({
                'territory': territory,
                'performance': None,
            })
    
    # Calculate overall KPIs
    total_revenue = sum(
        td['performance'].total_revenue if td['performance'] else 0 
        for td in territory_data
    )
    total_deals = sum(
        td['performance'].total_deals if td['performance'] else 0 
        for td in territory_data
    )
    avg_conversion_rate = sum(
        td['performance'].conversion_rate if td['performance'] else 0 
        for td in territory_data
    ) / len([td for td in territory_data if td['performance']]) if len([td for td in territory_data if td['performance']]) > 0 else 0
    
    context = {
        'territory_data': territory_data,
        'total_revenue': total_revenue,
        'total_deals': total_deals,
        'avg_conversion_rate': avg_conversion_rate,
    }
    
    return render(request, 'sales/territory_performance_dashboard.html', context)


def territory_assignment_optimization_dashboard(request):
    """
    Dashboard for territory assignment optimization
    """
    user = request.user
    
    # Get all optimization records for territories in the tenant
    optimizations = TerritoryAssignmentOptimizer.objects.filter(
        territory__tenant_id=user.tenant_id
    ).select_related('territory').order_by('-optimization_date')
    
    # Get latest optimization for each territory
    territory_optimizations = {}
    for opt in optimizations:
        if opt.territory not in territory_optimizations:
            territory_optimizations[opt.territory] = opt
    
    context = {
        'optimizations': list(territory_optimizations.values()),
    }
    
    return render(request, 'sales/territory_assignment_optimization_dashboard.html', context)


def run_territory_optimization(request, territory_id):
    """
    Run territory assignment optimization for a specific territory
    """
    territory = get_object_or_404(TenantTerritory, id=territory_id, tenant_id=request.user.tenant_id)
    
    # Create a new optimization record
    optimizer = TerritoryAssignmentOptimizer.objects.create(
        territory=territory,
        optimization_type=request.GET.get('type', 'load_balancing')
    )
    
    # Run the optimization
    optimizer.run_optimization()
    
    messages.success(request, f"Territory optimization completed for {territory.label}")
    return redirect('sales:territory_assignment_optimization_dashboard')


def territory_comparison_tool(request):
    """
    Tool for comparing territory performance
    """
    user = request.user
    
    # Get territories and their latest performance data
    territories = TenantTerritory.objects.filter(tenant_id=user.tenant_id)
    territory_comparison_data = []
    
    for territory in territories:
        try:
            latest_performance = territory.performance_metrics.latest('period_end')
            territory_comparison_data.append({
                'territory': territory,
                'performance': latest_performance,
            })
        except TerritoryPerformance.DoesNotExist:
            territory_comparison_data.append({
                'territory': territory,
                'performance': None,
            })
    
    # Prepare data for comparison chart
    chart_data = {
        'labels': [td['territory'].name for td in territory_comparison_data if td['performance']],
        'revenue_data': [float(td['performance'].total_revenue) if td['performance'] else 0 for td in territory_comparison_data],
        'deal_data': [td['performance'].total_deals if td['performance'] else 0 for td in territory_comparison_data],
        'conversion_data': [float(td['performance'].conversion_rate) if td['performance'] else 0 for td in territory_comparison_data],
    }
    
    context = {
        'territory_comparison_data': territory_comparison_data,
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder),
    }
    
    return render(request, 'sales/territory_comparison_tool.html', context)


def territory_performance_api(request):
    """
    API endpoint for territory performance data
    """
    user = request.user
    
    # Get territories and their latest performance data
    territories = TenantTerritory.objects.filter(tenant_id=user.tenant_id)
    data = []
    
    for territory in territories:
        try:
            latest_performance = territory.performance_metrics.latest('period_end')
            data.append({
                'id': territory.id,
                'name': territory.name,
                'total_revenue': float(latest_performance.total_revenue),
                'total_deals': latest_performance.total_deals,
                'conversion_rate': float(latest_performance.conversion_rate),
                'opportunity_win_rate': float(latest_performance.opportunity_win_rate),
            })
        except TerritoryPerformance.DoesNotExist:
            data.append({
                'id': territory.id,
                'name': territory.name,
                'total_revenue': 0,
                'total_deals': 0,
                'conversion_rate': 0,
                'opportunity_win_rate': 0,
            })
    
    return JsonResponse({'territories': data})
