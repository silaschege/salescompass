from django.db import models
from django.utils import timezone
from tenants.models import TenantAwareModel as TenantModel
from core.models import TimeStampedModel, User
from products.models import Product
from decimal import Decimal
import uuid

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

class Order(TenantModel, TimeStampedModel):
    """
    Finalized order from a cart.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(EcommerceCustomer, on_delete=models.CASCADE, related_name='orders')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)
    shipping_zip = models.CharField(max_length=20)
    
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

class OrderItem(TenantModel):
    """
    Individual items in an order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    
    # Snapshots
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
