from django import forms
from .models import PurchaseOrder, SupplierInvoice
from products.models import Supplier

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'warehouse', 'order_date', 'expected_date', 'notes']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True) # Suppliers are not currently tenant-aware in core, assuming global or needs fix
            # Assuming Warehouse is tenant-aware
            from inventory.models import Warehouse
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant)

class SupplierInvoiceForm(forms.ModelForm):
    class Meta:
        model = SupplierInvoice
        fields = ['invoice_number', 'supplier', 'purchase_order', 'invoice_date', 'due_date', 'total_amount']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(tenant=tenant)
