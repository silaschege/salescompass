from django.db import models
from django.conf import settings
from tenants.models import TenantAwareModel as TenantModel
from django.utils import timezone
from core.models import User

# Account Types: Standard accounting categories
ACCOUNT_TYPE_CHOICES = [
    ('asset_non_current', 'Non-Current Asset'),
    ('asset_current', 'Current Asset'),
    ('liability_non_current', 'Non-Current Liability'),
    ('liability_current', 'Current Liability'),
    ('equity', 'Equity'),
    ('revenue', 'Revenue'),
    ('cost_of_sales', 'Cost of Sales'),
    ('expense', 'Operating Expense'),
    ('other_income', 'Other Income'),
    ('other_expense', 'Other Expense'),
]

# Legacy compatibility mapping (optional, or handle in migration)
# For now, we assume this is a forward-looking change.

JOURNAL_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('posted', 'Posted'),
    ('reversed', 'Reversed'),
    ('cancelled', 'Cancelled'),
]

RECURRING_FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('annually', 'Annually'),
]

JOURNAL_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('posted', 'Posted'),
    ('reversed', 'Reversed'),
]

class ChartOfAccount(TenantModel):
    """
    Standard Chart of Accounts for double-entry bookkeeping.
    """
    account_code = models.CharField(max_length=20, db_index=True)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    
    is_bank_account = models.BooleanField(default=False)
    is_reconcilable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Running balance updated via signals/methods (optional optimization)
    current_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    class Meta:
        ordering = ['account_code']
        unique_together = ['tenant', 'account_code']
        verbose_name = 'Chart of Account'
        verbose_name_plural = 'Chart of Accounts'

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class FiscalYear(TenantModel):
    """
    Fiscal Year definition (e.g., 2025).
    """
    name = models.CharField(max_length=50) # e.g. "FY 2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['tenant', 'name']

    def __str__(self):
        return self.name


class FiscalPeriod(TenantModel):
    """
    Accounting period (usually monthly).
    """
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='periods')
    name = models.CharField(max_length=50) # e.g. "Jan 2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ['start_date']
        unique_together = ['tenant', 'fiscal_year', 'name']

    def __str__(self):
        return f"{self.name} ({self.fiscal_year.name})"


class JournalEntry(TenantModel):
    """
    Header for a financial transaction (double-entry).
    """
    entry_number = models.CharField(max_length=50, unique=True) # Auto-generated sequence
    entry_date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True) # External ref (Invoice #, PO #)
    
    status = models.CharField(max_length=20, choices=JOURNAL_STATUS_CHOICES, default='draft')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='journal_entries_created')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries_posted')
    posted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.entry_number:
            # Simple auto-generation: JE-YYYY-COUNT
            import datetime
            year = datetime.datetime.now().year
            last_entry = JournalEntry.objects.filter(entry_number__startswith=f"JE-{year}").order_by('-entry_number').first()
            if last_entry:
                try:
                    last_num = int(last_entry.entry_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.entry_number = f"JE-{year}-{new_num:05d}"
            
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-entry_date', '-created_at']
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"{self.entry_number} ({self.entry_date})"

    @property
    def is_balanced(self):
        debits = sum(line.debit for line in self.lines.all())
        credits = sum(line.credit for line in self.lines.all())
        return debits == credits


class JournalEntryLine(TenantModel):
    """
    Line item for a journal entry.
    """
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT, related_name='journal_lines')
    description = models.CharField(max_length=255, blank=True)
    
    debit = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Optional dimension linking
    partner_id = models.IntegerField(null=True, blank=True) # Generic link to Supplier/Customer
    
    def __str__(self):
        if self.debit > 0:
            return f"{self.account.account_code}: Dr {self.debit}"
        return f"{self.account.account_code}: Cr {self.credit}"


class BankReconciliation(TenantModel):
    """
    Bank Reconciliation Statement.
    """
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, limit_choices_to={'is_bank_account': True}, related_name='reconciliations')
    statement_date = models.DateField()
    
    opening_balance = models.DecimalField(max_digits=20, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=20, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=[('in_progress', 'In Progress'), ('completed', 'Completed')], default='in_progress')
    
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-statement_date']
        unique_together = ['account', 'statement_date']

    def __str__(self):
        return f"{self.account} - {self.statement_date}"

from django.db import models
from django.conf import settings
from tenants.models import TenantAwareModel as TenantModel
from core.models import User

class Budget(TenantModel):
    """
    Financial budget for a specific period and account.
    """
    fiscal_year = models.ForeignKey('FiscalYear', on_delete=models.CASCADE, related_name='budgets')
    account = models.ForeignKey('ChartOfAccount', on_delete=models.CASCADE, related_name='budgets')
    
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fiscal_year', 'account']
        unique_together = ['tenant', 'fiscal_year', 'account']
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'

    def __str__(self):
        return f"{self.fiscal_year} - {self.account}: {self.amount}"

