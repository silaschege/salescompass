from django import forms
from .models import Product, PricingTier, ProductBundle, BundleItem, CompetitorProduct

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
            'esg_certified', 'carbon_footprint', 'esg_certifications', 'sustainability_notes', 'tco2e_saved',
            'product_is_active', 'available_from', 'available_to'
        ]
        widgets = {
            'product_description': forms.Textarea(attrs={'rows': 4}),
            'sustainability_notes': forms.Textarea(attrs={'rows': 3}),
            'pricing_model': forms.Select(choices=PRICING_MODEL_CHOICES),
            'esg_certifications': forms.SelectMultiple(choices=ESG_CERTIFICATION_CHOICES),
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_to': forms.DateInput(attrs={'type': 'date'}),
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
            'min_quantity': forms.NumberInput(attrs={'min': 1}),
            'max_quantity': forms.NumberInput(attrs={'min': 1}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'discount_percent': forms.NumberInput(attrs={'step': '0.1', 'max': 100}),
        }


class ProductBundleForm(forms.ModelForm):
    class Meta:
        model = ProductBundle
        fields = ['product_bundle_name', 'product_bundle_description', 'bundle_price', 'product_bundle_is_active']
        widgets = {
            'product_bundle_description': forms.Textarea(attrs={'rows': 3}),
        }


class CompetitorProductForm(forms.ModelForm):
    class Meta:
        model = CompetitorProduct
        fields = [
            'competitor_product_name', 'competitor_name', 'competitor_sku', 
            'competitive_advantage', 'price_difference_percent', 'is_direct_competitor'
        ]
        widgets = {
            'competitive_advantage': forms.Textarea(attrs={'rows': 3}),
            'price_difference_percent': forms.NumberInput(attrs={'step': '0.1'}),
        }