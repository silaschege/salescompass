from django import forms
from .models import (
    ChartOfAccount, JournalEntry, JournalEntryLine, 
    Budget, RecurringJournalEntry, AccountingIntegration, 
    FiscalYear, FiscalPeriod, TaxRate, TaxRule
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
        fields = ['entry_date', 'reference', 'description']
        widgets = {
            'entry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']

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
