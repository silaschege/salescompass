from django import forms
from .models import (
    Warehouse, StockLocation, StockLevel, StockMovement,
    StockAdjustment, StockAdjustmentLine, ReorderRule,
    InterStoreTransfer
)
from products.models import Product
from django.forms import formset_factory


class WarehouseForm(forms.ModelForm):
    """Form for creating/editing warehouses."""
    
    class Meta:
        model = Warehouse
        fields = [
            'warehouse_name', 'warehouse_code', 'address', 'city', 
            'state', 'country', 'postal_code', 'phone', 'email',
            'manager', 'is_active', 'is_default'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            # Filter manager to users in the same tenant
            from core.models import User
            self.fields['manager'].queryset = User.objects.filter(tenant=tenant)



class StockLocationForm(forms.ModelForm):
    """Form for creating/editing stock locations."""
    
    class Meta:
        model = StockLocation
        fields = [
            'warehouse', 'location_code', 'location_name',
            'aisle', 'shelf', 'bin', 'is_active', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
            


class StockAddForm(forms.Form):
    """Form for adding stock."""
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all())
    location = forms.ModelChoiceField(queryset=StockLocation.objects.all(), required=False)
    quantity = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    unit_cost = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant)
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
            self.fields['location'].queryset = StockLocation.objects.filter(tenant=tenant, is_active=True)


class StockRemoveForm(forms.Form):
    """Form for removing stock."""
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all())
    location = forms.ModelChoiceField(queryset=StockLocation.objects.all(), required=False)
    quantity = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    reason = forms.ChoiceField(choices=[
        ('sale', 'Sale'),
        ('damage', 'Damage'),
        ('expired', 'Expired'),
        ('other', 'Other'),
    ])
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant)
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
            self.fields['location'].queryset = StockLocation.objects.filter(tenant=tenant, is_active=True)


class StockTransferForm(forms.Form):
    """Form for transferring stock between warehouses."""
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    from_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label='From Warehouse')
    from_location = forms.ModelChoiceField(queryset=StockLocation.objects.all(), required=False, label='From Location')
    to_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label='To Warehouse')
    to_location = forms.ModelChoiceField(queryset=StockLocation.objects.all(), required=False, label='To Location')
    quantity = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant)
            self.fields['from_warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
            self.fields['to_warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
            self.fields['from_location'].queryset = StockLocation.objects.filter(tenant=tenant, is_active=True)
            self.fields['to_location'].queryset = StockLocation.objects.filter(tenant=tenant, is_active=True)


class StockAdjustmentForm(forms.ModelForm):
    """Form for creating stock adjustments."""
    
    class Meta:
        model = StockAdjustment
        fields = ['warehouse', 'reason', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)


class StockAdjustmentLineForm(forms.ModelForm):
    """Form for adjustment line items."""
    
    class Meta:
        model = StockAdjustmentLine
        fields = ['product', 'location', 'system_quantity', 'actual_quantity']

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant, is_active=True)
            self.fields['location'].queryset = StockLocation.objects.filter(tenant=tenant, is_active=True)


class ReorderRuleForm(forms.ModelForm):
    """Form for creating/editing reorder rules."""
    
    class Meta:
        model = ReorderRule
        fields = [
            'product', 'warehouse', 'min_quantity', 'reorder_quantity',
            'max_quantity', 'lead_time_days', 'is_active'
        ]
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant)
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant)
            self.fields['warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)


class TransferCreateForm(forms.ModelForm):
    """Form for creating a new transfer."""
    class Meta:
        model = InterStoreTransfer
        fields = ['source_warehouse', 'destination_warehouse', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['source_warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)
            self.fields['destination_warehouse'].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True)


class TransferLineForm(forms.Form):
    """Form for adding products to a transfer."""
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    quantity = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant, is_active=True)

TransferLineFormSet = formset_factory(TransferLineForm, extra=1)

