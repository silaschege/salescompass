from django import forms
from .models import InspectionRule, InspectionLog, NonConformanceReport, CAPA, QualityCheckLibrary

class InspectionRuleForm(forms.ModelForm):
    class Meta:
        model = InspectionRule
        fields = ['name', 'product', 'check_list', 'is_required_on_receipt', 'sampling_type', 'aql_level', 'inspection_level']
        widgets = {
            'check_list': forms.HiddenInput(),  # Populated by JS builder
            'product': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sampling_type': forms.Select(attrs={'class': 'form-select'}),
            'aql_level': forms.Select(attrs={'class': 'form-select'}),
            'inspection_level': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            from products.models import Product
            self.fields['product'].queryset = Product.objects.filter(tenant=self.tenant)

class CAPAForm(forms.ModelForm):
    class Meta:
        model = CAPA
        fields = ['title', 'capa_type', 'description', 'root_cause', 'action_plan', 'verification_plan', 'assigned_to', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'capa_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'root_cause': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'action_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'verification_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            # CAPAForm doesn't have a 'product' field; filtering 'assigned_to' or others if they existed
            # For now, just ensuring it doesn't crash trying to access 'product'
            pass

class InspectionLogForm(forms.ModelForm):
    class Meta:
        model = InspectionLog
        fields = ['rule', 'source_reference', 'status', 'results_data', 'comments']
        widgets = {
            'results_data': forms.HiddenInput(), # Populated by JS
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'rule': forms.Select(attrs={'class': 'form-select'}),
            'source_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['rule'].queryset = self.fields['rule'].queryset.filter(tenant=self.tenant)

class NCRManagementForm(forms.ModelForm):
    class Meta:
        model = NonConformanceReport
        fields = ['root_cause', 'action_taken', 'rca_type', 'rca_data', 'resolved_at']
        widgets = {
            'root_cause': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'action_taken': forms.Select(attrs={'class': 'form-select'}),
            'rca_type': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleRCAUI(this.value)'}),
            'rca_data': forms.HiddenInput(),
            'resolved_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

class QualityCheckLibraryForm(forms.ModelForm):
    class Meta:
        model = QualityCheckLibrary
        fields = ['label', 'check_type', 'category', 'description', 'is_active']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Is the product clean?'}),
            'check_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Packaging'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional instructions...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
