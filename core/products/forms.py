from django import forms
from .models import Product, PricingTier, ProductBundle, BundleItem, CompetitorProduct, ProductComparison, ProductDependency

PRICING_MODEL_CHOICES = [
    ('flat', 'Flat Fee'),
    ('per_unit', 'Per Unit'),
    ('tiered', 'Tiered'),
    ('subscription', 'Subscription'),
]

ESG_CERTIFICATION_CHOICES = [
    ('iso14001', 'ISO 14001'),
    ('energy_star', 'Energy Star'),
    ('epa', 'EPA Certified'),
    ('none', 'None'),
]

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_name', 'product_description', 'sku', 'upc', 'category', 'tags',
            'base_price', 'pricing_model', 'currency',
            'is_subscription', 'billing_cycle', 'subscription_term', 'auto_renewal',
            'esg_certified', 'carbon_footprint', 'esg_certifications', 'sustainability_notes', 'tco2e_saved',
            'product_is_active', 'available_from', 'available_to'
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'upc': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pricing_model': forms.Select(attrs={'class': 'form-select'}, choices=PRICING_MODEL_CHOICES),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'is_subscription': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('monthly', 'Monthly'),
                ('quarterly', 'Quarterly'),
                ('annually', 'Annually'),
                ('one_time', 'One-Time'),
            ]),
            'subscription_term': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_renewal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esg_certified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'carbon_footprint': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'esg_certifications': forms.SelectMultiple(attrs={'class': 'form-select'}, choices=ESG_CERTIFICATION_CHOICES),
            'sustainability_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tco2e_saved': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'product_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'available_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'available_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Set initial value for certifications
            if self.instance.esg_certifications:
                self.fields['esg_certifications'].initial = self.instance.get_certifications_list()


class PricingTierForm(forms.ModelForm):
    class Meta:
        model = PricingTier
        fields = ['min_quantity', 'max_quantity', 'unit_price', 'discount_percent']
        widgets = {
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'max_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'max': 100}),
        }


class ProductBundleForm(forms.ModelForm):
    class Meta:
        model = ProductBundle
        fields = ['product_bundle_name', 'product_bundle_description', 'bundle_price', 'product_bundle_is_active']
        widgets = {
            'product_bundle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_bundle_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bundle_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'product_bundle_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BundleItemForm(forms.ModelForm):
    class Meta:
        model = BundleItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class CompetitorProductForm(forms.ModelForm):
    class Meta:
        model = CompetitorProduct
        fields = [
            'competitor_product_name', 'competitor_name', 'competitor_sku', 
            'our_product', 'competitive_advantage', 'price_difference_percent', 'is_direct_competitor'
        ]
        widgets = {
            'competitor_product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'competitor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'competitor_sku': forms.TextInput(attrs={'class': 'form-control'}),
            'our_product': forms.Select(attrs={'class': 'form-select'}),
            'competitive_advantage': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price_difference_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'is_direct_competitor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductComparisonForm(forms.ModelForm):
    class Meta:
        model = ProductComparison
        fields = ['product_comparison_name', 'products', 'product_comparison_is_active']
        widgets = {
            'product_comparison_name': forms.TextInput(attrs={'class': 'form-control'}),
            'products': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'product_comparison_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductDependencyForm(forms.ModelForm):
    class Meta:
        model = ProductDependency
        fields = ['product', 'required_product', 'dependency_type']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'required_product': forms.Select(attrs={'class': 'form-select'}),
            'dependency_type': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('required', 'Required'),
                ('recommended', 'Recommended'),
            ]),
        }