from django import forms
from .models import (
    POSTerminal, POSSession, POSTransaction, POSRefund
)
from inventory.models import Warehouse
from decimal import Decimal


class TerminalForm(forms.ModelForm):
    """Form for creating/editing POS terminals."""
    
    class Meta:
        model = POSTerminal
        fields = [
            'terminal_name', 'terminal_code', 'warehouse', 'location',
            'is_active', 'allow_negative_stock', 'require_customer',
            'auto_print_receipt', 'receipt_footer',
            'receipt_printer_name', 'printer_type', 'printer_ip', 'printer_port', 'printer_width',
            'barcode_scanner_enabled', 'cash_drawer_enabled',
            'customer_display_enabled', 'customer_display_port'
        ]
        widgets = {
            'receipt_footer': forms.Textarea(attrs={'rows': 3}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Front Counter, Back Office'}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(
                tenant=tenant, is_active=True
            )


class SessionOpenForm(forms.Form):
    """Form for opening a POS session."""
    terminal = forms.ModelChoiceField(queryset=POSTerminal.objects.all())
    opening_cash = forms.DecimalField(
        min_value=0, 
        max_digits=12, 
        decimal_places=2,
        initial=0,
        help_text="Count the cash in the drawer before starting"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), 
        required=False
    )
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['terminal'].queryset = POSTerminal.objects.filter(
                tenant=tenant, is_active=True
            )


class SessionCloseForm(forms.Form):
    """Form for closing a POS session."""
    closing_cash = forms.DecimalField(
        min_value=0, 
        max_digits=12, 
        decimal_places=2,
        help_text="Count all cash in the drawer"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), 
        required=False,
        help_text="Any notes about the session or discrepancies"
    )


class TransactionCustomerForm(forms.Form):
    """Form for adding customer info to a transaction."""
    customer_name = forms.CharField(max_length=255, required=False)
    customer_phone = forms.CharField(max_length=50, required=False)
    customer_email = forms.EmailField(required=False)


class TransactionDiscountForm(forms.Form):
    """Form for applying a discount to a transaction."""
    discount_type = forms.ChoiceField(choices=[
        ('percent', 'Percentage'),
        ('amount', 'Fixed Amount'),
    ])
    discount_value = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)
    reason = forms.CharField(max_length=255, required=True)


class PaymentForm(forms.Form):
    """Form for processing a payment."""
    payment_method = forms.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile_money', 'Mobile Money (M-PESA)'),
        ('voucher', 'Voucher/Gift Card'),
    ])
    amount = forms.DecimalField(min_value=0.01, max_digits=14, decimal_places=2)
    reference_number = forms.CharField(max_length=100, required=False)
    
    # Card fields
    card_last_four = forms.CharField(max_length=4, required=False)
    card_type = forms.ChoiceField(choices=[
        ('', '---'),
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
    ], required=False)
    
    # Mobile money fields
    mobile_number = forms.CharField(max_length=20, required=False)
    mobile_provider = forms.ChoiceField(choices=[
        ('', '---'),
        ('mpesa', 'M-PESA'),
        ('airtel', 'Airtel Money'),
        ('tkash', 'T-Kash'),
    ], required=False)
    
    # Voucher fields
    voucher_code = forms.CharField(max_length=50, required=False)


class VoidTransactionForm(forms.Form):
    """Form for voiding a transaction."""
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Explain why this transaction is being voided"
    )


class RefundForm(forms.Form):
    """Form for creating a refund."""
    refund_method = forms.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('card', 'Credit to Card'),
        ('mobile_money', 'Mobile Money'),
        ('credit', 'Store Credit'),
    ])
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Reason for the refund"
    )
    requires_approval = forms.BooleanField(
        initial=True, 
        required=False,
        help_text="Require manager approval before processing"
    )


class CashMovementForm(forms.Form):
    """Form for cash pay in/pay out."""
    amount = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        help_text="Reason for this cash movement"
    )


class ProductSearchForm(forms.Form):
    """Simple product search form."""
    query = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, SKU, or barcode...',
            'class': 'form-control',
            'autofocus': True
        })
    )


class DenominationCountForm(forms.Form):
    """Form for counting cash denominations during session close."""
    # Kenya Shilling denominations
    notes_1000 = forms.IntegerField(min_value=0, initial=0, label='KES 1000 Notes')
    notes_500 = forms.IntegerField(min_value=0, initial=0, label='KES 500 Notes')
    notes_200 = forms.IntegerField(min_value=0, initial=0, label='KES 200 Notes')
    notes_100 = forms.IntegerField(min_value=0, initial=0, label='KES 100 Notes')
    notes_50 = forms.IntegerField(min_value=0, initial=0, label='KES 50 Notes')
    coins_40 = forms.IntegerField(min_value=0, initial=0, label='KES 40 Coins')
    coins_20 = forms.IntegerField(min_value=0, initial=0, label='KES 20 Coins')
    coins_10 = forms.IntegerField(min_value=0, initial=0, label='KES 10 Coins')
    coins_5 = forms.IntegerField(min_value=0, initial=0, label='KES 5 Coins')
    coins_1 = forms.IntegerField(min_value=0, initial=0, label='KES 1 Coins')
    
    def calculate_total(self):
        """Calculate total from denomination counts."""
        denominations = {
            'notes_1000': 1000,
            'notes_500': 500,
            'notes_200': 200,
            'notes_100': 100,
            'notes_50': 50,
            'coins_40': 40,
            'coins_20': 20,
            'coins_10': 10,
            'coins_5': 5,
            'coins_1': 1,
        }
        total = Decimal('0')
        for field, value in denominations.items():
            count = self.cleaned_data.get(field, 0)
            total += Decimal(str(count * value))
        return total
