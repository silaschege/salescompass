from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import TimeStampedModel, User
from products.models import Product
from decimal import Decimal

class EcommerceCustomer(TenantModel, TimeStampedModel):
    """
    Extensions for ecommerce users. Can be linked to a CRM Account.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ecommerce_profile')
    crm_account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='ecommerce_profiles')
    
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return self.user.get_full_name()

class Cart(TenantModel, TimeStampedModel):
    """
    Shopping cart for a customer or guest.
    """
    customer = models.ForeignKey(EcommerceCustomer, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    is_active = models.BooleanField(default=True)
    abandoned = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Cart {self.id} ({self.customer or 'Guest'})"

    @property
    def total_amount(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(TenantModel):
    """
    Individual items in a cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    # Store price at time of adding to cart (could be snapshot)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
