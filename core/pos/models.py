from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from decimal import Decimal
import uuid


# ============================================================================
# PAYMENT CHOICES
# ============================================================================

PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash'),
    ('card', 'Credit/Debit Card'),
    ('mobile_money', 'Mobile Money (M-PESA)'),
    ('bank_transfer', 'Bank Transfer'),
    ('check', 'Check'),
    ('voucher', 'Voucher/Gift Card'),
    ('credit', 'Store Credit'),
    ('split', 'Split Payment'),
]

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('partial_refund', 'Partially Refunded'),
]

TRANSACTION_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending Payment'),
    ('completed', 'Completed'),
    ('voided', 'Voided'),
    ('refunded', 'Refunded'),
    ('on_hold', 'On Hold'),
]

DRAWER_STATUS_CHOICES = [
    ('closed', 'Closed'),
    ('open', 'Open'),
    ('counting', 'Counting'),
]

PRINTER_TYPE_CHOICES = [
    ('disabled', 'Disabled'),
    ('network', 'Network (TCP/IP)'),
    ('usb', 'USB'),
    ('serial', 'Serial (COM/TTY)'),
]

PRINTER_WIDTH_CHOICES = [
    (32, '32 Characters'),
    (42, '42 Characters'),
    (48, '48 Characters'),
]


# ============================================================================
# TERMINAL MODELS
# ============================================================================

class POSTerminal(TenantModel):
    """
    Physical or virtual POS terminal registration.
    """
    terminal_name = models.CharField(max_length=100)
    terminal_code = models.CharField(max_length=50, unique=True)
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_terminals',
        help_text="Default warehouse for stock operations"
    )
    
    # Terminal details
    location = models.CharField(max_length=255, blank=True, help_text="Physical location description")
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    
    # Settings
    allow_negative_stock = models.BooleanField(default=False)
    require_customer = models.BooleanField(default=False)
    auto_print_receipt = models.BooleanField(default=True)
    receipt_footer = models.TextField(blank=True)
    
    # Hardware
    receipt_printer_name = models.CharField(max_length=100, blank=True)
    printer_type = models.CharField(max_length=20, choices=PRINTER_TYPE_CHOICES, default='disabled')
    printer_ip = models.GenericIPAddressField(null=True, blank=True, help_text="For network printers")
    printer_port = models.CharField(max_length=100, blank=True, help_text="For USB/Serial ports")
    printer_width = models.IntegerField(choices=PRINTER_WIDTH_CHOICES, default=48)
    
    barcode_scanner_enabled = models.BooleanField(default=True)
    cash_drawer_enabled = models.BooleanField(default=True)
    customer_display_enabled = models.BooleanField(default=False)
    customer_display_port = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['terminal_name']
        verbose_name = 'POS Terminal'
        verbose_name_plural = 'POS Terminals'

    def __str__(self):
        return f"{self.terminal_name} ({self.terminal_code})"


class POSSession(TenantModel):
    """
    Cashier shift/session management.
    """
    SESSION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('closing', 'Closing'),
        ('closed', 'Closed'),
    ]
    
    terminal = models.ForeignKey(
        POSTerminal,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    cashier = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pos_sessions'
    )
    session_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='active')
    
    # Opening
    opened_at = models.DateTimeField(auto_now_add=True)
    opening_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    opening_notes = models.TextField(blank=True)
    
    # Closing
    closed_at = models.DateTimeField(null=True, blank=True)
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_difference = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    closing_notes = models.TextField(blank=True)
    
    # Summary (populated on close)
    total_sales = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    total_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_discounts = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-opened_at']
        verbose_name = 'POS Session'
        verbose_name_plural = 'POS Sessions'

    def __str__(self):
        return f"Session {self.session_number} - {self.cashier.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.session_number:
            self.session_number = f"SES-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


# ============================================================================
# TRANSACTION MODELS
# ============================================================================

