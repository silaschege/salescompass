from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from decimal import Decimal


class Warehouse(TenantModel):
    """
    Physical storage location for inventory.
    """
    warehouse_name = models.CharField(max_length=255)
    warehouse_code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_warehouses'
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default warehouse for new stock")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['warehouse_name']
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'

    def __str__(self):
        return f"{self.warehouse_name} ({self.warehouse_code})"

    def save(self, *args, **kwargs):
        # Ensure only one default warehouse per tenant
        if self.is_default:
            Warehouse.objects.filter(tenant=self.tenant, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class StockLocation(TenantModel):
    """
    Specific areas within a warehouse (aisle, shelf, bin).
    """
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name='locations'
    )
    location_code = models.CharField(max_length=100)
    location_name = models.CharField(max_length=255, blank=True)
    aisle = models.CharField(max_length=20, blank=True)
    shelf = models.CharField(max_length=20, blank=True)
    bin = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['warehouse', 'location_code']
        unique_together = [('warehouse', 'location_code')]
        verbose_name = 'Stock Location'
        verbose_name_plural = 'Stock Locations'

    def __str__(self):
        return f"{self.warehouse.warehouse_code}/{self.location_code}"


MOVEMENT_TYPE_CHOICES = [
    ('in', 'Stock In'),
    ('out', 'Stock Out'),
    ('transfer', 'Transfer'),
    ('adjustment', 'Adjustment'),
    ('sale', 'Sale'),
    ('return', 'Return'),
    ('damage', 'Damage'),
    ('expired', 'Expired'),
]

ADJUSTMENT_REASON_CHOICES = [
    ('count', 'Physical Count'),
    ('damage', 'Damaged Goods'),
    ('theft', 'Theft/Loss'),
    ('expired', 'Expired'),
    ('correction', 'Data Correction'),
    ('other', 'Other'),
]


class StockLevel(TenantModel):
    """
    Current stock quantity per product and location.
    """
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='stock_levels'
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name='stock_levels'
    )
    location = models.ForeignKey(
        StockLocation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='stock_levels'
    )
    quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    reserved_quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Quantity reserved for pending orders"
    )
    cost_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Average cost price per unit"
    )
    last_counted = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Valuation Tracers (IAS 2)
    batch_number = models.CharField(max_length=100, blank=True, help_text="Batch tracking for FIFO")
    acquisition_date = models.DateField(null=True, blank=True)
    last_valuation_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['product', 'warehouse']
        unique_together = [('product', 'warehouse', 'location')]
        verbose_name = 'Stock Level'
        verbose_name_plural = 'Stock Levels'

    def __str__(self):
        loc = f"/{self.location.location_code}" if self.location else ""
        return f"{self.product.product_name} @ {self.warehouse.warehouse_code}{loc}: {self.quantity}"

    @property
    def available_quantity(self):
        """Quantity available for sale (total - reserved)."""
        return self.quantity - self.reserved_quantity

    @property
    def stock_value(self):
        """Total value of stock at cost price."""
        if self.cost_price:
            return self.quantity * self.cost_price
        return Decimal('0')


class StockMovement(TenantModel):
    """
    Track all stock movements (in, out, transfers).
    """
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Source and destination
    from_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='outgoing_movements'
    )
    from_location = models.ForeignKey(
        StockLocation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='outgoing_movements'
    )
    to_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='incoming_movements'
    )
    to_location = models.ForeignKey(
        StockLocation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='incoming_movements'
    )
    
    # Reference
    reference_type = models.CharField(
        max_length=50, 
        blank=True,
        help_text="e.g., 'pos_transaction', 'purchase_order', 'adjustment'"
    )
    reference_id = models.IntegerField(null=True, blank=True)
    
    # Costs
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='stock_movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'

    def __str__(self):
        return f"{self.movement_type.upper()}: {self.quantity} x {self.product.product_name}"


class StockAdjustment(TenantModel):
    """
    Manual stock adjustments with approval workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('applied', 'Applied'),
    ]
    
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name='adjustments'
    )
    adjustment_number = models.CharField(max_length=50, unique=True)
    reason = models.CharField(max_length=20, choices=ADJUSTMENT_REASON_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    # Audit
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_adjustments'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_adjustments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Adjustment'
        verbose_name_plural = 'Stock Adjustments'

    def __str__(self):
        return f"{self.adjustment_number} - {self.get_reason_display()}"


class StockAdjustmentLine(TenantModel):
    """
    Individual line items in a stock adjustment.
    """
    adjustment = models.ForeignKey(
        StockAdjustment, 
        on_delete=models.CASCADE, 
        related_name='lines'
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        StockLocation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    system_quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Quantity in system before adjustment"
    )
    actual_quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Actual counted quantity"
    )
    
    @property
    def variance(self):
        """Difference between actual and system quantity."""
        return self.actual_quantity - self.system_quantity

    class Meta:
        verbose_name = 'Adjustment Line'
        verbose_name_plural = 'Adjustment Lines'

    def __str__(self):
        return f"{self.product.product_name}: {self.variance:+}"


class ReorderRule(TenantModel):
    """
    Automatic reorder triggers when stock falls below threshold.
    """
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='reorder_rules'
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name='reorder_rules'
    )
    min_quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Minimum quantity before reorder alert"
    )
    reorder_quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Quantity to reorder"
    )
    max_quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Maximum stock level"
    )
    lead_time_days = models.IntegerField(
        default=7,
        help_text="Days to receive new stock"
    )
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('product', 'warehouse')]
        verbose_name = 'Reorder Rule'
        verbose_name_plural = 'Reorder Rules'

    def __str__(self):
        return f"{self.product.product_name} @ {self.warehouse.warehouse_code}: min={self.min_quantity}"

    def check_trigger(self):
        """Check if reorder should be triggered."""
        try:
            stock = StockLevel.objects.get(
                product=self.product, 
                warehouse=self.warehouse,
                tenant=self.tenant
            )
            return stock.available_quantity <= self.min_quantity
        except StockLevel.DoesNotExist:
            return True  # No stock = needs reorder


class StockAlert(TenantModel):
    """
    Alerts for low stock and reorder notifications.
    """
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstock', 'Overstock'),
        ('expiring', 'Expiring Soon'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='stock_alerts'
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name='stock_alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    current_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    threshold_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField(blank=True)
    acknowledged_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stock Alert'
        verbose_name_plural = 'Stock Alerts'

    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.product.product_name}"

class InterStoreTransfer(TenantModel):
    """
    Transfer stock between warehouses/stores.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('partial', 'Partially Received'),
        ('cancelled', 'Cancelled'),
    ]

    transfer_number = models.CharField(max_length=50, unique=True)
    source_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE,
        related_name='outgoing_transfers'
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE,
        related_name='incoming_transfers'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='requested_transfers'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_transfers'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inter-Store Transfer'
        verbose_name_plural = 'Inter-Store Transfers'

    def __str__(self):
        return f"{self.transfer_number}: {self.source_warehouse.warehouse_code} -> {self.destination_warehouse.warehouse_code}"


class InterStoreTransferLine(TenantModel):
    """
    Line items in a transfer.
    """
    transfer = models.ForeignKey(
        InterStoreTransfer, 
        on_delete=models.CASCADE,
        related_name='lines'
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE
    )
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_shipped = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Transfer Line'
        verbose_name_plural = 'Transfer Lines'

    def __str__(self):
        return f"{self.product.product_name} ({self.quantity_requested})"
