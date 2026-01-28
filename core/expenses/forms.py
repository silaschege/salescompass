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
