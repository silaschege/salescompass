from django import forms
from core.models import User as Account
from opportunities.models import Opportunity
from .models import Proposal

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
            'placeholder': 'Enter your proposal content here. You can use HTML tags for formatting.'
        }),
        help_text="Main proposal content (HTML supported)"
    )
    
    esg_section_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
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
            'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Q3 Enterprise Solution Proposal'
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

    def clean_content(self):
        """Validate proposal content."""
        content = self.cleaned_data['content']
        if not content or len(content.strip()) < 10:
            raise forms.ValidationError("Proposal content must be at least 10 characters long.")
        return content

    def clean_title(self):
        """Validate proposal title."""
        title = self.cleaned_data['title']
        if not title or len(title.strip()) < 3:
            raise forms.ValidationError("Proposal title must be at least 3 characters long.")
        return title.strip()

    def save(self, commit=True):
        """Save the proposal with proper user association."""
        proposal = super().save(commit=False)
        
        # Set the sent_by field if this is a new proposal
        if not proposal.pk and hasattr(self, 'current_user'):
            proposal.sent_by = self.current_user
        
        if commit:
            proposal.save()
        return proposal