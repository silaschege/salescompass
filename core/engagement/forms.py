# apps/engagement/forms.py
from django import forms
from .models import NextBestAction, EngagementEvent
from accounts.models import  Contact
from opportunities.models import Opportunity
from cases.models import Case
from core.templatetags.filters_extras import get
from nps.models import NpsResponse
from django.utils import timezone
from core.models import User as Account

class EngagementEventForm(forms.ModelForm):
    """
    Form for creating and updating engagement events.
    """
    
    class Meta:
        model = EngagementEvent
        fields = [
            'account', 'opportunity', 'case', 'nps_response', 'contact',
            'event_type', 'title', 'description', 'contact_email', 
            'priority', 'is_important', 'engagement_score'
        ]
        widgets = {
            
            'engagement_score': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '100'}),
            'account': forms.Select(attrs={'class': 'form-select','data-placeholder': 'Select account (optional)...'}),
            'title': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter source (optional)...'}),
            'event_type': forms.Select(attrs={'class': 'form-select','data-placeholder': 'Select event_type (optional)...'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'opportunity': forms.Select(attrs={'class': 'form-select','data-placeholder': 'Select opportunity(optional)...'}),
            'case': forms.Select(attrs={'class': 'form-select','data-placeholder': 'Select case(optional)...'}),
            'nps_response': forms.Select(attrs={'class': 'form-select','data-placeholder': 'Select nps response(optional)...'}),
            'contact': forms.Select(attrs={'class': 'form-select','data-placeholder': 'Select contact(optional)...'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control','placeholder': 'Enter contact email (optional)...'}),
            'priority': forms.Select(attrs={'class': 'form-select','data-placeholder': 'Select priority  (optional)...'}),
            'is_important': forms.CheckboxInput(),

        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter dropdowns to user's tenant
        if self.user and hasattr(self.user, 'tenant_id'):
            tenant_id = self.user.tenant_id
            
            self.fields['account'].queryset = Account.objects.filter(tenant_id=tenant_id)
            self.fields['opportunity'].queryset = Opportunity.objects.filter(tenant_id=tenant_id)
            self.fields['case'].queryset = Case.objects.filter(tenant_id=tenant_id)
            self.fields['nps_response'].queryset = NpsResponse.objects.filter(tenant_id=tenant_id)
            self.fields['contact'].queryset = Contact.objects.filter(tenant_id=tenant_id)
        
        # Make account required (since it's required in the model)
        self.fields['account'].required = True
        
        # Add help text
        self.fields['engagement_score'].help_text = "Score between 0-100 representing engagement level"

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        
        # Validate engagement_score range
        engagement_score = cleaned_data.get('engagement_score')
        if engagement_score is not None:
            if engagement_score < 0 or engagement_score > 100:
                raise forms.ValidationError(
                    "Engagement score must be between 0 and 100."
                )
        
        # Ensure account is provided (redundant but safe)
        if not cleaned_data.get('account'):
            raise forms.ValidationError("Account is required.")
            
        return cleaned_data

class NextBestActionForm(forms.ModelForm):
    """
    Form for creating and updating Next Best Actions with comprehensive validation.
    
    Features:
    - Tenant-aware dropdown filtering
    - Smart defaults based on user context
    - Comprehensive field validation
    - User-friendly widget configuration
    - Performance optimization
    """
    
    class Meta:
        model = NextBestAction
        fields = [
            'account', 'opportunity', 'contact', 'action_type', 
            'description', 'due_date', 'priority', 'source'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select account...'
            }),
            'opportunity': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select opportunity (optional)...'
            }),
            'contact': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select contact (optional)...'
            }),
            'action_type': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select action type...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Describe the recommended action in detail...'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local',
                'placeholder': 'Select due date and time...'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select priority...'
            }),
            'source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Source system (e.g., ESG Engine, Health Predictor)...'
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize form with tenant-aware dropdowns and smart defaults.
        
        Args:
            user: Current user for tenant filtering and defaults
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            tenant_id = getattr(user, 'tenant_id', None)
            
            # Filter dropdowns to user's tenant
            self.fields['account'].queryset = Account.objects.filter(tenant_id=tenant_id).order_by('name')
            self.fields['opportunity'].queryset = Opportunity.objects.filter(tenant_id=tenant_id).order_by('name')
            self.fields['contact'].queryset = Contact.objects.filter(tenant_id=tenant_id).order_by('first_name', 'last_name')
            
            # For assigned_to, we'd typically handle this in the view since it's not in the form fields
            # But if you want to make it editable:
            # self.fields['assigned_to'].queryset = User.objects.filter(tenant_id=tenant_id)
            
            # Set smart defaults
            if not self.instance.pk:  # Creating new action
                self.fields['source'].initial = 'Manual Entry'
                # Due date default to tomorrow
                from datetime import datetime, timedelta
                tomorrow = datetime.now() + timedelta(days=1)
                self.fields['due_date'].initial = tomorrow.replace(second=0, microsecond=0)
            else:  # Updating existing action
                if not self.instance.source:
                    self.fields['source'].initial = 'Manual Entry'

    def clean(self):
        """
        Validate form data with comprehensive business rules.
        
        Validation rules:
        - Account is required
        - Due date cannot be in the past (for new actions)
        - Opportunity and contact must belong to the selected account
        """
        cleaned_data = super().clean()
        
        account = cleaned_data.get('account')
        opportunity = cleaned_data.get('opportunity')
        contact = cleaned_data.get('contact')
        due_date = cleaned_data.get('due_date')
        
        # Account is required
        if not account:
            raise forms.ValidationError("Account is required.")
        
        # Validate opportunity belongs to account
        if opportunity and opportunity.account != account:
            raise forms.ValidationError("Selected opportunity does not belong to the selected account.")
        
        # Validate contact belongs to account
        if contact and contact.account != account:
            raise forms.ValidationError("Selected contact does not belong to the selected account.")
        
        # Due date validation (only for new actions or if due date changed)
        if due_date:
            if not self.instance.pk or self.instance.due_date != due_date:
                if due_date < timezone.now():
                    raise forms.ValidationError("Due date cannot be in the past.")
        
        return cleaned_data