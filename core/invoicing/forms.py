from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceLine, Payment, CreditNote, DebitNote
from accounts.models import Account
from products.models import Product

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'invoice_number', 'issue_date', 'due_date', 'notes', 'terms']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['customer'].queryset = Account.objects.filter(tenant=tenant)
            # Pre-fill invoice number if new instance
            if not self.instance.pk:
                last_invoice = Invoice.objects.filter(tenant=tenant).order_by('-id').first()
                if last_invoice:
                    # Simple increment logic (can be made more robust)
                    try:
                        prefix = last_invoice.invoice_number.rstrip('0123456789')
                        num = int(last_invoice.invoice_number[len(prefix):])
                        self.fields['invoice_number'].initial = f"{prefix}{num + 1}"
                    except:
                        pass
                else:
                    self.fields['invoice_number'].initial = "INV-001"

class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
        fields = ['product', 'description', 'quantity', 'unit_price', 'tax_rate']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control tax-input', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
             self.fields['product'].queryset = Product.objects.filter(tenant=tenant)

InvoiceLineFormSet = inlineformset_factory(
    Invoice, InvoiceLine, form=InvoiceLineForm,
    extra=1, can_delete=True
)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['invoice'].queryset = Invoice.objects.filter(tenant=tenant)

class CreditNoteForm(forms.ModelForm):
    class Meta:
        model = CreditNote
        fields = ['invoice', 'note_number', 'amount', 'reason']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'note_number': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['invoice'].queryset = Invoice.objects.filter(tenant=tenant)

class DebitNoteForm(forms.ModelForm):
    class Meta:
        model = DebitNote
        fields = ['invoice', 'note_number', 'amount', 'reason']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'note_number': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['invoice'].queryset = Invoice.objects.filter(tenant=tenant)
