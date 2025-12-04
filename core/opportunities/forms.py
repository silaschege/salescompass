from django import forms
from core.models import User
from accounts.models import Account
from products.models import Product
from .models import Opportunity, OpportunityProduct, WinLossAnalysis

STAGE_CHOICES = [
    ('prospecting', 'Prospecting'),
    ('qualification', 'Qualification'),
    ('proposal', 'Proposal'),
    ('negotiation', 'Negotiation'),
    ('closed_won', 'Closed Won'),
    ('closed_lost', 'Closed Lost'),
]

class OpportunityForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        help_text="Select an existing account"
    )
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Opportunity
        fields = [
            'name', 'account', 'amount', 'stage', 'close_date',
            'probability', 'esg_tagged', 'esg_impact_description', 'owner', 'products'
        ]
        widgets = {
            'stage': forms.Select(choices=STAGE_CHOICES),
            'close_date': forms.DateInput(attrs={'type': 'date'}),
            'esg_impact_description': forms.Textarea(attrs={'rows': 3}),
            'probability': forms.NumberInput(attrs={'min': 0, 'max': 1, 'step': 0.01}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Filter accounts to user's visible set
        if user:
            from core.object_permissions import AccountObjectPolicy
            self.fields['account'].queryset = AccountObjectPolicy.get_viewable_queryset(user, Account.objects.all())
            self.fields['products'].queryset = Product.objects.filter(tenant_id=user.tenant_id)
        
        # Owner field
        if user and not user.has_perm('opportunities:*'):
            self.fields['owner'].queryset = User.objects.filter(id=user.id)
            self.fields['owner'].initial = user
            self.fields['owner'].disabled = True

    def save(self, commit=True):
        opportunity = super().save(commit)
        if commit:
            # Handle products
            if 'products' in self.cleaned_data:
                # Clear existing products
                OpportunityProduct.objects.filter(opportunity=opportunity).delete()
                # Add selected products
                for product in self.cleaned_data['products']:
                    OpportunityProduct.objects.create(
                        opportunity=opportunity,
                        product=product,
                        quantity=1,
                        unit_price=product.base_price
                    )
        return opportunity


class WinLossAnalysisForm(forms.ModelForm):
    class Meta:
        model = WinLossAnalysis
        fields = ['is_won', 'win_reason', 'loss_reason', 'competitor_name', 'sales_cycle_days']
        widgets = {
            'win_reason': forms.Textarea(attrs={'rows': 3}),
            'loss_reason': forms.Textarea(attrs={'rows': 3}),
        }