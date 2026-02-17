from django import forms
from .models import PurchaseOrder, PurchaseOrderLine, SupplierInvoice, PurchaseRequisition, PurchaseRequisitionLine, SupplierPayment
from products.models import Product
from suppliers.models import Supplier
from django.forms import inlineformset_factory
from hr.models import Department

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'warehouse', 'order_date', 'expected_date', 'notes', 'requisition']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['supplier'].queryset = Supplier.objects.filter(tenant=tenant, is_active=True)
            from inventory.models import Warehouse
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant)
            self.fields['requisition'].queryset = PurchaseRequisition.objects.filter(tenant=tenant, status='approved')

class PurchaseOrderLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLine
        fields = ['product', 'quantity_ordered', 'unit_cost', 'tax_rate_percent', 'is_fixed_asset']
        widgets = {
            'product': forms.Select(attrs={'class': 'product-select'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'quantity-input', 'min': '0', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'cost-input', 'min': '0', 'step': '0.01'}),
            'tax_rate_percent': forms.NumberInput(attrs={'class': 'tax-input', 'min': '0', 'max': '100', 'step': '0.01'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant, product_is_active=True)

def PurchaseOrderLineFormSet(*args, **kwargs):
    """
    Lazy factory to avoid 'str' object has no attribute '_meta' error at import time.
    """
    FormSet = inlineformset_factory(
        PurchaseOrder,
        PurchaseOrderLine,
        form=PurchaseOrderLineForm,
        extra=1,
        can_delete=True
    )
    return FormSet(*args, **kwargs)

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
            self.fields['supplier'].queryset = Supplier.objects.filter(tenant=tenant, is_active=True)
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(tenant=tenant)


class PurchaseRequisitionForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisition
        fields = ['department', 'date_required', 'priority', 'notes']
        widgets = {
            'date_required': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['department'].queryset = Department.objects.filter(tenant=tenant)

class PurchaseRequisitionLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisitionLine
        fields = ['product', 'quantity', 'estimated_unit_price', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'quantity-input', 'min': '0', 'step': '0.01'}),
            'estimated_unit_price': forms.NumberInput(attrs={'class': 'price-input', 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 1}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant, product_is_active=True)

def PurchaseRequisitionLineFormSet(*args, **kwargs):
    """
    Lazy factory to avoid import-time errors.
    """
    FormSet = inlineformset_factory(
        PurchaseRequisition,
        PurchaseRequisitionLine,
        form=PurchaseRequisitionLineForm,
        extra=1,
        can_delete=True
    )
    return FormSet(*args, **kwargs)


class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ['supplier', 'payment_date', 'amount', 'method', 'reference', 'invoices']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['supplier'].queryset = Supplier.objects.filter(tenant=tenant, is_active=True)
            self.fields['invoices'].queryset = SupplierInvoice.objects.filter(
                tenant=tenant, status__in=['posted', 'overdue']
            )
