from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from core.permissions import ObjectPermissionRequiredMixin
from .models import Product, ProductBundle, CompetitorProduct, ProductComparison
from .forms import ProductForm, CompetitorProductForm
from .utils import generate_sku


class ProductListView(ObjectPermissionRequiredMixin, ListView):
    model = Product
class ProductListView(ObjectPermissionRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset.filter(is_active=True)


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
        messages.success(self.request, f"Product '{form.instance.name}' created!")
        return super().form_valid(form)


class ProductUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')


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