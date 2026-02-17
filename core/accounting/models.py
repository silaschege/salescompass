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


class Currency(TenantModel):
    """
    Supported currencies for a tenant.
    """
    code = models.CharField(max_length=3) # e.g., USD, EUR, KES
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['tenant', 'code']
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} - {self.name}"


class ExchangeRate(TenantModel):
    """
    Dated exchange rates between currencies.
    """
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates_from')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates_to')
    rate = models.DecimalField(max_digits=20, decimal_places=10, help_text="1 from_currency = X to_currency")
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ['tenant', 'from_currency', 'to_currency', 'date']

    def __str__(self):
        return f"{self.from_currency.code} to {self.to_currency.code} on {self.date}: {self.rate}"


class JournalEntry(TenantModel):
    """
    Header for a financial transaction (double-entry).
    """
    entry_number = models.CharField(max_length=50, unique=True) # Auto-generated sequence
    entry_date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True) # External ref (Invoice #, PO #)
    
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='journal_entries', null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=10, default=1.0, help_text="Rate to convert to tenant base currency")
    
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
            
        # Validation: check if period is closed
        if self.status == 'posted':
            from .models import FiscalPeriod
            period = FiscalPeriod.objects.filter(
                tenant=self.tenant,
                start_date__lte=self.entry_date,
                end_date__gte=self.entry_date
            ).first()
            if period and period.is_closed:
                raise ValueError(f"Cannot post to date {self.entry_date} because accounting period {period.name} is closed.")
            
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
    
    # Amount in original currency
    debit_currency = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    credit_currency = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Amount in base currency (converted)
    debit = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Optional dimension linking
    partner_id = models.IntegerField(null=True, blank=True) # Generic link to Supplier/Customer
    
    # Matching
    is_reconciled = models.BooleanField(default=False)
    
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

class BankStatement(TenantModel):
    """
    Metadata for an imported bank statement file.
    """
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, limit_choices_to={'is_bank_account': True}, related_name='statements')
    import_date = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-import_date']
        verbose_name = 'Bank Statement'
        verbose_name_plural = 'Bank Statements'

    def get_unreconciled_count(self):
        return self.lines.filter(is_reconciled=False).count()

    def __str__(self):
        return f"Statement for {self.account} imported on {self.import_date.date()}"

class BankStatementLine(TenantModel):
    """
    Individual transaction lines from an imported bank statement.
    """
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name='lines')
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=20, decimal_places=2, help_text="Positive for deposits, negative for withdrawals")
    reference = models.CharField(max_length=100, blank=True)
    
    # Matching logic
    reconciled_line = models.OneToOneField('JournalEntryLine', on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_statement_line')
    is_reconciled = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'id']

    def __str__(self):
        return f"{self.date} - {self.description}: {self.amount}"

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
        
        # Platform Billing
        ('platform_invoice_paid', 'Platform Invoice Paid'),
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


class CustomFinancialReport(TenantModel):
    """
    Flexible custom report definitions.
    """
    REPORT_TYPE_CHOICES = [
        ('balance_sheet', 'Balance Sheet'),
        ('income_statement', 'Income Statement'),
        ('cash_flow', 'Cash Flow'),
        ('custom', 'Custom Layout'),
    ]
    
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    
    # Configuration stored as JSON
    # e.g., { "sections": [ { "name": "Current Assets", "account_ranges": ["1000", "1999"] }, ... ] }
    config_data = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BankAPIConfig(TenantModel):
    """
    Configuration for direct bank API integrations.
    """
    PROVIDER_CHOICES = [
        ('plaid', 'Plaid'),
        ('tink', 'Tink'),
        ('mock', 'Mock Bank Provider'),
    ]
    
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, limit_choices_to={'is_bank_account': True}, related_name='api_configs')
    
    # Credentials (Use encrypted fields in production)
    credentials_json = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_provider_display()} - {self.account}"
