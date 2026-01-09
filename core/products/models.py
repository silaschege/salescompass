from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User

PRICING_MODEL_CHOICES = [
    ('flat', 'Flat Fee'),
    ('per_unit', 'Per Unit'),
    ('tiered', 'Tiered'),
    ('subscription', 'Subscription'),
]

ESG_CERTIFICATION_CHOICES = [
    ('iso14001', 'ISO 14001'),
    ('energy_star', 'Energy Star'),
    ('epa', 'EPA Certified'),
    ('none', 'None'),
]

class Product(TenantModel):
    """
    Core product in the catalog.
    """
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    upc = models.CharField(max_length=12, blank=True, help_text="Universal Product Code")
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated")
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    pricing_model = models.CharField(max_length=20, choices=PRICING_MODEL_CHOICES, default='flat')
    currency = models.CharField(max_length=3, default='USD')
    
    # Subscription (for recurring revenue products)
    is_subscription = models.BooleanField(default=False, help_text="Is this a subscription product?")
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annually', 'Annually'),
            ('one_time', 'One-Time'),
        ],
        default='one_time'
    )
    subscription_term = models.IntegerField(null=True, blank=True, help_text="Contract term in months (e.g., 12, 24)")
    auto_renewal = models.BooleanField(default=False, help_text="Automatically renew subscription")
    
    # ESG
    esg_certified = models.BooleanField(default=False)
    carbon_footprint = models.FloatField(null=True, blank=True, help_text="kg CO2e per unit")
    esg_certifications = models.CharField(max_length=255, blank=True)  # comma-separated from choices
    sustainability_notes = models.TextField(blank=True)
    tco2e_saved = models.FloatField(default=0.0, help_text="Tonnes of CO2e saved by customer")
    
    # Availability
    product_is_active = models.BooleanField(default=True)
    available_from = models.DateField(null=True, blank=True)
    available_to = models.DateField(null=True, blank=True)
    
    # Metadata
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"{self.product_name} ({self.sku})"

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def get_certifications_list(self):
        return [cert.strip() for cert in self.esg_certifications.split(',') if cert.strip()]


class PricingTier(TenantModel):
    """
    Tiered pricing for products (e.g., 1-10 units: $10, 11-100: $8).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='pricing_tiers')
    min_quantity = models.IntegerField()
    max_quantity = models.IntegerField(null=True, blank=True)  # null = unlimited
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.FloatField(default=0.0)

    class Meta:
        ordering = ['min_quantity']

    def __str__(self):
        return f"{self.product.product_name} - {self.min_quantity}+ units"


class ProductBundle(TenantModel):
    """
    Product bundles (e.g., "Starter Pack" = Product A + Product B).
    """
    product_bundle_name = models.CharField(max_length=255)
    product_bundle_description = models.TextField(blank=True)
    products = models.ManyToManyField(Product, through='BundleItem')
    bundle_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    product_bundle_is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.product_bundle_name


class BundleItem(TenantModel):
    """
    Items in a product bundle.
    """
    bundle = models.ForeignKey(ProductBundle, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.product_name} in {self.bundle.product_bundle_name}"


class CompetitorProduct(TenantModel):
    """
    Competitor product mapping for competitive analysis.
    """
    competitor_product_name = models.CharField(max_length=255)
    competitor_name = models.CharField(max_length=255)
    competitor_sku = models.CharField(max_length=100, blank=True)
    our_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='competitor_mappings')
    competitive_advantage = models.TextField(blank=True)
    price_difference_percent = models.FloatField(default=0.0)
    is_direct_competitor = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.competitor_name} - {self.competitor_product_name}"


class ProductDependency(TenantModel):
    """
    Product dependencies (e.g., Product B requires Product A).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='dependencies')
    required_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='required_by')
    dependency_type = models.CharField(
        max_length=20,
        choices=[('required', 'Required'), ('recommended', 'Recommended')],
        default='required'
    )

    class Meta:
        unique_together = [('product', 'required_product')]

    def __str__(self):
        return f"{self.product.product_name} requires {self.required_product.product_name}"


class ProductComparison(TenantModel):
    """
    Pre-defined product comparisons for marketing.
    """
    product_comparison_name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, related_name='comparisons')
    product_comparison_is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.product_comparison_name