# core/commissions/forms.py
from django import forms
from .models import CommissionPlan, CommissionRule
from products.models import Product
from django.contrib.auth.models import User


class CommissionPlanForm(forms.ModelForm):
    class Meta:
        model = CommissionPlan
        fields = ['commission_plan_name', 'commission_plan_description', 'commission_plan_is_active', 'basis', 'period']
        widgets = {
            'commission_plan_name': forms.TextInput(attrs={'class': 'form-control'}),
            'commission_plan_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'commission_plan_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'basis': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
        }


class CommissionRuleForm(forms.ModelForm):
    class Meta:
        model = CommissionRule
        fields = [
            'product', 'product_category', 'rate_type', 'rate_value', 
            'tier_min_amount', 'tier_max_amount', 'performance_threshold', 
            'split_with', 'split_percentage'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'product_category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product category'}),
            'rate_type': forms.Select(attrs={'class': 'form-select'}),
            'rate_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Rate value'}),
            'tier_min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Min amount'}),
            'tier_max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Max amount (optional)'}),
            'performance_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Threshold for accelerator/decelerator'}),
            'split_with': forms.Select(attrs={'class': 'form-select'}),
            'split_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Percentage for split'}),
        }

    def __init__(self, *args, **kwargs):
        # Accept plan instance to filter rules
        plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)
        
        # Filter products and users
        self.fields['product'].queryset = Product.objects.all()
        self.fields['split_with'].queryset = User.objects.all()
        
        # Update help texts for better UX
        self.fields['rate_value'].help_text = "Percentage (e.g. 10.00 for 10%) or fixed amount"
        self.fields['tier_max_amount'].help_text = "Leave blank for infinity"
        self.fields['performance_threshold'].help_text = "Performance threshold for accelerator/decelerator (e.g., 90 for 90% attainment)"
        self.fields['split_percentage'].help_text = "Percentage of commission to give to the split user (e.g., 50 for 50%)"
        
        # Add conditional field logic using data attributes for frontend
        for field_name in ['tier_min_amount', 'tier_max_amount']:
            self.fields[field_name].widget.attrs['data-condition'] = 'rate_type:tiered'
        
        for field_name in ['performance_threshold']:
            self.fields[field_name].widget.attrs['data-condition'] = 'rate_type:accelerator,decelerator'
        
        for field_name in ['split_with', 'split_percentage']:
            self.fields[field_name].widget.attrs['data-condition'] = 'rate_type:flat,tiered'