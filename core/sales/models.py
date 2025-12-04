from django.db import models
from accounts.models import Account
from products.models import Product


SALE_TYPE_CHOICES = [
    ('hardware', 'Hardware Installation'),
    ('ship', 'Product Shipment'),
    ('software', 'Software License'),
]


class CommissionRule(models.Model):
    """
    Rules for calculating sales commissions.
    """
    name = models.CharField(max_length=255)
    product_type = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Apply to all products of this type (matches pricing_model)"
    )
    specific_product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sales_commission_rules',
        help_text="Apply to specific product (overrides type)"
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.0, 
        help_text="Commission percentage (e.g. 10.0 for 10%)"
    )
    flat_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0, 
        help_text="Flat commission amount"
    )
    min_sales_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0, 
        help_text="Minimum sale amount required"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def applies_to_product(self, product):
        """Check if this rule applies to a given product."""
        if self.specific_product_id:
            return self.specific_product_id == product.id
        if self.product_type:
            return product.pricing_model == self.product_type
        return True


class Sale(models.Model):
    """
    Represents a completed sale transaction.
    """
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
    sale_type = models.CharField(max_length=20, choices=SALE_TYPE_CHOICES, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product.name} for {self.account.name}"
    
    def calculate_commission(self, sales_rep=None):
        """
        Calculate commission for this sale.
        Returns the commission amount and the applied rule.
        """
        from django.utils import timezone
        
        sales_rep = sales_rep or self.sales_rep
        if not sales_rep:
            return 0, None
        
        today = timezone.now().date()
        
        rules = CommissionRule.objects.filter(
            is_active=True,
            start_date__lte=today,
        ).filter(
            models.Q(end_date__gte=today) | models.Q(end_date__isnull=True)
        ).filter(
            min_sales_amount__lte=self.amount
        ).order_by('-min_sales_amount')
        
        for rule in rules:
            if rule.applies_to_product(self.product):
                percentage_amount = (self.amount * rule.percentage / 100)
                total_commission = percentage_amount + rule.flat_amount
                return total_commission, rule
        
        return 0, None


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
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.sales_rep.email} - {self.amount} ({self.status})"
    
    @classmethod
    def create_from_sale(cls, sale, sales_rep=None):
        """
        Create a commission record from a sale.
        """
        sales_rep = sales_rep or sale.sales_rep
        if not sales_rep:
            return None
        
        amount, rule = sale.calculate_commission(sales_rep)
        
        if amount <= 0:
            return None
        
        return cls.objects.create(
            sale=sale,
            sales_rep=sales_rep,
            rule_applied=rule,
            amount=amount,
            status='pending',
        )
