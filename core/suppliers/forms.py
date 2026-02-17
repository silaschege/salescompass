from django import forms
from .models import Supplier, SupplierCategory, SupplierContact, SupplierDocument, SupplierPerformanceReview


class SupplierForm(forms.ModelForm):
    """Form for creating/editing suppliers."""
    
    class Meta:
        model = Supplier
        fields = [
            'supplier_name', 'supplier_code', 'category',
            'contact_person', 'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'tax_id', 'registration_number',
            'bank_name', 'bank_account', 'bank_branch',
            'payment_terms', 'credit_limit', 'currency',
            'classification', 'status', 'is_active', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'address_line1': forms.TextInput(attrs={'placeholder': 'Street address'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Suite, unit, etc.'}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = SupplierCategory.objects.filter(tenant=tenant, is_active=True)
        
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SupplierCategoryForm(forms.ModelForm):
    """Form for supplier categories."""
    
    class Meta:
        model = SupplierCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SupplierContactForm(forms.ModelForm):
    """Form for supplier contacts."""
    
    class Meta:
        model = SupplierContact
        fields = ['name', 'title', 'email', 'phone', 'is_primary']
    
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['class'] = 'form-control'


class SupplierDocumentForm(forms.ModelForm):
    """Form for supplier documents."""
    
    class Meta:
        model = SupplierDocument
        fields = ['document_type', 'name', 'file', 'expiry_date', 'notes']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SupplierPerformanceReviewForm(forms.ModelForm):
    """Form for supplier performance reviews."""
    
    class Meta:
        model = SupplierPerformanceReview
        fields = ['date', 'delivery_rating', 'quality_rating', 'responsiveness_rating', 'comments']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