class POSTransaction(TenantModel):
    """
    Individual POS sale transaction.
    """
    # Reference
    transaction_number = models.CharField(max_length=50, unique=True)
    session = models.ForeignKey(
        POSSession,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )
    terminal = models.ForeignKey(
        POSTerminal,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )
    
    # Customer (optional for walk-ins)
    customer = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_transactions'
    )
    customer_name = models.CharField(max_length=255, blank=True, help_text="For walk-in customers")
    customer_phone = models.CharField(max_length=50, blank=True)
    customer_email = models.EmailField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    coupon = models.ForeignKey(
        'products.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_transactions'
    )
    discount_reason = models.CharField(max_length=255, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tax details
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.00, help_text="Tax rate percentage")
    is_tax_inclusive = models.BooleanField(default=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    cashier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pos_transactions_processed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_transactions_voided'
    )
    void_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'POS Transaction'
        verbose_name_plural = 'POS Transactions'

    def __str__(self):
        return f"{self.transaction_number} - {self.total_amount}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from quality_control.models import InspectionLog, InspectionRule

        # Quality Gate: Mandatory inspection for specific products on sale
        if self.status == 'completed':
            for line in self.lines.all():
                rules = InspectionRule.objects.filter(product=line.product, tenant=self.tenant)
                if rules.exists():
                    # Check if an inspection log exists and passed for this product in this store context
                    # Note: POS might use batch-level inspections or individual serial inspections.
                    # For now, we'll check if ANY passed inspection exists for this product recently,
                    # or if the source (Warehouse) has a passed inspection.
                    # Simple version: check if there's a passed log for this product.
                    logs = InspectionLog.objects.filter(
                        product=line.product,
                        tenant=self.tenant,
                        status='passed'
                    )
                    
                    if not logs.exists():
                        raise ValidationError(f"Cannot complete Sale: Product {line.product.product_name} has no passed quality inspection.")

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = f"TXN-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Recalculate transaction totals from line items."""
        lines = self.lines.all()
        self.subtotal = sum(line.line_total for line in lines)
        
        # Apply discount
        if self.discount_percent > 0:
            self.discount_amount = self.subtotal * (self.discount_percent / Decimal('100'))
        
        amount_after_discount = self.subtotal - self.discount_amount
        
        if self.is_tax_inclusive:
            # Tax is already included in prices
            # self.tax_amount = amount_after_discount - (amount_after_discount / (1 + self.tax_rate / Decimal('100')))
            pass # Now calculated from lines
        else:
            # Add tax on top
            # self.tax_amount = amount_after_discount * (self.tax_rate / Decimal('100'))
            pass # Now calculated from lines
        
        # Aggregate from lines
        self.tax_amount = sum(line.tax_amount for line in lines)
        
        # Total is subtotal - discount + tax (if exclusive) or just subtotal - discount (if inclusive, but lines handle this)
        # Actually, simpler:
        # Total = Sum of line totals
        self.total_amount = sum(line.line_total for line in lines)
        self.save()

    @property
    def is_paid(self):
        return self.amount_paid >= self.total_amount

    @property
    def balance_due(self):
        return max(self.total_amount - self.amount_paid, Decimal('0'))


class POSTransactionLine(TenantModel):
    """
    Line items in a POS transaction.
    """
    transaction = models.ForeignKey(
        POSTransaction,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='pos_transaction_lines'
    )
    
    # Quantity and pricing
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_tax_inclusive = models.BooleanField(default=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Product snapshot (for historical accuracy)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100, blank=True)
    
    # Flags
    is_returned = models.BooleanField(default=False)
    return_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Transaction Line'
        verbose_name_plural = 'Transaction Lines'

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def save(self, *args, **kwargs):
        # Snapshot product details
        if self.product:
            self.product_name = self.product.product_name
            self.product_sku = self.product.sku
        
        # Calculate line total
        subtotal = self.quantity * self.unit_price
        if self.discount_percent > 0:
            self.discount_amount = subtotal * (self.discount_percent / Decimal('100'))
        
        amount_after_discount = subtotal - self.discount_amount
        
        if self.is_tax_inclusive:
             self.tax_amount = amount_after_discount - (amount_after_discount / (1 + self.tax_rate / Decimal('100')))
             self.line_total = amount_after_discount # Inclusive total matches the discounted price
        else:
             self.tax_amount = amount_after_discount * (self.tax_rate / Decimal('100'))
             self.line_total = amount_after_discount + self.tax_amount
        
        super().save(*args, **kwargs)


# ============================================================================
# PAYMENT MODELS
# ============================================================================

class POSPayment(TenantModel):
    """
    Payment records for POS transactions.
    """
    transaction = models.ForeignKey(
        POSTransaction,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='completed')
    
    # Method-specific details
    reference_number = models.CharField(max_length=100, blank=True, help_text="External payment reference")
    
    # Card details (if applicable)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_type = models.CharField(max_length=20, blank=True)
    
    # Mobile money (if applicable)
    mobile_number = models.CharField(max_length=20, blank=True)
    mobile_provider = models.CharField(max_length=50, blank=True)
    
    # Voucher (if applicable)
    voucher_code = models.CharField(max_length=50, blank=True)
    
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pos_payments_processed'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'POS Payment'
        verbose_name_plural = 'POS Payments'

    def __str__(self):
        return f"{self.get_payment_method_display()}: {self.amount}"


