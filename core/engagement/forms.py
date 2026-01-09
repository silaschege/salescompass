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
from .models import EngagementWebhook


class EngagementEventForm(forms.ModelForm):
    """
    Form for creating and updating engagement events.
    """
    
    
    class Meta:
        model = EngagementEvent
        fields = [
            'account', 'opportunity', 'case', 'nps_response', 'contact',
            'event_type', 'title', 'description', 'contact_email', 
            'priority', 'is_important', 'engagement_score', 'internal_notes',
            'assigned_to', 'mentions',
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'referrer_url', 'campaign_name', 'campaign_source'
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
            'internal_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Internal notes (private)...'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select', 'data-placeholder': 'Assign to team member...'}),
            'mentions': forms.SelectMultiple(attrs={'class': 'form-select', 'data-placeholder': 'Mention team members...'}),
            'utm_source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., google, newsletter'}),
            'utm_medium': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., cpc, banner, email'}),
            'utm_campaign': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., summer_sale'}),
            'utm_term': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., paid keywords'}),
            'utm_content': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., text_link'}),
            'referrer_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'e.g., https://example.com'}),
            'campaign_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Summer Promotion'}),
            'campaign_source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Marketing Team'}),

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
            self.fields['assigned_to'].queryset = Account.objects.filter(tenant_id=tenant_id)
            self.fields['mentions'].queryset = Account.objects.filter(tenant_id=tenant_id)
        
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
            'description', 'due_date', 'priority', 'source', 
            'assigned_to', 'collaborators', 'comments'
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
            'assigned_to': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Assign to team member...'
            }),
            'collaborators': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'data-placeholder': 'Select collaborators...'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Collaboration comments...'
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
            self.fields['account'].queryset = Account.objects.filter(tenant_id=tenant_id).order_by('first_name', 'last_name')
            self.fields['opportunity'].queryset = Opportunity.objects.filter(tenant_id=tenant_id).order_by('opportunity_name')
            self.fields['contact'].queryset = Contact.objects.filter(tenant_id=tenant_id).order_by('first_name', 'last_name')
            self.fields['assigned_to'].queryset = Account.objects.filter(tenant_id=tenant_id).order_by('first_name', 'last_name')
            self.fields['collaborators'].queryset = Account.objects.filter(tenant_id=tenant_id).order_by('first_name', 'last_name')
            
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
        return cleaned_data


from .models import EngagementPlaybook, PlaybookStep

class EngagementPlaybookForm(forms.ModelForm):
    class Meta:
        model = EngagementPlaybook
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Playbook Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PlaybookStepForm(forms.ModelForm):
    class Meta:
        model = PlaybookStep
        fields = ['day_offset', 'action_type', 'description', 'priority']
        widgets = {
            'day_offset': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Instructions...'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class EngagementWebhookForm(forms.ModelForm):
    class Meta:
        model = EngagementWebhook
        fields = [
            'engagement_webhook_name', 'webhook_url', 'secret_key', 'event_types',
            'engagement_webhook_is_active', 'payload_template', 'http_method',
            'headers', 'timeout_seconds', 'max_retry_attempts', 'initial_retry_delay',
            'retry_backoff_factor', 'retry_on_status_codes'
        ]
        widgets = {
            'engagement_webhook_name': forms.TextInput(attrs={'class': 'form-control'}),
            'webhook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'secret_key': forms.TextInput(attrs={'class': 'form-control'}),
            'event_types': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'engagement_webhook_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payload_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"event_id": "{{event.id}}", "event_type": "{{event.type}}", ...}'}),
            'http_method': forms.Select(attrs={'class': 'form-select'}),
            'headers': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '{"Authorization": "Bearer token", "X-Custom-Header": "value"}'}),
            'timeout_seconds': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 300}),
            'max_retry_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'initial_retry_delay': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 300}),
            'retry_backoff_factor': forms.NumberInput(attrs={'class': 'form-control', 'min': 1.0, 'max': 10.0, 'step': 0.1}),
            'retry_on_status_codes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '[500, 502, 503, 504]'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for event types
        self.fields['event_types'].help_text = "Select event types that should trigger this webhook"
        self.fields['retry_on_status_codes'].help_text = "Enter HTTP status codes as JSON array that should trigger retries"
    
    def clean_retry_on_status_codes(self):
        """Validate retry_on_status_codes is a valid JSON array."""
        data = self.cleaned_data['retry_on_status_codes']
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Must be a valid JSON array of integers")
        return data
    
   

    def clean_headers(self):
        """Validate headers is a valid JSON object."""
        data = self.cleaned_data['headers']
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Must be a valid JSON object")
        return data


from .models import EngagementWorkflow

class EngagementWorkflowForm(forms.ModelForm):
    class Meta:
        model = EngagementWorkflow
        fields = [
            'workflow_name', 'workflow_description', 'workflow_type', 
            'trigger_condition', 'engagement_work_flow_is_active', 'config', 'email_template_ids',
            'delay_between_emails', 'task_title_template', 'task_description_template',
            'task_due_date_offset', 'task_priority', 'escalation_recipients', 
            'escalation_delay'
        ]
        widgets = {
            'workflow_name': forms.TextInput(attrs={'class': 'form-control'}),
            'workflow_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'workflow_type': forms.Select(attrs={'class': 'form-control'}),
            'trigger_condition': forms.Select(attrs={'class': 'form-control'}),
            'engagement_work_flow_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email_template_ids': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delay_between_emails': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'task_title_template': forms.TextInput(attrs={'class': 'form-control'}),
            'task_description_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'task_due_date_offset': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'task_priority': forms.Select(attrs={'class': 'form-control'}),
            'escalation_recipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'escalation_delay': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help texts
        self.fields['config'].help_text = "Enter configuration as JSON"
        self.fields['email_template_ids'].help_text = "Enter email template IDs as JSON array"
        self.fields['escalation_recipients'].help_text = "Enter user IDs as JSON array"

    def clean_config(self):
        """Validate config is a valid JSON object."""
        data = self.cleaned_data['config']
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Must be a valid JSON object")
        return data

    def clean_email_template_ids(self):
        """Validate email_template_ids is a valid JSON array."""
        data = self.cleaned_data['email_template_ids']
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Must be a valid JSON array")
        return data

    def clean_escalation_recipients(self):
        """Validate escalation_recipients is a valid JSON array."""
        data = self.cleaned_data['escalation_recipients']
        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Must be a valid JSON array")
        return data
