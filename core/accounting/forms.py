from django import forms
from .models import (
    ChartOfAccount, JournalEntry, JournalEntryLine, 
    Budget, RecurringJournalEntry, AccountingIntegration, 
    FiscalYear, FiscalPeriod, TaxRate, TaxRule,
    BankReconciliation, BankStatement, BankStatementLine,
    Currency, ExchangeRate, CustomFinancialReport, BankAPIConfig
)

class ChartOfAccountForm(forms.ModelForm):
    class Meta:
        model = ChartOfAccount
        fields = ['account_code', 'account_name', 'account_type', 'parent', 'description', 'is_bank_account']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['parent'].queryset = ChartOfAccount.objects.filter(tenant=self.tenant)

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['entry_date', 'reference', 'description', 'currency', 'exchange_rate']
        widgets = {
            'entry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000000001'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['currency'].queryset = Currency.objects.filter(tenant=self.tenant)

class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit_currency', 'credit_currency', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'debit_currency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'credit_currency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'debit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'credit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(tenant=self.tenant)

JournalEntryLineFormSet = forms.inlineformset_factory(
    JournalEntry, JournalEntryLine,
    form=JournalEntryLineForm,
    extra=2, can_delete=True
)

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['fiscal_year', 'account', 'amount', 'description']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(tenant=self.tenant)
            self.fields['fiscal_year'].queryset = FiscalYear.objects.filter(tenant=self.tenant)

class RecurringJournalEntryForm(forms.ModelForm):
    class Meta:
        model = RecurringJournalEntry
        fields = ['name', 'frequency', 'start_date', 'end_date', 'next_run_date', 'description', 'lines_data', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'next_run_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

class BankReconciliationForm(forms.ModelForm):
    class Meta:
        model = BankReconciliation
        fields = ['account', 'statement_date', 'opening_balance', 'closing_balance', 'status']
        widgets = {
            'statement_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'closing_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(
                tenant=self.tenant, 
                is_bank_account=True
            )

class AccountingIntegrationForm(forms.ModelForm):
    class Meta:
        model = AccountingIntegration
        fields = ['event_type', 'debit_account', 'credit_account', 'is_active']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['debit_account'].queryset = ChartOfAccount.objects.filter(tenant=self.tenant)
            self.fields['credit_account'].queryset = ChartOfAccount.objects.filter(tenant=self.tenant)

class FiscalYearForm(forms.ModelForm):
    class Meta:
        model = FiscalYear
        fields = ['name', 'start_date', 'end_date', 'is_closed']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

class TaxRateForm(forms.ModelForm):
    class Meta:
        model = TaxRate
        fields = ['name', 'rate', 'description', 'is_active', 'is_default', 'account']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(tenant=self.tenant)

class TaxRuleForm(forms.ModelForm):
    class Meta:
        model = TaxRule
        fields = ['name', 'tax_rate', 'priority', 'product_category', 'region', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'product_category': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['tax_rate'].queryset = TaxRate.objects.filter(tenant=self.tenant)
        else:
            self.fields['tax_rate'].queryset = TaxRate.objects.none()

class BankStatementImportForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.none(), 
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the bank account this statement belongs to."
    )
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(
                tenant=self.tenant, 
                is_bank_account=True
            )
    
class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['code', 'name', 'symbol', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'USD'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'US Dollar'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '$'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = ['from_currency', 'to_currency', 'rate', 'date']
        widgets = {
            'from_currency': forms.Select(attrs={'class': 'form-select'}),
            'to_currency': forms.Select(attrs={'class': 'form-select'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000000001'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['from_currency'].queryset = Currency.objects.filter(tenant=self.tenant)
            self.fields['to_currency'].queryset = Currency.objects.filter(tenant=self.tenant)

class CustomFinancialReportForm(forms.ModelForm):
    class Meta:
        model = CustomFinancialReport
        fields = ['name', 'report_type', 'config_data', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'config_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

class BankAPIConfigForm(forms.ModelForm):
    class Meta:
        model = BankAPIConfig
        fields = ['provider', 'account', 'credentials_json', 'is_active']
        widgets = {
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'credentials_json': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(
                tenant=self.tenant, 
                is_bank_account=True
            )
