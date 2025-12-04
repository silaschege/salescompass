from django.db import models
from accounts.models import Account

class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('hardware', 'Hardware Installation'),
        ('ship', 'Product Shipment'),
        ('software', 'Software License'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class CommissionRule(models.Model):
    """
    Rules for calculating sales commissions.
    """
    name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=10, choices=Product.PRODUCT_TYPE_CHOICES, blank=True, help_text="Apply to all products of this type")
    specific_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, help_text="Apply to specific product (overrides type)")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Commission percentage (e.g. 10.0 for 10%)")
    flat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Flat commission amount")
    min_sales_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Minimum sale amount required")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Sale(models.Model):
    SALE_TYPE_CHOICES = [
        ('hardware', 'Hardware Installation'),
        ('ship', 'Product Shipment'),
        ('software', 'Software License'),
    ]

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='sales'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sales'
    )
    sales_rep = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales',
        help_text="User credited with this sale"
    )
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} ({self.get_sale_type_display()}) for {self.account.name}"

class Commission(models.Model):
    """
    Recorded commission for a sale.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='commissions')
    sales_rep = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='commissions')
    rule_applied = models.ForeignKey(CommissionRule, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_earned = models.DateTimeField(auto_now_add=True)
    date_paid = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.sales_rep.email} - {self.amount} ({self.status})"
