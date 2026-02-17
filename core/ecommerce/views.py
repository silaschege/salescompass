from django.views.generic import ListView, DetailView, TemplateView, View, CreateView
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, Cart, CartItem, Order, EcommerceCustomer
from .services import EcommerceService
from .forms import CheckoutForm
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

class CheckoutView(TenantAwareViewMixin, LoginRequiredMixin, View):
    template_name = 'ecommerce/checkout.html'

    def get(self, request):
        session_key = request.session.session_key
        cart = EcommerceService.get_or_create_cart(
            tenant=request.user.tenant,
            session_key=session_key
        )
        if not cart.items.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect('ecommerce:cart_view')
            
        form = CheckoutForm()
        return render(request, self.template_name, {'form': form, 'cart': cart})

    def post(self, request):
        session_key = request.session.session_key
        cart = EcommerceService.get_or_create_cart(
            tenant=request.user.tenant,
            session_key=session_key
        )
        
        form = CheckoutForm(request.POST)
        if form.is_valid():
            shipping_info = form.cleaned_data
            payment_method = shipping_info.pop('payment_method')
            
            # Identify customer
            customer, _ = EcommerceCustomer.objects.get_or_create(
                user=request.user,
                tenant=request.user.tenant
            )
            cart.customer = customer
            cart.save()
            
            order, error = EcommerceService.process_checkout(cart, shipping_info, payment_method, user=request.user)
            
            if error:
                messages.error(request, error)
                return redirect('ecommerce:cart_view')
                
            messages.success(request, "Order placed successfully!")
            return redirect('ecommerce:order_confirmation', pk=order.pk)
            
        return render(request, self.template_name, {'form': form, 'cart': cart})

class OrderConfirmationView(TenantAwareViewMixin, LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'ecommerce/order_confirmation.html'
    context_object_name = 'order'

class OrderHistoryView(TenantAwareViewMixin, LoginRequiredMixin, ListView):
    model = Order
    template_name = 'ecommerce/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(
            tenant=self.request.user.tenant,
            customer__user=self.request.user
        ).order_by('-created_at')

class OrderDetailView(TenantAwareViewMixin, LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'ecommerce/order_detail.html'
    context_object_name = 'order'

class RemoveFromCartView(TenantAwareViewMixin, View):
    def post(self, request, pk):
        session_key = request.session.session_key
        if not session_key:
            return redirect('ecommerce:cart_view')
            
        cart = EcommerceService.get_or_create_cart(
            tenant=request.user.tenant,
            session_key=session_key
        )
        
        success, message = EcommerceService.remove_from_cart(cart, pk)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
        return redirect('ecommerce:cart_view')

class ClearCartView(TenantAwareViewMixin, View):
    def post(self, request):
        session_key = request.session.session_key
        if not session_key:
            return redirect('ecommerce:cart_view')
            
        cart = EcommerceService.get_or_create_cart(
            tenant=request.user.tenant,
            session_key=session_key
        )
        
        EcommerceService.clear_cart(cart)
        messages.success(request, "Cart cleared successfully.")
        return redirect('ecommerce:cart_view')
