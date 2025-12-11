from django import forms
from core.models import User
from core.models import User as Account
from accounts.models import  Contact
from .models import Case

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

class CaseForm(forms.ModelForm):
    """
    Form for creating and updating customer support cases.
    Includes account selection, contact assignment, and priority settings.
    """
    # Account field with dynamic queryset
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        help_text="Select the customer account for this case"
    )
    
    # Contact field that depends on selected account
    contact = forms.ModelChoiceField(
        queryset=Contact.objects.none(),
        required=False,
        help_text="Select a primary contact for this case (optional)"
    )
    
    # Owner field for assignment
    owner = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        help_text="Assign this case to a support agent"
    )
    
    # Priority field with clear options
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        initial='medium',
        help_text="Set the priority level for SLA calculations"
    )

    class Meta:
        model = Case
        fields = [
            'subject', 'case_description', 'account', 'contact', 
            'priority', 'owner', 'assigned_team'
        ]
        widgets = {
            'subject': forms.TextInput(attrs={
                'placeholder': 'e.g., Login Issue, Billing Question, Feature Request'
            }),
            'case_description': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Provide detailed information about the customer issue...'
            }),
            'assigned_team': forms.TextInput(attrs={
                'placeholder': 'e.g., Support, Billing, Technical'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter accounts to user's visible set
            from core.object_permissions import AccountObjectPolicy
            self.fields['account'].queryset = AccountObjectPolicy.get_viewable_queryset(
                user, 
                Account.objects.all()
            )
            
            # Set initial account if provided
            account_id = self.data.get('account') or self.initial.get('account')
            if account_id:
                try:
                    account = Account.objects.get(id=account_id)
                    self.fields['account'].initial = account
                    # Populate contacts for selected account
                    self.fields['contact'].queryset = Contact.objects.filter(account=account)
                except Account.DoesNotExist:
                    pass
            
            # Owner field - filter to active users in tenant
            self.fields['owner'].queryset = User.objects.filter(
                is_active=True,
                tenant_id=user.tenant_id
            )
            
            # Auto-assign owner for non-admin users
            if not user.has_perm('cases:*'):
                self.fields['owner'].queryset = User.objects.filter(id=user.id)
                self.fields['owner'].initial = user
                self.fields['owner'].disabled = True
        else:
            # Fallback - show all accounts (shouldn't happen in normal use)
            self.fields['account'].queryset = Account.objects.all()
            self.fields['contact'].queryset = Contact.objects.none()

    def clean_subject(self):
        """Validate case subject."""
        subject = self.cleaned_data['subject']
        if not subject or len(subject.strip()) < 5:
            raise forms.ValidationError("Subject must be at least 5 characters long.")
        return subject.strip()

    def clean_case_description(self):
        """Validate case description."""
        description = self.cleaned_data['case_description']
        if not description or len(description.strip()) < 10:
            raise forms.ValidationError("Description must be at least 10 characters long.")
        return description.strip()

    def clean(self):
        """Validate form-level constraints."""
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        contact = cleaned_data.get('contact')
        
        if contact and account and contact.account != account:
            raise forms.ValidationError("Selected contact does not belong to the selected account.")
        
        return cleaned_data

    def save(self, commit=True):
        """Save the case with proper tenant association."""
        case = super().save(commit=False)
        
        # Set tenant_id from user if not set
        if not case.tenant_id and hasattr(self, 'current_user'):
            case.tenant_id = self.current_user.tenant_id
        
        if commit:
            case.save()
        return case