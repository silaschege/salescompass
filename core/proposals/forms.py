from django import forms
from django.forms.models import inlineformset_factory
from core.models import User as Account
from opportunities.models import Opportunity
from .models import Proposal, ProposalTemplate, ProposalEmail, ProposalPDF, ProposalEvent, ProposalSignature, ApprovalStep, ProposalApproval, ApprovalTemplate, ApprovalTemplateStep, ProposalLine



class ProposalForm(forms.ModelForm):
    """
    Form for creating and updating proposals.
    Includes content fields, opportunity selection, and ESG content.
    """
    # Opportunity field with dynamic queryset
    opportunity = forms.ModelChoiceField(
        queryset=Opportunity.objects.none(),
        help_text="Select an opportunity to link this proposal to"
    )
     
    # Content fields
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 15,
            'class': 'form-control',
            'placeholder': 'Enter your proposal content here. You can use HTML tags for formatting.'
        }),
        help_text="Main proposal content (HTML supported)"
    )
    
    esg_section_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
            'class': 'form-control',
            'placeholder': 'Describe the environmental and social impact of this proposal.'
        }),
        required=False,
        help_text="ESG-specific content (optional)"
    )
    
    # Status field (for admin use)
    status = forms.ChoiceField(
        choices=Proposal._meta.get_field('status').choices,
        required=False,
        help_text="Current status of the proposal"
    )

    class Meta:
        model = Proposal
        fields = [
            'title', 'opportunity', 'content', 'esg_section_content', 
            'status', 'approval_template'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Q3 Enterprise Solution Proposal'
            }),
            'opportunity': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'approval_template': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter opportunities to user's visible set
            from core.object_permissions import OpportunityObjectPolicy
            self.fields['opportunity'].queryset = OpportunityObjectPolicy.get_viewable_queryset(
                user, 
                Opportunity.objects.all()
            )
            
            # Filter approval templates to active ones
            self.fields['approval_template'].queryset = ApprovalTemplate.objects.filter(
                is_active=True
            )
            
            # Set initial opportunity if provided in GET parameters
            opportunity_id = self.data.get('opportunity') or self.initial.get('opportunity')
            if opportunity_id:
                try:
                    opportunity = Opportunity.objects.get(id=opportunity_id)
                    self.fields['opportunity'].initial = opportunity
                except Opportunity.DoesNotExist:
                    pass
            
            # For non-admin users, hide status field or limit choices
            if not user.has_perm('proposals:*'):
                # Remove status field for regular users
                if 'status' in self.fields:
                    del self.fields['status']
        else:
            # If no user, show all opportunities (shouldn't happen in normal use)
            self.fields['opportunity'].queryset = Opportunity.objects.all()
            self.fields['approval_template'].queryset = ApprovalTemplate.objects.filter(
                is_active=True
            )
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if user or self.tenant:
            target_tenant = self.tenant or (user.tenant if user else None)
            
            # Filter opportunities to user's visible set
            from core.object_permissions import OpportunityObjectPolicy
            if user:
                self.fields['opportunity'].queryset = OpportunityObjectPolicy.get_viewable_queryset(
                    user, 
                    Opportunity.objects.all()
                )
            elif target_tenant:
                self.fields['opportunity'].queryset = Opportunity.objects.filter(tenant=target_tenant)
            
            # Filter approval templates to active ones
            if target_tenant:
                self.fields['approval_template'].queryset = ApprovalTemplate.objects.filter(
                    tenant=target_tenant, is_active=True
                )
            else:
                self.fields['approval_template'].queryset = ApprovalTemplate.objects.filter(is_active=True)
            
            # ... rest of logic ...

class ProposalTemplateForm(forms.ModelForm):
    # ...
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

class ProposalEmailForm(forms.ModelForm):
    # ...
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        target_tenant = self.tenant or (user.tenant if user else None)
        
        if target_tenant:
            self.fields['proposal'].queryset = Proposal.objects.filter(tenant=target_tenant)
            self.fields['email_template'].queryset = ProposalTemplate.objects.filter(
                tenant=target_tenant, email_template_is_active=True
            )


