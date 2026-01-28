from django import forms
from django import forms
from .models import (
    Product, ProductCategory, PricingTier, ProductBundle, BundleItem, 
    CompetitorProduct, ProductComparison, ProductDependency,
    PriceList, PriceListItem, Coupon, Promotion, Supplier
)

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
            'image', 'thumbnail', 'base_price', 'pricing_model', 'currency', 'tax_rate',
            'is_subscription', 'billing_cycle', 'subscription_term', 'auto_renewal',
            'esg_certified', 'carbon_footprint', 'tco2e_saved', 'esg_certifications', 'sustainability_notes',
            'product_is_active', 'available_from', 'available_to', 'track_inventory',
            'low_stock_threshold', 'weight', 'length', 'width', 'height',
            'valuation_method', 'is_capital_asset', 'nrv', 'ssp_min', 'ssp_max',
            'preferred_supplier'
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'upc': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tag1, tag2'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pricing_model': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.Select(attrs={'class': 'form-select'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}),
            'subscription_term': forms.NumberInput(attrs={'class': 'form-control'}),
            'carbon_footprint': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'esg_certifications': forms.TextInput(attrs={'class': 'form-control'}),
            'available_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'available_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'valuation_method': forms.Select(attrs={'class': 'form-select'}),
            'nrv': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ssp_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ssp_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tco2e_saved': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sustainability_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'product_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'track_inventory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_capital_asset': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_subscription': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_renewal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esg_certified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preferred_supplier': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.esg_certifications:
            self.fields['esg_certifications'].initial = self.instance.get_certifications_list()
        if tenant:
             self.fields['category'].queryset = ProductCategory.objects.filter(tenant=tenant)
             self.fields['preferred_supplier'].queryset = Supplier.objects.filter(tenant=tenant)

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'slug', 'parent', 'description', 'image', 'display_order', 'is_active']
        # ... widgets ...
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['parent'].queryset = ProductCategory.objects.filter(tenant=tenant)

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

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)


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
        fields = ['primary_product', 'dependent_product', 'dependency_type']
        widgets = {
            'primary_product': forms.Select(attrs={'class': 'form-select'}),
            'dependent_product': forms.Select(attrs={'class': 'form-select'}),
            'dependency_type': forms.Select(attrs={'class': 'form-select'}),
        }

class PriceListForm(forms.ModelForm):
    class Meta:
        model = PriceList
        fields = ['name', 'description', 'currency', 'is_default', 'is_active', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class PriceListItemForm(forms.ModelForm):
    class Meta:
        model = PriceListItem
        fields = ['price_list', 'product', 'price', 'min_quantity']
        widgets = {
            'price_list': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'description', 'discount_type', 'discount_value', 'min_purchase_amount', 
                  'start_date', 'end_date', 'usage_limit', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['name', 'description', 'discount_type', 'discount_value', 
                  'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_name', 'contact_person', 'email', 'phone', 'address', 'website', 'is_active']
        widgets = {
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }