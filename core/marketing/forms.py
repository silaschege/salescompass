# apps/marketing/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    MarketingCampaign, EmailTemplate, LandingPage, 
    AbTest, AbVariant, Unsubscribe, CampaignPerformance, LandingPageBlock,
    DripCampaign, DripStep, DripEnrollment
)
from .utils import calculate_campaign_roi, send_campaign_email

class MarketingCampaignForm(forms.ModelForm):
    class Meta:
        model = MarketingCampaign
        fields = [
            'name', 'description', 'status', 'send_date', 'timezone',
            'target_list', 'segment_filter'
        ]
        widgets = {
            'send_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'target_list': forms.Textarea(attrs={'rows': 3}),
            'segment_filter': forms.Textarea(attrs={'rows': 3}),
        }

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject_line', 'html_content', 'text_content', 'category', 'description', 'is_shared', 'is_active']
        widgets = {
            'html_content': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'text_content': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class LandingPageForm(forms.ModelForm):
    class Meta:
        model = LandingPage
        fields = ['title', 'slug', 'campaign', 'html_content', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Q4 Product Launch Landing Page'
            }),
            'slug': forms.TextInput(attrs={
                'placeholder': 'e.g., product-launch-2025'
            }),
            'html_content': forms.Textarea(attrs={
                'rows': 15,
                'placeholder': '<!DOCTYPE html>\n<html>\n<head>\n    <title>Your Landing Page</title>\n</head>\n<body>\n    <!-- Your content here -->\n</body>\n</html>'
            }),
        }

class AbTestForm(forms.ModelForm):
    class Meta:
        model = AbTest
        fields = ['campaign', 'name', 'is_active', 'min_responses', 'confidence_level']
        widgets = {
            'min_responses': forms.NumberInput(attrs={'min': 100}),
            'confidence_level': forms.NumberInput(attrs={'min': 0.8, 'max': 0.99, 'step': 0.01}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['campaign'].queryset = MarketingCampaign.objects.filter(
                tenant_id=user.tenant_id
            )

AbVariantFormSet = inlineformset_factory(
    AbTest,
    AbVariant,
    fields=['variant', 'email_template', 'landing_page', 'assignment_rate'],
    extra=2,
    max_num=2,
    min_num=2,
    validate_min=True
)

class UnsubscribeForm(forms.ModelForm):
    class Meta:
        model = Unsubscribe
        fields = ['email']



class CampaignPerformanceForm(forms.ModelForm):
    """
    Form for creating/editing campaign performance records.
    Typically used for manual data entry or adjustments.
    """
    class Meta:
        model = CampaignPerformance
        fields = [
            'campaign', 'date', 'open_rate', 'click_rate', 
            'conversion_rate', 'total_sent', 'total_opened', 
            'total_clicked', 'total_conversions', 'revenue_generated'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'open_rate': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '100'}),
            'click_rate': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '100'}),
            'conversion_rate': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '100'}),
        }
        help_texts = {
            'open_rate': 'Percentage of recipients who opened the email (0-100)',
            'click_rate': 'Percentage of recipients who clicked links (0-100)',
            'conversion_rate': 'Percentage of recipients who converted (0-100)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter campaigns to user's tenant
            self.fields['campaign'].queryset = self.fields['campaign'].queryset.filter(
                tenant_id=user.tenant_id
            )

    def clean(self):
        cleaned_data = super().clean()
        open_rate = cleaned_data.get('open_rate', 0)
        click_rate = cleaned_data.get('click_rate', 0)
        conversion_rate = cleaned_data.get('conversion_rate', 0)
        
        if open_rate > 100 or open_rate < 0:
            raise forms.ValidationError("Open rate must be between 0 and 100.")
        if click_rate > 100 or click_rate < 0:
            raise forms.ValidationError("Click rate must be between 0 and 100.")
        if conversion_rate > 100 or conversion_rate < 0:
            raise forms.ValidationError("Conversion rate must be between 0 and 100.")
        
        return cleaned_data


class LandingPageBlockForm(forms.ModelForm):
    """
    Form for creating/editing landing page blocks.
    Used in the drag-and-drop builder interface.
    """
    class Meta: 
        model = LandingPageBlock
        fields = ['block_type', 'title', 'content', 'order', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        landing_page = kwargs.pop('landing_page', None)
        super().__init__(*args, **kwargs)
        if landing_page:
            self.fields['landing_page'].initial = landing_page


class CampaignPerformanceFilterForm(forms.Form):
    """
    Form for filtering campaign performance data in reports.
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    campaign = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['campaign'].queryset = MarketingCampaign.objects.filter(
                tenant_id=user.tenant_id
            )


class DripCampaignForm(forms.ModelForm):
    """
    Form for creating/editing Drip Campaigns.
    """
    class Meta:
        model = DripCampaign
        fields = ['name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class DripStepForm(forms.ModelForm):
    """
    Form for creating/editing Drip Steps.
    """
    class Meta:
        model = DripStep
        fields = ['drip_campaign', 'step_type', 'order', 'email_template', 'wait_days', 'wait_hours']
        widgets = {
            'wait_days': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'wait_hours': forms.NumberInput(attrs={'min': 0, 'max': 23, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        drip_campaign = kwargs.pop('drip_campaign', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['email_template'].queryset = EmailTemplate.objects.filter(
                tenant_id=user.tenant_id,
                is_active=True
            )
        
        if drip_campaign:
            self.fields['drip_campaign'].initial = drip_campaign
            self.fields['drip_campaign'].widget = forms.HiddenInput()


class DripEnrollmentForm(forms.ModelForm):
    """
    Form for enrolling accounts in Drip Campaigns.
    """
    class Meta:
        model = DripEnrollment
        fields = ['drip_campaign', 'account', 'email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            from accounts.models import Account
            self.fields['account'].queryset = Account.objects.filter(
                tenant_id=user.tenant_id
            )
            self.fields['drip_campaign'].queryset = DripCampaign.objects.filter(
                tenant_id=user.tenant_id,
                is_active=True
            )