from django import forms
from core.models import User
from .models import Lead, WebToLeadForm, LeadSource, LeadStatus
from accounts.models import Account

LEAD_SOURCE_CHOICES = [
    ('web', 'Web Form'),
    ('event', 'Event'),
    ('referral', 'Referral'),
    ('ads', 'Paid Ads'),
    ('manual', 'Manual Entry'),
]

INDUSTRY_CHOICES = [
    ('tech', 'Technology'),
    ('manufacturing', 'Manufacturing'),
    ('finance', 'Finance'),
    ('healthcare', 'Healthcare'),
    ('retail', 'Retail'),
    ('energy', 'Energy'),
    ('education', 'Education'),
    ('other', 'Other'),
]


class LeadForm(forms.ModelForm):
    """
    Form for creating and updating leads (general purpose).
    """
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'company', 
            'industry', 'job_title', 'source_ref', 'status_ref', 'description', 
            'title', 'account'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.Select(attrs={'class': 'form-select'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'source_ref': forms.Select(attrs={'class': 'form-select'}),
            'status_ref': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'account': 'Select an existing account if this lead is for an upsell/cross-sell opportunity',
            'title': 'Custom title for this lead (e.g., "ESG Champion", "Decision Maker")',
            'description': 'Additional notes about this lead and their interests',
        }
        labels = {
            'source_ref': 'Lead Source',
            'status_ref': 'Status',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter accounts to user's tenant and active accounts only
            self.fields['account'].queryset = Account.objects.filter(
                tenant_id=user.tenant_id,
                status='active'
            )
            
            # Filter dynamic configuration fields
            self.fields['source_ref'].queryset = LeadSource.objects.filter(
                tenant_id=user.tenant_id, is_active=True
            )
            self.fields['status_ref'].queryset = LeadStatus.objects.filter(
                tenant_id=user.tenant_id, is_active=True
            )
        else:
            # If no user, show only active accounts
            self.fields['account'].queryset = Account.objects.filter(status='active')
        
        # Make required fields
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['company'].required = True
        self.fields['source_ref'].required = True
        self.fields['status_ref'].required = True

    def clean_email(self):
        """Ensure email is unique for new leads in the same tenant."""
        email = self.cleaned_data['email']
        tenant_id = getattr(self.instance, 'tenant_id', None)
        
        if not self.instance.pk:  # Only for new leads
            existing_lead = Lead.objects.filter(
                email=email,
                tenant_id=tenant_id,
                status__in=['new', 'contacted', 'qualified']
            ).exists()
            
            if existing_lead:
                raise forms.ValidationError('A lead with this email already exists.')
        
        return email

      



class WebToLeadFormBuilder(forms.ModelForm):
    class Meta:
        model = WebToLeadForm
        fields = [
            'name', 'description', 'is_active', 'success_redirect_url',
            'include_first_name', 'include_last_name', 'include_email',
            'include_phone', 'include_company', 'include_job_title',
            'include_industry', 'custom_fields', 'assign_to', 'assign_to_role'
        ]
        widgets = {
            'custom_fields': forms.Textarea(attrs={'rows': 4}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['assign_to'].queryset = User.objects.filter(
                is_active=True,
                tenant_id=user.tenant_id
            )


class WebToLeadSubmissionForm(forms.Form):
    """Dynamically generated form for web-to-lead submissions."""
    
    def __init__(self, *args, **kwargs):
        form_config = kwargs.pop('form_config', None)
        super().__init__(*args, **kwargs)
        
        if form_config:
            if form_config.include_first_name:
                self.fields['first_name'] = forms.CharField(max_length=100)
            if form_config.include_last_name:
                self.fields['last_name'] = forms.CharField(max_length=100)
            if form_config.include_email:
                self.fields['email'] = forms.EmailField()
            if form_config.include_phone:
                self.fields['phone'] = forms.CharField(max_length=20, required=False)
            if form_config.include_company:
                self.fields['company'] = forms.CharField(max_length=255)
            if form_config.include_job_title:
                self.fields['job_title'] = forms.CharField(max_length=100, required=False)
            if form_config.include_industry:
                self.fields['industry'] = forms.ChoiceField(choices=INDUSTRY_CHOICES)
            
            # Add custom fields
            for field_name, field_config in form_config.custom_fields.items():
                field_type = field_config.get('type', 'text')
                if field_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        max_length=field_config.get('max_length', 255),
                        required=field_config.get('required', False)
                    )
                elif field_type == 'select':
                    choices = [(opt, opt) for opt in field_config.get('options', [])]
                    self.fields[field_name] = forms.ChoiceField(choices=choices)