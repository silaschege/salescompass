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
    ('pending_approval', 'Pending Approval'), # Generic pending state
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
    
    # Advanced Approval Fields
    approval_workflow = models.ForeignKey('ExpenseApprovalWorkflow', on_delete=models.SET_NULL, null=True, blank=True)
    current_step = models.ForeignKey('ExpenseApprovalStep', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_reports')
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.report_number:
            import random
            from django.utils import timezone
            now = timezone.now()
            # Generate a candidate number: EXP-YYYYMMDD-XXXX
            while True:
                candidate = f"EXP-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                if not ExpenseReport.objects.filter(report_number=candidate).exists():
                    self.report_number = candidate
                    break
        super().save(*args, **kwargs)

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
    
    # Phase 2: Card Integration
    matched_transaction = models.OneToOneField('expenses.CardTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='expense_line')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update report total
        total = self.report.lines.aggregate(sum=models.Sum('amount'))['sum'] or 0
        self.report.total_amount = total
        self.report.save()

    def __str__(self):
        return f"{self.date}: {self.amount} ({self.category})"


class ExpenseApprovalWorkflow(TenantModel):
    """
    Defines a sequence of approval steps for expenses.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Conditional logic triggers? 
    # For now, we might just have a default workflow, or select one.
    
    def __str__(self):
        return self.name

class ExpenseApprovalStep(TenantModel):
    """
    A single step in the expense approval workflow.
    """
    workflow = models.ForeignKey(ExpenseApprovalWorkflow, on_delete=models.CASCADE, related_name='steps')
    step_order = models.PositiveIntegerField(help_text="Sequence number of this step (1, 2, 3...)")
    name = models.CharField(max_length=100, help_text="e.g. 'Manager Approval', 'Finance Review'")
    
    # Approver definition
    approver_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="Specific user approver")
    approver_role = models.CharField(max_length=50, blank=True, help_text="e.g. 'manager', 'finance_admin'. System will resolve this dynamically.")
    
    # Conditions
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Step required only if amount >= this value")
    
    class Meta:
        ordering = ['step_order']
        unique_together = ['workflow', 'step_order']
        
    def __str__(self):
        return f"{self.workflow.name} - Step {self.step_order}: {self.name}"

class ExpensePolicy(TenantModel):
    """
    Policy rules for expense creation and submission.
    """
    ACTION_CHOICES = [
        ('block', 'Block Submission'),
        ('warn', 'Show Warning'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Scope
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, null=True, blank=True, help_text="Applies to specific category. If null, applies globally.")
    
    # Limits
    max_amount_per_transaction = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Maximum allowed amount for a single line item")
    max_amount_daily = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Maximum allowed daily total (per user)")
    
    # Action
    action_on_violation = models.CharField(max_length=10, choices=ACTION_CHOICES, default='warn')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Expense Policies"
        
    def __str__(self):
        scope = self.category.name if self.category else "Global"
        return f"{self.name} ({scope})"


class CorporateCard(TenantModel):
    """
    Represents a corporate credit card.
    """
    name = models.CharField(max_length=100, help_text="e.g. 'Gold HDFC Card'")
    last_4_digits = models.CharField(max_length=4)
    assigned_employee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='corporate_cards')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (*{self.last_4_digits})"

class CardTransaction(TenantModel):
    """
    Imported transaction from a corporate card statement.
    """
    STATUS_CHOICES = [
        ('unmatched', 'Unmatched'),
        ('matched', 'Matched'),
        ('ignored', 'Ignored'),
    ]
    
    card = models.ForeignKey(CorporateCard, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    merchant = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Bank transaction ref")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unmatched')
    
    def __str__(self):
        return f"{self.date}: {self.merchant} {self.amount}"