# ============================================================================
# RECEIPT MODELS
# ============================================================================

class POSReceipt(TenantModel):
    """
    Digital/printed receipt data.
    """
    RECEIPT_TYPE_CHOICES = [
        ('sale', 'Sale Receipt'),
        ('refund', 'Refund Receipt'),
        ('duplicate', 'Duplicate'),
        ('gift', 'Gift Receipt'),
    ]
    
    transaction = models.ForeignKey(
        POSTransaction,
        on_delete=models.CASCADE,
        related_name='receipts'
    )
    receipt_number = models.CharField(max_length=50, unique=True)
    receipt_type = models.CharField(max_length=20, choices=RECEIPT_TYPE_CHOICES, default='sale')
    
    # Content
    header_text = models.TextField(blank=True)
    footer_text = models.TextField(blank=True)
    
    # Status
    is_printed = models.BooleanField(default=False)
    printed_count = models.IntegerField(default=0)
    last_printed_at = models.DateTimeField(null=True, blank=True)
    
    # Digital delivery
    emailed_to = models.EmailField(blank=True)
    sms_sent_to = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'POS Receipt'
        verbose_name_plural = 'POS Receipts'

    def __str__(self):
        return f"Receipt {self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCP-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


# ============================================================================
# CASH DRAWER MODELS
# ============================================================================

class POSCashDrawer(TenantModel):
    """
    Cash drawer operations and current state.
    """
    terminal = models.OneToOneField(
        POSTerminal,
        on_delete=models.CASCADE,
        related_name='cash_drawer'
    )
    status = models.CharField(max_length=20, choices=DRAWER_STATUS_CHOICES, default='closed')
    current_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_opened_at = models.DateTimeField(null=True, blank=True)
    last_opened_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_drawer_opens'
    )
    
    # Denomination tracking (optional)
    denomination_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON object with denomination counts"
    )
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'POS Cash Drawer'
        verbose_name_plural = 'POS Cash Drawers'

    def __str__(self):
        return f"Cash Drawer - {self.terminal.terminal_name}"


class POSCashMovement(TenantModel):
    """
    Track all cash in/out movements for a drawer.
    """
    MOVEMENT_TYPE_CHOICES = [
        ('opening', 'Opening Balance'),
        ('sale', 'Sale'),
        ('refund', 'Refund'),
        ('pay_in', 'Pay In'),
        ('pay_out', 'Pay Out'),
        ('closing', 'Closing Balance'),
    ]
    
    drawer = models.ForeignKey(
        POSCashDrawer,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    session = models.ForeignKey(
        POSSession,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Reference
    transaction = models.ForeignKey(
        POSTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_movements'
    )
    
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cash Movement'
        verbose_name_plural = 'Cash Movements'

    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.amount}"


# ============================================================================
# REFUND MODELS
# ============================================================================

class POSRefund(TenantModel):
    """
    Returns and refunds processing.
    """
    REFUND_TYPE_CHOICES = [
        ('full', 'Full Refund'),
        ('partial', 'Partial Refund'),
        ('exchange', 'Exchange'),
    ]
    REFUND_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    original_transaction = models.ForeignKey(
        POSTransaction,
        on_delete=models.PROTECT,
        related_name='refunds'
    )
    refund_transaction = models.OneToOneField(
        POSTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_for'
    )
    
    refund_number = models.CharField(max_length=50, unique=True)
    refund_type = models.CharField(max_length=20, choices=REFUND_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    
    # Amounts
    refund_amount = models.DecimalField(max_digits=14, decimal_places=2)
    refund_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    
    # Reason
    reason = models.TextField()
    
    # Approval
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_refunds_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Processing
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pos_refunds_processed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'POS Refund'
        verbose_name_plural = 'POS Refunds'

    def __str__(self):
        return f"Refund {self.refund_number}"

    def save(self, *args, **kwargs):
        if not self.refund_number:
            self.refund_number = f"REF-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class POSRefundLine(TenantModel):
    """
    Line items being refunded.
    """
    refund = models.ForeignKey(
        POSRefund,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    original_line = models.ForeignKey(
        POSTransactionLine,
        on_delete=models.PROTECT,
        related_name='refund_lines'
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    restock = models.BooleanField(default=True, help_text="Return item to stock?")
    
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Refund Line'
        verbose_name_plural = 'Refund Lines'

    def __str__(self):
        return f"{self.quantity} x {self.original_line.product_name}"
