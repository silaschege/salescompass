from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import Account
from django import forms
from django.contrib import messages
from .models import Sale, Product, Commission, CommissionRule
from django.db.models import Count, Avg, Sum
from core.utils import get_queryset_for_user

# List View
def sale_list(request):
    sales = get_queryset_for_user(request.user, Sale).select_related('account').order_by('-sale_date')
    return render(request, 'sales/sales_list.html', {'sales': sales})

# Detail View
def sale_detail(request, pk):
    sale = get_object_or_404(get_queryset_for_user(request.user, Sale), pk=pk)
    return render(request, 'sales/sales_detail.html', {'sale': sale})

# Create View
def sale_create(request):
    if request.method == 'POST':
        account_id = request.POST.get('account')
        sale_type = request.POST.get('sale_type')
        product_id = request.POST.get('product')
        amount = request.POST.get('amount')
      
        sale = Sale.objects.create(
            account_id=account_id,
            sale_type=sale_type,
            product_id=product_id,
            amount=amount,
        )
        messages.success(request, f"Sale recorded for {sale.account.name}!")
        return redirect('sales:sale_detail', pk=sale.pk)
    
    accounts = get_queryset_for_user(request.user, Account).filter(status='active')
    products = get_queryset_for_user(request.user, Product).filter(is_active=True)
  
    return render(request, 'sales/sales_form.html', {
        'accounts': accounts,
        'products': products,
        'sale_types': Sale.SALE_TYPE_CHOICES
    })

# Update View
def sale_update(request, pk):
    sale = get_object_or_404(get_queryset_for_user(request.user, Sale), pk=pk)
    if request.method == 'POST':
        sale.account_id = request.POST.get('account')
        sale.sale_type = request.POST.get('sale_type')
        sale.product_id = request.POST.get('product')
        sale.amount = request.POST.get('amount')
        sale.save()
        messages.success(request, "Sale updated!")
        return redirect('sales:sale_detail', pk=sale.pk)
    
    accounts = get_queryset_for_user(request.user, Account).filter(status='active')
    products = get_queryset_for_user(request.user, Product).filter(is_active=True)
    
    return render(request, 'sales/sales_form.html', {
        'sale': sale,
        'accounts': accounts,
        'products': products,
        'sale_types': Sale.SALE_TYPE_CHOICES
    })

def sales_dashboard(request):
    sales = get_queryset_for_user(request.user, Sale).select_related('account')
    
    # KPIs
    total_revenue = sales.aggregate(total=Sum('amount'))['total'] or 0
    total_sales = sales.count()
    avg_deal_size = sales.aggregate(avg=Avg('amount'))['avg'] or 0
    
    # Sales by Type
    sales_by_type = dict(sales.values_list('sale_type').annotate(count=Count('id')))
    # Humanize type names
    type_labels = {'hardware': 'Hardware', 'ship': 'Shipment', 'software': 'Software'}
    sales_by_type = {type_labels.get(k, k): v for k, v in sales_by_type.items()}

    # Top Accounts by Revenue
    top_accounts = sales.values('account__name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    top_accounts_data = {item['account__name']: item['total'] for item in top_accounts}

    # Recent Sales
    recent_sales = sales.order_by('-sale_date')[:10]

    context = {
        'total_revenue': total_revenue,
        'total_sales': total_sales,
        'avg_deal_size': avg_deal_size,
        'sales_by_type': sales_by_type,
        'top_accounts': top_accounts_data,
        'recent_sales': recent_sales,
    }
    return render(request, 'sales/sales_dashboard.html', context)

def product_list(request):
    products = get_queryset_for_user(request.user, Product).order_by('-created_at')
    return render(request, 'product/product_list.html', {'products': products})

def product_create(request):
    if request.method == 'POST':
        Product.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            product_type=request.POST['product_type'],
            price=request.POST['price'],
            is_active='is_active' in request.POST
        )
        messages.success(request, "Product added!")
        return redirect('sales:product_list')
    return render(request, 'product/product_form.html', {
        'product_types': Product.PRODUCT_TYPE_CHOICES
    })

