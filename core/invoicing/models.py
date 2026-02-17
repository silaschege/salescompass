from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User, TimeStampedModel
from accounts.models import Account
from products.models import Product

class Invoice(TenantModel, TimeStampedModel):
    """
    Tenant-level Invoice: A bill sent by the Tenant to their Customer (Account).
    """
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='invoicing_invoices')
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='tenant_invoices')
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField()
    due_date = models.DateField()
    
    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.account_name}"

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

class InvoiceLine(TenantModel):
    """
    Line item for a Tenant Invoice.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.product and not self.description:
            self.description = self.product.product_name
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} ({self.amount})"

class Payment(TenantModel, TimeStampedModel):
    """
    Payment received by the Tenant from the Customer.
    """
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='invoicing_payments')
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Other'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='tenant_payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.amount} for {self.invoice.invoice_number}"

class CreditNote(TenantModel, TimeStampedModel):
    """
    Credit Note issued to a Customer.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_notes')
    note_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    issue_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"CN-{self.note_number} for {self.invoice.invoice_number}"

class DebitNote(TenantModel, TimeStampedModel):
    """
    Debit Note issued to a Customer.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='debit_notes')
    note_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    issue_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"DN-{self.note_number} for {self.invoice.invoice_number}"