class RecurringJournalEntry(TenantModel):
    """
    Template for recurring journal entries (e.g., monthly rent, depreciation).
    """
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ])
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_run_date = models.DateField()
    
    description = models.TextField(blank=True)
    
    # Template lines stored as JSON to avoid complex relationship management for templates
    # Structure: [{'account_id': 1, 'debit': 100, 'credit': 0, 'description': '...'}, ...]
    lines_data = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
    last_run_date = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recurring_journals')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recurring Journal'
        verbose_name_plural = 'Recurring Journals'

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

class AccountingIntegration(TenantModel):
    """
    Configuration for mapping system events to GL accounts.
    Allows dynamic setup of "Which account to debit/credit when X happens".
    """
    EVENT_TYPE_CHOICES = [
        # Sales
        ('invoice_validated', 'Customer Invoice Validated'),
        ('payment_received', 'Customer Payment Received'),
        ('pos_sale', 'POS Sale Completed'),
        
        # Purchasing
        ('grn_received', 'Goods Received (GRN)'),
        ('bill_approved', 'Vendor Bill Approved'),
        ('payment_sent', 'Vendor Payment Sent'),
        
        # Inventory
        ('inventory_loss', 'Inventory Loss/Adjustment'),
        ('inventory_gain', 'Inventory Gain/Adjustment'),
        
        # Assets (IAS 16, 36)
        ('asset_depreciation', 'Asset Depreciation'),
        ('asset_acquisition', 'Asset Capitalization (Purchase)'),
        ('asset_impairment', 'Asset Impairment Loss'),
        ('asset_revaluation', 'Asset Fair Value Revaluation'),
        ('asset_disposal', 'Asset Retirement / Disposal'),

        # Loyalty (IFRS 15)
        ('loyalty_earned', 'Loyalty Points Earned (Revenue Deferral)'),
        ('loyalty_redeemed', 'Loyalty Points Redeemed'),
        ('loyalty_breakage', 'Loyalty Points Expired (Breakage)'),
        
        # Expenses
        ('expense_accrual', 'Expense Report Accrual'),
        ('expense_payment', 'Expense Reimbursement Payment'),
        
        # Sales & Revenue (IFRS 15)
        ('revenue_deferral', 'Revenue Deferral (Contract Liability)'),
        ('revenue_recognition', 'Revenue Recognition (Fulfillment)'),
        ('contract_asset_recognition', 'Contract Asset Recognition (Unbilled Revenue)'),

        # Payroll & Benefits (IAS 19)
        ('payroll_accrual', 'Payroll Accrual (Salary Expense)'),
        ('payroll_payment', 'Payroll Payment Settlement'),
        ('leave_accrual', 'Leave Liability Provision'),
        ('benefit_contribution', 'Employer Benefit Contribution'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    
    # We might need multiple lines for one event, so let's simplify:
    # This model defines ONE leg of the transaction. A full config might need a more complex structure,
    # or we define "Default Debit Account" and "Default Credit Account" for simple events.
    
    debit_account = models.ForeignKey('ChartOfAccount', on_delete=models.CASCADE, related_name='integrations_debit', null=True, blank=True)
    credit_account = models.ForeignKey('ChartOfAccount', on_delete=models.CASCADE, related_name='integrations_credit', null=True, blank=True)
    
    # Optional specific journal
    # journal = models.ForeignKey('Journal', ... ) 
    
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['tenant', 'event_type']
        verbose_name = 'Accounting Integration Rule'
        verbose_name_plural = 'Accounting Integration Rules'

    def __str__(self):
        return f"{self.get_event_type_display()} Rule"

class TaxRate(TenantModel):
    """
    Tax rates definition (e.g., VAT 16%, Zero Rated 0%).
    """
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage (e.g., 16.00)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Link to Accounting - now direct FK
    account = models.ForeignKey('ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='tax_rates', help_text="GL Account for Tax Liability/Receivable")
    
    class Meta:
        verbose_name = 'Tax Rate'
        verbose_name_plural = 'Tax Rates'
    
    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class TaxRule(TenantModel):
    """
    Rules for applying tax rates based on criteria.
    """
    name = models.CharField(max_length=100)
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.CASCADE, related_name='rules')
    priority = models.IntegerField(default=0, help_text="Higher priority rules apply first")
    
    # Criteria (Null means "Any")
    product_category = models.ForeignKey('products.ProductCategory', on_delete=models.SET_NULL, null=True, blank=True)
    region = models.CharField(max_length=10, choices=[
        ('KE', 'Kenya'),
        ('US', 'United States'),
        ('GB', 'United Kingdom'),
        ('EU', 'European Union'),
    ], null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-priority', 'name']
        verbose_name = 'Tax Rule'
        verbose_name_plural = 'Tax Rules'

    def __str__(self):
        return f"{self.name} -> {self.tax_rate.name}"
