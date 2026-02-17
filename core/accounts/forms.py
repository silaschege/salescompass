from django import forms
from core.models import User
from .models import Contact
from .models import Account



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
    
    # Hierarchy
    parent = forms.ModelChoiceField(
        queryset=Account.objects.none(), # Populated in __init__
        required=False,
        label="Parent Account",
        help_text="Parent company for this account"
    )

    # Team Members (Simple assignment - default role 'other')
    team_members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        label="Team Members",
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'data-placeholder': 'Select team members...'}),
        help_text="Select users to add to the account team"
    )

    class Meta:
        model = Account
        fields = ['account_name', 'parent', 'industry', 'website', 'phone', 'owner',
                 'gdpr_consent', 'ccpa_consent', 'is_active']
        widgets = {
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.Select(attrs={'class': 'form-select'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'gdpr_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ccpa_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)  # Inject current user for filtering
        super().__init__(*args, **kwargs)
        
        # Populate parent choices (exclude self to avoid loops if editing)
        self.fields['parent'].queryset = Account.objects.all()
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Account.objects.exclude(pk=self.instance.pk)
            # Initialize team members
            self.fields['team_members'].initial = self.instance.users.all()

        # Only admins can assign owners; others see only themselves
        if user and not user.has_perm('accounts:*'):
            self.fields['owner'].queryset = User.objects.filter(id=user.id)
            self.fields['owner'].initial = user
            self.fields['owner'].disabled = True

    def save(self, commit=True):
        account = super().save(commit=False)
        if commit:
            account.save()
            
        if account.pk:
            # Handle Team Members
            from .models import AccountTeamMember
            selected_users = self.cleaned_data.get('team_members', [])
            current_users = list(account.users.all())
            
            # Add new
            for user in selected_users:
                if user not in current_users:
                    AccountTeamMember.objects.create(account=account, user=user, role='other')
            
            # Remove unselected (Optional: might want to be careful here not to delete roles)
            # For this simple UI, we assume "Members" list is authoritative for membership
            # But converting to through model implies we should probably be careful.
            # However, simpler requirement: "assign team members in the UI".
            # Logic: If user was in team but not in selected, remove them.
            if selected_users:
                AccountTeamMember.objects.filter(account=account).exclude(user__in=selected_users).delete()
            else:
                 AccountTeamMember.objects.filter(account=account).delete()

        return account


class ContactForm(forms.ModelForm):
    """
    Form for creating and updating contacts.
    """
    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'account', 'role', 
            'communication_preference', 'is_primary', 'esg_influence'
        ]
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
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
                User.objects.all()
            )
        
        # Set required fields
        self.fields['account'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        """Ensure email is unique across all contacts, not just within an account."""
        email = self.cleaned_data['email']
        
        # Check if email already exists
        qs = Contact.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError(
                'This email is already in use by another contact.'
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

