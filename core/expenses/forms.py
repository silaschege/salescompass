from django import forms
from .models import ExpenseReport, ExpenseLine, ExpenseCategory

class ExpenseReportForm(forms.ModelForm):
    class Meta:
        model = ExpenseReport
        fields = ['title', 'payment_method', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional: Describe the purpose of this report...'}),
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Q1 Sales Trip to Nairobi'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

class ExpenseLineForm(forms.ModelForm):
    class Meta:
        model = ExpenseLine
        fields = [
            'category', 'date', 'description', 'amount', 'tax_amount', 
            'is_capex', 'is_billable', 'customer_account', 
            'related_asset', 'related_shipment', 'related_route'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = ExpenseCategory.objects.filter(tenant=tenant, is_active=True)
            from accounts.models import Account
            self.fields['customer_account'].queryset = Account.objects.filter(tenant=tenant)

class CorporateCardForm(forms.ModelForm):
    class Meta:
        from .models import CorporateCard
        model = CorporateCard
        fields = ['name', 'last_4_digits', 'assigned_employee', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Amex Gold - Marketing'}),
            'last_4_digits': forms.TextInput(attrs={'placeholder': '1234', 'maxlength': '4'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
             from core.models import User
             self.fields['assigned_employee'].queryset = User.objects.filter(tenant=tenant)

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'gl_account', 'description', 'default_vat_rate', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        # No specific filtering needed yet for Category, but we must accept the tenant argument
