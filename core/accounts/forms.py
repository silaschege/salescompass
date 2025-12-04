from django import forms
from core.models import User
from .models import Account, Contact


class AccountForm(forms.ModelForm):
    """
    Form for creating/updating accounts.
    Includes ESG and compliance fields.
    """
    # Owner field (for assignment)
    owner = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        help_text="Assign an owner (e.g., Account Executive)"
    )

    # Compliance
    gdpr_consent = forms.BooleanField(
        required=False,
        label="GDPR Consent",
        help_text="Customer consents to data processing under GDPR"
    )
    ccpa_consent = forms.BooleanField(
        required=False,
        label="CCPA Consent",
        help_text="Customer consents to data processing under CCPA"
    )

    class Meta:
        model = Account
        fields = [
            'name', 'industry', 'tier', 'website', 'country', 'address',
            'esg_engagement', 'sustainability_goals',
            'renewal_date', 'owner',
            'gdpr_consent', 'ccpa_consent'
        ]
        widgets = {
            'name':forms.TextInput(attrs={'class': 'form-control'}),
            'industry':forms.Select(attrs={'class': 'form-select'}),
            'tier': forms.Select(attrs={'class': 'form-select'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'country':forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'esg_engagement': forms.Select(attrs={'class': 'form-select'}),
            'sustainability_goals': forms.Textarea(attrs={'rows': 3,'class': 'form-control'}),
            'renewal_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'gdpr_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ccpa_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)  # Inject current user for filtering
        super().__init__(*args, **kwargs)
        
        # Only admins can assign owners; others see only themselves
        if user and not user.has_perm('accounts:*'):
            self.fields['owner'].queryset = User.objects.filter(id=user.id)
            self.fields['owner'].initial = user
            self.fields['owner'].disabled = True

 


class ContactForm(forms.ModelForm):
    """
    Form for creating and updating contacts.
    """
    class Meta:
        model = Contact
        fields = [
            'account', 'first_name', 'last_name', 'email', 'phone', 
            'role', 'communication_preference', 'is_primary', 'esg_influence'
        ]
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'communication_preference': forms.Select(attrs={'class': 'form-select'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esg_influence': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'is_primary': 'Primary contact for the account',
            'esg_influence': 'Level of influence on ESG decisions',
            'communication_preference': 'Preferred method for communications',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter accounts to user's viewable accounts
            from core.object_permissions import AccountObjectPolicy
            self.fields['account'].queryset = AccountObjectPolicy.get_viewable_queryset(
                user, 
                Account.objects.all()
            )
        
        # Set required fields
        self.fields['account'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        """Ensure email is unique within the account."""
        email = self.cleaned_data['email']
        account = self.cleaned_data.get('account')
        
        if account:
            # Check if email already exists for this account
            qs = Contact.objects.filter(account=account, email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError(
                    'This email already exists for this account.'
                )
        
        return email

    def clean(self):
        """Ensure only one primary contact per account."""
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        is_primary = cleaned_data.get('is_primary', False)
        
        if account and is_primary:
            # Check if there's already a primary contact for this account
            qs = Contact.objects.filter(account=account, is_primary=True)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError(
                    'This account already has a primary contact. '
                    'Please uncheck "Primary" or update the existing primary contact.'
                )
        
        return cleaned_data

class BulkImportUploadForm(forms.Form):
    """
    Form for uploading CSV files for bulk account import.
    """
    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with account data. Must include: name, industry, country."
    )

    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        if not file.name.endswith('.csv'):
            raise forms.ValidationError("Only CSV files are allowed.")
        return file