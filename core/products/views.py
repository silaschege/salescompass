from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from core.permissions import ObjectPermissionRequiredMixin
from .models import (
    Product, ProductCategory, ProductBundle, CompetitorProduct, 
    ProductComparison, ProductDependency, PriceList, PriceListItem,
    Coupon, Promotion, Supplier
)
from .models import PricingTier # Import this as well since it is used in logic
from .forms import (
    ProductForm, ProductCategoryForm, CompetitorProductForm, 
    ProductDependencyForm, ProductBundleForm, ProductComparisonForm,
    PriceListForm, PriceListItemForm, CouponForm, PromotionForm, SupplierForm
)
from django.utils.text import slugify
from .utils import generate_sku, get_product_price
from .services import BarcodeService
from django.views import View
from django.http import HttpResponse

from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from inventory.models import StockLevel, Warehouse
from inventory.services_valuation import ValuationService
from decimal import Decimal

from django.utils import timezone
from datetime import timedelta

class ProductGovernanceDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'products/dashboard_governance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        today = timezone.now().date()
        
        # 1. Financial Overview & Inventory Aging (IAS 2)
        stocks = StockLevel.objects.filter(tenant=tenant)
        total_val = Decimal('0')
        aging_buckets = [Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0')] # 0-30, 31-60, 61-90, 90+
        
        category_map = {}
        risk_batches = []
        total_risk_amt = Decimal('0')

        for s in stocks:
            val = s.quantity * (s.cost_price or 0)
            total_val += val
            
            # Aging
            if s.acquisition_date:
                days_old = (today - s.acquisition_date).days
                if days_old <= 30: aging_buckets[0] += val
                elif days_old <= 60: aging_buckets[1] += val
                elif days_old <= 90: aging_buckets[2] += val
                else: aging_buckets[3] += val
            else:
                aging_buckets[0] += val # Assume new if no date
            
            # Category Distribution
            cat_name = s.product.category.name if s.product.category else "Uncategorized"
            category_map[cat_name] = category_map.get(cat_name, Decimal('0')) + val
            
            # NRV Impairment Risk
            if s.product.nrv and s.cost_price > s.product.nrv:
                variance = s.cost_price - s.product.nrv
                risk_batches.append({
                    'product': s.product,
                    'batch_number': s.batch_number,
                    'cost_price': s.cost_price,
                    'nrv': s.product.nrv,
                    'variance': variance * s.quantity
                })
                total_risk_amt += (variance * s.quantity)

        # 2. Compliance Score Calculation
        # Score starts at 100, drops based on impairment percentage of total value
        impairment_ratio = (total_risk_amt / total_val * 100) if total_val > 0 else 0
        compliance_score = max(0, 100 - (impairment_ratio * 2)) # Weighted penalty

        # 3. Format Category Data for Charts
        category_distribution = [{'name': k, 'value': float(v)} for k, v in category_map.items()]

        context.update({
            'total_inventory_value': total_val,
            'total_impairment_risk': total_risk_amt,
            'impairment_count': len(risk_batches),
            'avg_stock_age': 32, # Calculated if needed, or keeping mock
            'compliance_score': round(compliance_score, 1),
            'risk_batches': sorted(risk_batches, key=lambda x: x['variance'], reverse=True)[:10],
            'aging_data': [float(x) for x in aging_buckets],
            'category_distribution': category_distribution,
            'valuation_flux': [
                {'name': 'Raw Materials (Steel)', 'change': -1.2, 'progress': 75},
                {'name': 'Finished Goods (Inventory)', 'change': 2.4, 'progress': 85},
                {'name': 'Market Price (Global)', 'change': 0.8, 'progress': 90},
            ]
        })
        return context


class ProductListView(ObjectPermissionRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(is_active=True, parent=None)
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset.filter(product_is_active=True)


class ProductDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Get pricing info
        pricing_info = {
            1: get_product_price(product.id, 1),
            10: get_product_price(product.id, 10),
            100: get_product_price(product.id, 100),
        }
        context['pricing_info'] = pricing_info
        
        # Get bundles containing this product
        context['bundles'] = ProductBundle.objects.filter(
            products=product,
            is_active=True
        )
        
        # Get competitor mappings
        context['competitors'] = CompetitorProduct.objects.filter(
            our_product=product
        )
        
        return context


class ProductCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Generate SKU suggestion
        name = self.request.GET.get('name', '')
        category = self.request.GET.get('category', '')
        if name:
            initial['sku'] = generate_sku(name, category)
        return initial

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f"Product '{form.instance.product_name}' created!")
        return super().form_valid(form)


class ProductUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Product '{form.instance.product_name}' updated!")
        return super().form_valid(form)


# === Category Views ===

class ProductCategoryListView(ObjectPermissionRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # Get root categories (no parent) for the current tenant
        root_categories = ProductCategory.objects.filter(
            parent=None, 
            tenant=self.request.user.tenant
        ).prefetch_related('children')
        
        # Sort by display order or name
        return root_categories.order_by('display_order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add additional context data if needed
        context['all_categories_count'] = ProductCategory.objects.filter(
            tenant=self.request.user.tenant
        ).count()
        return context
class ProductCategoryCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')

    def form_valid(self, form):
        if not form.instance.slug:
            form.instance.slug = slugify(form.instance.name)
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f"Category '{form.instance.name}' created.")
        return super().form_valid(form)


class ProductCategoryUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')

    def form_valid(self, form):
        if not form.instance.slug:
            form.instance.slug = slugify(form.instance.name)
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, f"Category '{form.instance.name}' updated.")
        return super().form_valid(form)

class ProductCategoryDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = 'products/category_confirm_delete.html'
    success_url = reverse_lazy('products:category_list')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(request, f"Category '{category.name}' deleted.")
        return super().delete(request, *args, **kwargs)

class ProductDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:product_list')

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        messages.success(request, f"Product '{product.name}' deleted.")
        return super().delete(request, *args, **kwargs)


# === Competitor Mapping View ===
class CompetitorMappingView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'products/competitor_mapping.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.request.GET.get('product_id')
        
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            context['product'] = product
            context['competitors'] = CompetitorProduct.objects.filter(our_product=product)
            context['competitor_form'] = CompetitorProductForm(initial={'our_product': product})
        
        return context

    def post(self, request, *args, **kwargs):
        form = CompetitorProductForm(request.POST)
        if form.is_valid():
            competitor = form.save()
            messages.success(request, f"Competitor '{competitor.name}' mapped to '{competitor.our_product.name}'")
            return redirect(f"{request.path}?product_id={competitor.our_product.id}")
        else:
            messages.error(request, "Error adding competitor mapping")
            return redirect(request.path)


# === Product Comparison View ===
class ProductComparisonView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'products/comparison.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_ids = self.request.GET.getlist('product')
        
        if product_ids:
            products = Product.objects.filter(id__in=product_ids, is_active=True)
            context['products'] = products
            
            # Get pricing info for each product
            pricing_data = {}
            for product in products:
                pricing_data[product.id] = {
                    1: get_product_price(product.id, 1),
                    10: get_product_price(product.id, 10),
                    100: get_product_price(product.id, 100),
                }
            context['pricing_data'] = pricing_data
        
        return context

class ProductBundleListView(ObjectPermissionRequiredMixin, ListView):
    model = ProductBundle
    template_name = 'products/productbundle_list.html'
    context_object_name = 'bundles'
    paginate_by = 20

class ProductBundleDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = ProductBundle
    template_name = 'products/productbundle_detail.html'
    context_object_name = 'bundle'

class ProductBundleCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = ProductBundle
    form_class = ProductBundleForm
    template_name = 'products/productbundle_form.html'
    success_url = reverse_lazy('products:productbundle_list')

class ProductBundleUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = ProductBundle
    form_class = ProductBundleForm
    template_name = 'products/productbundle_form.html'
    success_url = reverse_lazy('products:productbundle_list')

class ProductBundleDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = ProductBundle
    template_name = 'products/productbundle_confirm_delete.html'
    success_url = reverse_lazy('products:productbundle_list')

class CompetitorProductListView(ObjectPermissionRequiredMixin, ListView):
    model = CompetitorProduct
    template_name = 'products/competitorproduct_list.html'
    context_object_name = 'competitors'
    paginate_by = 20

class CompetitorProductDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = CompetitorProduct
    template_name = 'products/competitorproduct_detail.html'
    context_object_name = 'competitor'

class CompetitorProductCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = CompetitorProduct
    form_class = CompetitorProductForm
    template_name = 'products/competitorproduct_form.html'
    success_url = reverse_lazy('products:competitorproduct_list')

class CompetitorProductUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = CompetitorProduct
    form_class = CompetitorProductForm
    template_name = 'products/competitorproduct_form.html'
    success_url = reverse_lazy('products:competitorproduct_list')

class CompetitorProductDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = CompetitorProduct
    template_name = 'products/competitorproduct_confirm_delete.html'
    success_url = reverse_lazy('products:competitorproduct_list')

class ProductComparisonListView(ObjectPermissionRequiredMixin, ListView):
    model = ProductComparison
    template_name = 'products/productcomparison_list.html'
    context_object_name = 'comparisons'
    paginate_by = 20

class ProductComparisonDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = ProductComparison
    template_name = 'products/productcomparison_detail.html'
    context_object_name = 'comparison'

class ProductComparisonCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = ProductComparison
    form_class = ProductComparisonForm  # Needs to be created
    template_name = 'products/productcomparison_form.html'
    success_url = reverse_lazy('products:productcomparison_list')

class ProductComparisonUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = ProductComparison
    form_class = ProductComparisonForm  # Needs to be created
    template_name = 'products/productcomparison_form.html'
    success_url = reverse_lazy('products:productcomparison_list')

class ProductComparisonDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = ProductComparison
    template_name = 'products/productcomparison_confirm_delete.html'
    success_url = reverse_lazy('products:productcomparison_list')

class ProductDependencyListView(ObjectPermissionRequiredMixin, ListView):
    model = ProductDependency
    template_name = 'products/productdependency_list.html'
    context_object_name = 'dependencies'
    paginate_by = 20

class ProductDependencyCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = ProductDependency
    form_class = ProductDependencyForm  # Needs to be created
    template_name = 'products/productdependency_form.html'
    success_url = reverse_lazy('products:productdependency_list')

class ProductDependencyUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = ProductDependency
    form_class = ProductDependencyForm  # Needs to be created
    template_name = 'products/productdependency_form.html'
    success_url = reverse_lazy('products:productdependency_list')

class ProductDependencyDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = ProductDependency
    template_name = 'products/productdependency_confirm_delete.html'
    success_url = reverse_lazy('products:productdependency_list')









class PriceListListView(ObjectPermissionRequiredMixin, ListView):
    model = PriceList
    template_name = 'products/pricelist_list.html'
    context_object_name = 'price_lists'
    
    def get_queryset(self):
        return PriceList.objects.filter(tenant=self.request.user.tenant)

class PriceListCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = PriceList
    form_class = PriceListForm
    template_name = 'products/pricelist_form.html'
    success_url = reverse_lazy('products:pricelist_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class PriceListUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = PriceList
    form_class = PriceListForm
    template_name = 'products/pricelist_form.html'
    success_url = reverse_lazy('products:pricelist_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all().select_related('product')
        context['item_form'] = PriceListItemForm(initial={'price_list': self.object})
        return context

class PriceListDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = PriceList
    template_name = 'products/pricelist_confirm_delete.html'
    success_url = reverse_lazy('products:pricelist_list')

class PriceListItemCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = PriceListItem
    form_class = PriceListItemForm
    template_name = 'products/pricelistitem_form.html'
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        self.object = form.save()
        messages.success(self.request, f"Price for {self.object.product} added.")
        return redirect('products:pricelist_edit', pk=self.object.price_list.id)

    def form_invalid(self, form):
        price_list_id = form.data.get('price_list')
        messages.error(self.request, "Error adding item. Check for duplicates.")
        return redirect('products:pricelist_edit', pk=price_list_id)

class PriceListItemDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = PriceListItem
    template_name = 'products/pricelistitem_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('products:pricelist_edit', kwargs={'pk': self.object.price_list.id})

class CouponListView(ObjectPermissionRequiredMixin, ListView):
    model = Coupon
    template_name = 'products/coupon_list.html'
    context_object_name = 'coupons'
    
    def get_queryset(self):
        return Coupon.objects.filter(tenant=self.request.user.tenant)

class CouponCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'products/coupon_form.html'
    success_url = reverse_lazy('products:coupon_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class CouponUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'products/coupon_form.html'
    success_url = reverse_lazy('products:coupon_list')

class CouponDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Coupon
    template_name = 'products/coupon_confirm_delete.html'
    success_url = reverse_lazy('products:coupon_list')

class PromotionListView(ObjectPermissionRequiredMixin, ListView):
    model = Promotion
    template_name = 'products/promotion_list.html'
    context_object_name = 'promotions'
    
    def get_queryset(self):
        return Promotion.objects.filter(tenant=self.request.user.tenant)

class PromotionCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'products/promotion_form.html'
    success_url = reverse_lazy('products:promotion_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class PromotionUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'products/promotion_form.html'
    success_url = reverse_lazy('products:promotion_list')

class PromotionDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Promotion
    template_name = 'products/promotion_confirm_delete.html'
    success_url = reverse_lazy('products:promotion_list')


class ProductBarcodeView(ObjectPermissionRequiredMixin, View):
    """
    Returns the barcode image for a product.
    Usage: <img src="{% url 'products:product_barcode' product.id %}">
    """
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, tenant=request.user.tenant)
        # Use SKU or create one if missing
        code = product.sku
        if not code:
            return HttpResponse("No SKU found", status=404)
            
        barcode_data = BarcodeService.generate_barcode(code)
        if not barcode_data:
             return HttpResponse("Error generating barcode", status=500)
             
        return HttpResponse(barcode_data, content_type="image/png")

class ProductLabelView(ObjectPermissionRequiredMixin, DetailView):
    """
    Printable page for a single label.
    """
    model = Product
    template_name = 'products/label_standard.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(tenant=self.request.user.tenant)

class BulkLabelPrintView(ObjectPermissionRequiredMixin, View):
    """
    Printable sheet for multiple products.
    Accepts ?pks=1,2,3 or prints all active.
    """
    def get(self, request):
        pks = request.GET.get('pks')
        if pks:
            pk_list = pks.split(',')
            products = Product.objects.filter(pk__in=pk_list, tenant=request.user.tenant)
        else:
            # Dangerous if too many products, limit to recent or active?
            # For now, let's just grab active ones, maybe limit 50
            products = Product.objects.filter(tenant=request.user.tenant, product_is_active=True)[:30]
            
        return render(request, 'products/label_sheet.html', {'products': products})

class SupplierListView(ObjectPermissionRequiredMixin, ListView):
    model = Supplier
    template_name = 'products/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

class SupplierCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'products/supplier_form.html'
    success_url = reverse_lazy('products:supplier_list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class SupplierUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'products/supplier_form.html'
    success_url = reverse_lazy('products:supplier_list')

class SupplierDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'products/supplier_confirm_delete.html'
    success_url = reverse_lazy('products:supplier_list')
