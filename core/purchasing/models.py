from django.db import models
from django.conf import settings
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from decimal import Decimal

# Choices
PO_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent to Supplier'),
    ('partial', 'Partially Received'),
    ('received', 'Fully Received'),
    ('partially_billed', 'Partially Billed'),
    ('billed', 'Fully Billed'),
    ('closed', 'Closed'),
    ('cancelled', 'Cancelled'),
]

INVOICE_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('posted', 'Posted'), # Approved/Liability recorded
    ('paid', 'Paid'),
    ('overdue', 'Overdue'),
    ('void', 'Void'),
]

class PurchaseOrder(TenantModel):
    """
    Commercial document issued to a seller indicating types, quantities, and prices.
    """
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey('products.Supplier', on_delete=models.CASCADE, related_name='purchase_orders')
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, related_name='purchase_orders')
    
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=PO_STATUS_CHOICES, default='draft')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='po_requests')
    
    # Approval Workflow
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='po_approvals')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # IFRS/IPSAS Metadata
    is_capital_commitment = models.BooleanField(default=False, help_text="Is this a commitment for capital expenditure?")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-created_at']
        verbose_name = 'Purchase Order'

    def __str__(self):
        return f"{self.po_number} - {self.supplier}"


class PurchaseOrderLine(TenantModel):
    """
    Line item for a PO.
    """
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Optional tax rate per line
    tax_rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    # Asset Recognition (IAS 16)
    is_fixed_asset = models.BooleanField(default=False, help_text="Mark if this item is a Capital Asset")
    asset_category = models.ForeignKey('assets.AssetCategory', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity_ordered * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_name} ({self.quantity_ordered})"


class GoodsReceipt(TenantModel):
    """
    Record of goods received against a PO (GRN).
    Updates inventory levels.
    """
    grn_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='receipts')
    received_date = models.DateField()
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE) # Where it was received
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_date']

    def clean(self):
        from django.core.exceptions import ValidationError
        from quality_control.models import InspectionLog, InspectionRule

        # Quality Gate: Mandatory inspection for incoming goods
        # Check if there are inspection rules for any product in this receipt
        for line in self.lines.all():
            rules = InspectionRule.objects.filter(product=line.po_line.product, tenant=self.tenant, is_required_on_receipt=True)
            if rules.exists():
                logs = InspectionLog.objects.filter(
                    source_reference=self.grn_number,
                    tenant=self.tenant
                )
                
                if not logs.exists():
                    raise ValidationError(f"Cannot confirm Receipt: No quality inspection log found for {self.grn_number}.")
                
                if not logs.filter(status='passed').exists():
                    raise ValidationError(f"Cannot confirm Receipt: Quality inspection for {self.grn_number} has not passed.")

    def __str__(self):
        return self.grn_number


class GoodsReceiptLine(TenantModel):
    """
    Detailed line for GRN.
    """
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='lines')
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.CASCADE)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.ForeignKey('inventory.StockLocation', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # TODO: Trigger inventory update here or via signals


class SupplierInvoice(TenantModel):
    """
    Bill from supplier (Accounts Payable).
    """
    invoice_number = models.CharField(max_length=50) # Vendor's invoice number
    supplier = models.ForeignKey('products.Supplier', on_delete=models.CASCADE, related_name='invoices')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    invoice_date = models.DateField()
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-invoice_date']
        unique_together = ['tenant', 'supplier', 'invoice_number']

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier}"


class SupplierPayment(TenantModel):
    """
    Payment made to a supplier.
    """
    supplier = models.ForeignKey('products.Supplier', on_delete=models.CASCADE, related_name='payments')
    invoices = models.ManyToManyField(SupplierInvoice, related_name='payments')
    
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    method = models.CharField(max_length=20, choices=[
        ('bank_transfer', 'Bank Transfer'), 
        ('check', 'Check'), 
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card')
    ], default='bank_transfer')
    
    reference = models.CharField(max_length=100, blank=True)
    
    # Link to Accounting Journal
    journal_entry = models.ForeignKey('accounting.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.supplier} - {self.amount} ({self.payment_date})"

