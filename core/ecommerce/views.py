from django.views.generic import ListView, DetailView, TemplateView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Cart, CartItem
from .services import EcommerceService
from core.views import TenantAwareViewMixin

class ProductListView(TenantAwareViewMixin, ListView):
    model = Product
    template_name = 'ecommerce/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(
            tenant=self.request.user.tenant,
            product_is_active=True
        ).order_by('product_name')

class ProductDetailView(TenantAwareViewMixin, DetailView):
    model = Product
    template_name = 'ecommerce/product_detail.html'
    context_object_name = 'product'

class CartView(TenantAwareViewMixin, TemplateView):
    template_name = 'ecommerce/cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
            
        context['cart'] = EcommerceService.get_or_create_cart(
            tenant=self.request.user.tenant,
            session_key=session_key
        )
        return context

class AddToCartView(TenantAwareViewMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk, tenant=request.user.tenant)
        quantity = request.POST.get('quantity', 1)
        
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
            
        cart = EcommerceService.get_or_create_cart(
            tenant=request.user.tenant,
            session_key=session_key
        )
        
        EcommerceService.add_to_cart(cart, product, quantity)
        messages.success(request, f"Added {product.product_name} to cart.")
        return redirect('ecommerce:cart_view')
