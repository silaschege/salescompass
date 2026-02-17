from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_city', 'shipping_country', 'shipping_zip',
            'payment_method', 'notes'
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '123 Street... '}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_zip': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(choices=[
                ('cod', 'Cash on Delivery'),
                ('stripe', 'Stripe (Credit Card)'),
                ('mpesa', 'M-Pesa')
            ], attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Special instructions...'}),
        }