class ProposalEmailForm(forms.ModelForm):
    """
    Form for creating and updating proposal emails.
    """
    
    class Meta:
        model = ProposalEmail
        fields = ['proposal', 'recipient_email', 'subject', 'tracking_enabled', 'email_template']
        widgets = {
            'proposal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'recipient_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., client@example.com'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email subject'
            }),
            'tracking_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_template': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        help_texts = {
            'tracking_enabled': 'Enable tracking for opens and clicks',
            'email_template': 'Optional template to use for this email',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter proposals to user's visible set
            from core.object_permissions import ProposalObjectPolicy
            self.fields['proposal'].queryset = ProposalObjectPolicy.get_viewable_queryset(
                user, 
                Proposal.objects.all()
            )
            
            # Filter templates to active ones
            self.fields['email_template'].queryset = ProposalTemplate.objects.filter(
                email_template_is_active=True
            )


class ProposalPDFForm(forms.ModelForm):
    """
    Form for creating and updating proposal PDFs.
    """
    
    class Meta:
        model = ProposalPDF
        fields = ['proposal', 'file']
        widgets = {
            'proposal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter proposals to user's visible set
            from core.object_permissions import ProposalObjectPolicy
            self.fields['proposal'].queryset = ProposalObjectPolicy.get_viewable_queryset(
                user, 
                Proposal.objects.all()
            )


class ProposalEventForm(forms.ModelForm):
    """
    Form for creating and updating proposal events.
    """
    
    class Meta:
        model = ProposalEvent
        fields = ['proposal', 'event_type', 'ip_address', 'user_agent', 'duration_sec', 'link_url']
        widgets = {
            'proposal': forms.Select(attrs={
                'class': 'form-select'
                }),
            'event_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ip_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IP address'
            }),
            'user_agent': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'User agent string'
            }),
            'duration_sec': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duration in seconds'
            }),
            'link_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clicked link URL'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter proposals to user's visible set
            from core.object_permissions import ProposalObjectPolicy
            self.fields['proposal'].queryset = ProposalObjectPolicy.get_viewable_queryset(
                user, 
                Proposal.objects.all()
            )


class ProposalSignatureForm(forms.ModelForm):
    """
    Form for capturing proposal signatures.
    """
    
    class Meta:
        model = ProposalSignature
        fields = ['signature_data', 'signer_name', 'signer_title']
        widgets = {
            'signature_data': forms.HiddenInput(),
            'signer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'signer_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Title'
            }),
        }


class ApprovalStepForm(forms.ModelForm):
    """
    Form for creating and updating approval steps.
    """
    
    class Meta:
        model = ApprovalStep
        fields = ['name', 'order', 'is_required']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class ProposalApprovalForm(forms.ModelForm):
    """
    Form for handling proposal approvals.
    """
    
    class Meta:
        model = ProposalApproval
        fields = ['is_approved', 'comments']
        widgets = {
            'is_approved': forms.Select(attrs={
                'class': 'form-select'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any comments about your decision'
            }),
        }


class ApprovalTemplateForm(forms.ModelForm):
    """
    Form for creating and updating approval templates.
    """
    
    class Meta:
        model = ApprovalTemplate
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }



class ApprovalTemplateStepForm(forms.ModelForm):
    """
    Form for managing approval template steps.
    """
    
    class Meta:
        model = ApprovalTemplateStep
        fields = ['template', 'step', 'order']
        widgets = {
            'template': forms.HiddenInput(),
            'step': forms.Select(attrs={
                'class': 'form-select'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }


class ProposalLineForm(forms.ModelForm):
    """
    Form for individual line items in a proposal.
    """
    class Meta:
        model = ProposalLine
        fields = ['product', 'quantity', 'unit_price', 'discount_percent']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input', 'readonly': 'readonly'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control discount-input', 'min': 0, 'max': 100}),
        }

ProposalLineFormSet = inlineformset_factory(
    Proposal, 
    ProposalLine, 
    form=ProposalLineForm,
    extra=1,
    can_delete=True
)
