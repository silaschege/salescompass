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

DISCOUNT_TYPE_CHOICES = [
    ('percentage', 'Percentage'),
    ('fixed', 'Fixed Amount'),
]

class ProductCategory(TenantModel):
    """Hierarchical product categories."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, 
                               null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # IFRS 15 Integration
    deferred_revenue_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='category_deferred_revenue', help_text="Contract Liability account (IFRS 15)")
    revenue_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='category_revenue', help_text="Earned Income account")
    asset_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='category_assets', help_text="Inventory/Capital Asset account (IAS 16)")
    cogs_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='category_cogs', help_text="Cost of Goods Sold account (IAS 2)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])

class Supplier(TenantModel):
    """
    Vendor/Supplier information.
    """
    supplier_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['supplier_name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def __str__(self):
        return self.supplier_name


class Product(TenantModel):
    """
    Core product in the catalog.
    """
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    upc = models.CharField(max_length=12, blank=True, help_text="Universal Product Code")
    old_category = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL,  null=True, blank=True, related_name='products_category')
 
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated")
    
    # Images
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='products/thumbs/', blank=True, null=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    pricing_model = models.CharField(max_length=20, choices=PRICING_MODEL_CHOICES, default='flat')
    currency = models.CharField(max_length=3, default='USD')
    tax_rate = models.ForeignKey('accounting.TaxRate', on_delete=models.SET_NULL, 
                                 null=True, blank=True, help_text="Override system tax rules")
    
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
    
    # Inventory Management (for POS integration)
    track_inventory = models.BooleanField(default=False, help_text="Enable stock tracking for this product")
    low_stock_threshold = models.IntegerField(default=10, help_text="Alert when stock falls below this level")
    weight = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, help_text="Weight in kg")
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Length in cm")
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Width in cm")
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Height in cm")
    
    # Financial Intelligence (IFRS/IPSAS)
    valuation_method = models.CharField(
        max_length=20, 
        choices=[('fifo', 'FIFO'), ('avco', 'Weighted Average'), ('specific', 'Specific Identification')],
        default='avco'
    )
    is_capital_asset = models.BooleanField(default=False, help_text="IAS 16: Capitalize on purchase")
    nrv = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Net Realizable Value for impairment testing")
    ssp_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Standalone Selling Price (Min)")
    ssp_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Standalone Selling Price (Max)")
    
    # Metadata
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_supplier = models.ForeignKey(
        'Supplier', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='supplied_products'
    )


    def __str__(self):
        return f"{self.product_name} ({self.sku})"

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def get_certifications_list(self):
        return [cert.strip() for cert in self.esg_certifications.split(',') if cert.strip()]

    @property
    def name(self):
        return self.product_name
    
    @name.setter
    def name(self, value):
        self.product_name = value

    @property
    def is_active(self):
        return self.product_is_active

    @is_active.setter
    def is_active(self, value):
        self.product_is_active = value


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


class ProductDependency(TenantModel):
    """
    CPQ Rule: Relationship between products.
    e.g., 'If item A is selected, item B is mandatory'.
    """
    DEPENDENCY_TYPES = [
        ('mandatory', 'Mandatory (Must include)'),
        ('recommended', 'Recommended (Suggest to user)'),
        ('incompatible', 'Incompatible (Cannot include both)'),
    ]
    
    primary_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='dependencies'
    )
    dependent_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='requirements'
    )
    dependency_type = models.CharField(max_length=20, choices=DEPENDENCY_TYPES)
    message = models.CharField(max_length=255, blank=True, help_text="Message to show the user")
    
    class Meta:
        verbose_name_plural = 'product dependencies'
        unique_together = ['primary_product', 'dependent_product', 'dependency_type']

    def __str__(self):
        return f"{self.primary_product.product_name} -> {self.dependency_type} -> {self.dependent_product.product_name}"


class PriceList(TenantModel):
    """
    Named price lists for different customer segments (e.g., Retail, Wholesale, VIP).
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default='USD')
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Price List'
        verbose_name_plural = 'Price Lists'
    
    def __str__(self):
        return self.name


class PriceListItem(TenantModel):
    """
    Individual product price in a price list.
    """
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_list_items')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    min_quantity = models.IntegerField(default=1, help_text="Minimum qty for this price to apply")
    
    class Meta:
        unique_together = ['price_list', 'product', 'min_quantity']
        ordering = ['min_quantity']
    
    def __str__(self):
        return f"{self.product.sku} @ {self.price} ({self.price_list.name})"


class Coupon(TenantModel):
    """
    Discount codes entered manually at checkout.
    """
    code = models.CharField(max_length=50) # Tenant-scoped uniqueness via validation or constraints if possible
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Total times this coupon can be used")
    used_count = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['code', 'tenant']
    
    def __str__(self):
        return self.code


class Promotion(TenantModel):
    """
    Automatic promotions applied based on criteria (e.g., Seasonal Sale).
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    
    # Simple global promotion for now, can add product/category filters later
    
    def __str__(self):
        return self.name


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




class ProductComparison(TenantModel):
    """
    Pre-defined product comparisons for marketing.
    """
    product_comparison_name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, related_name='comparisons')
    product_comparison_is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.product_comparison_name