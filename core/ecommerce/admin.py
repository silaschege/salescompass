from django.contrib import admin
from .models import EcommerceCustomer, Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'session_key', 'is_active', 'abandoned', 'created_at']
    list_filter = ['is_active', 'abandoned', 'tenant']
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'tenant']
    search_fields = ['order_number', 'customer__user__username', 'customer__user__email']
    inlines = [OrderItemInline]

@admin.register(EcommerceCustomer)
class EcommerceCustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'crm_account', 'phone', 'tenant']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
