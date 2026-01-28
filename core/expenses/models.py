from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User
from decimal import Decimal

EXPENSE_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('paid', 'Paid/Reimbursed'),
]

PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash/Petty Cash'),
    ('bank', 'Bank Transfer'),
    ('payroll', 'Payroll Reimbursement'),
]

class ExpenseCategory(TenantModel):
    """
    Categories for expenses (e.g., Travel, Meals, Office Supplies).
    Links to GL Account for accounting integration.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    gl_account = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True)
    is_capital_expenditure = models.BooleanField(default=False, help_text="Default flag for CAPEX tracking")
    default_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Default tax rate for this category")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Expense Categories"
        unique_together = ['tenant', 'name']

    def __str__(self):
        return self.name


class ExpenseReport(TenantModel):
    """
    Collection of expenses submitted by an employee.
    """
    report_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_reports')
    
    status = models.CharField(max_length=20, choices=EXPENSE_STATUS_CHOICES, default='draft')
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='KES') # Tenant default currency usually
    
    submitted_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_approved')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    payroll_run = models.ForeignKey('hr.PayrollRun', on_delete=models.SET_NULL, null=True, blank=True, related_name='reimbursed_expenses')
    
    is_accrued = models.BooleanField(default=False, help_text="Indicates if the accrual entry has been posted to GL")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_number} - {self.title}"


class ExpenseLine(TenantModel):
    """
    Individual expense item.
    """
    report = models.ForeignKey(ExpenseReport, on_delete=models.CASCADE, related_name='lines')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    receipt = models.FileField(upload_to='expenses/receipts/', null=True, blank=True)
    
    is_billable = models.BooleanField(default=False)
    customer_account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True)
    
    # IFRS & Integration fields
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_capex = models.BooleanField(default=False, help_text="Overridable capitalization flag")
    
    related_asset = models.ForeignKey('assets.FixedAsset', on_delete=models.SET_NULL, null=True, blank=True, related_name='acquisition_expenses')
    related_shipment = models.ForeignKey('logistics.Shipment', on_delete=models.SET_NULL, null=True, blank=True, related_name='freight_expenses')
    related_route = models.ForeignKey('logistics.DeliveryRoute', on_delete=models.SET_NULL, null=True, blank=True, related_name='operational_expenses')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update report total
        total = self.report.lines.aggregate(sum=models.Sum('amount'))['sum'] or 0
        self.report.total_amount = total
        self.report.save()

    def __str__(self):
        return f"{self.date}: {self.amount} ({self.category})"
