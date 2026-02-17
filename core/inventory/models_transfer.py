
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