def product_update(request, pk):
    product = get_object_or_404(get_queryset_for_user(request.user, Product), pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST.get('description', '')
        product.product_type = request.POST['product_type']
        product.price = request.POST['price']
        product.is_active = 'is_active' in request.POST
        product.save()
        messages.success(request, "Product updated!")
        return redirect('sales:product_list')
    return render(request, 'product/product_form.html', {
        'product': product,
        'product_types': Product.PRODUCT_TYPE_CHOICES
    })

def product_dashboard(request):
    # Active products
    products = get_queryset_for_user(request.user, Product).filter(is_active=True)
    total_products = products.count()
    avg_price = products.aggregate(avg=Avg('price'))['avg'] or 0

    # Sales data
    sales = get_queryset_for_user(request.user, Sale).select_related('account')
    total_revenue = sales.aggregate(total=Sum('amount'))['total'] or 0

    # Top product
    top_product = sales.values('product__name').annotate(count=Count('id')).order_by('-count').first()
    top_product_name = top_product['product__name'] if top_product else None

    # Sales by Type (Hardware, Shipment, Software)
    type_labels = {'hardware': 'Hardware', 'ship': 'Shipment', 'software': 'Software'}
    sales_by_type = {}
    for key, label in type_labels.items():
        rev = sales.filter(sale_type=key).aggregate(r=Sum('amount'))['r'] or 0
        cnt = sales.filter(sale_type=key).count()
        sales_by_type[label] = {'sales': cnt, 'revenue': rev}

    # Recent sales
    recent_sales = sales.order_by('-sale_date')[:10]

    context = {
        'total_products': total_products,
        'total_revenue': total_revenue,
        'avg_price': avg_price,
        'top_product_name': top_product_name,
        'sales_by_type': sales_by_type,
        'recent_sales': recent_sales,
    }
    return render(request, 'product/product_dashboard.html', context)

# Commission Views
def commission_dashboard(request):
    """
    Dashboard for sales commissions.
    """
    user = request.user
    
    # Base queryset
    commissions = Commission.objects.select_related('sale', 'sales_rep', 'rule_applied')
    
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
        top_earners = Commission.objects.values('sales_rep__email').annotate(
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
    model = CommissionRule
    template_name = 'sales/commission_rule_list.html'
    context_object_name = 'rules'
    permission_required = 'sales.view_commissionrule'

class CommissionRuleCreateView(PermissionRequiredMixin, CreateView):
    model = CommissionRule
    fields = ['name', 'product_type', 'specific_product', 'percentage', 'flat_amount', 'min_sales_amount', 'start_date', 'end_date', 'is_active']
    template_name = 'sales/commission_rule_form.html'
    success_url = reverse_lazy('sales:rule_list')
    permission_required = 'sales.add_commissionrule'

    def form_valid(self, form):
        messages.success(self.request, "Commission rule created!")
        return super().form_valid(form)

class CommissionRuleUpdateView(PermissionRequiredMixin, UpdateView):
    model = CommissionRule
    fields = ['name', 'product_type', 'specific_product', 'percentage', 'flat_amount', 'min_sales_amount', 'start_date', 'end_date', 'is_active']
    template_name = 'sales/commission_rule_form.html'
    success_url = reverse_lazy('sales:rule_list')
    permission_required = 'sales.change_commissionrule'

    def form_valid(self, form):
        messages.success(self.request, "Commission rule updated!")
        return super().form_valid(form)

class CommissionRuleDeleteView(PermissionRequiredMixin, DeleteView):
    model = CommissionRule
    template_name = 'sales/commission_rule_confirm_delete.html'
    success_url = reverse_lazy('sales:rule_list')
    permission_required = 'sales.delete_commissionrule'