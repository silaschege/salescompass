from django import forms
from django.core.exceptions import ValidationError
from .models import (
    NotificationTemplate, EmailSMSServiceConfiguration, CommunicationHistory,
    CustomerSupportTicket, FeedbackAndSurvey, Email, SMS, CallLog,
    SocialMediaPost, ChatMessage, EmailSignature
)
from .whatsapp_models import WhatsAppTemplate


class NotificationTemplateForm(forms.ModelForm):
    """Form for creating and editing notification templates"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'name', 'subject', 'body_html', 'body_text', 'template_type',
            'is_active', 'is_default', 'variables', 'tags', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Template name'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email subject or SMS preview'}),
            'body_html': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'HTML content...'}),
            'body_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Plain text content...'}),
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'variables': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'JSON format for variables'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated tags'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmailSMSServiceConfigurationForm(forms.ModelForm):
    """Form for configuring email and SMS services"""
    
    class Meta:
        model = EmailSMSServiceConfiguration
        fields = [
            'name', 'service_type', 'service_provider', 'configuration',
            'is_active', 'is_primary', 'rate_limit_requests', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'service_provider': forms.Select(attrs={'class': 'form-select'}),
            'configuration': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'JSON configuration'}),
            'rate_limit_requests': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommunicationHistoryForm(forms.ModelForm):
    """Form for logging communication history manually"""
    
    class Meta:
        model = CommunicationHistory
        fields = [
            'communication_type', 'direction', 'recipient', 'subject',
            'content_text', 'status', 'sent_at', 'metadata'
        ]
        widgets = {
            'communication_type': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'recipient': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'sent_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class CustomerSupportTicketForm(forms.ModelForm):
    """Form for creating and managing support tickets"""
    
    class Meta:
        model = CustomerSupportTicket
        fields = [
            'subject', 'description', 'ticket_type', 'priority', 'status',
            'assigned_to', 'tags'
        ]
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description of the issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Detailed description...'}),
            'ticket_type': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }


class FeedbackAndSurveyForm(forms.ModelForm):
    """Form for creating feedback forms and surveys"""
    
    class Meta:
        model = FeedbackAndSurvey
        fields = [
            'title', 'description', 'feedback_type', 'questions',
            'target_audience', 'is_active', 'is_anonymous', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'feedback_type': forms.Select(attrs={'class': 'form-select'}),
            'questions': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'JSON format for questions'}),
            'target_audience': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmailForm(forms.ModelForm):
    """Form for composing emails"""
    recipient = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Email
        fields = [
            'email_name', 'subject', 'content_html', 'cc', 'bcc',
            'send_at', 'priority', 'tracking_enabled'
        ]
        widgets = {
            'email_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Internal name for this email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content_html': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'cc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}),
            'bcc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}),
            'send_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'tracking_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_cc(self):
        cc = self.cleaned_data.get('cc')
        if cc and isinstance(cc, str):
            return [email.strip() for email in cc.split(',')]
        return cc or []

    def clean_bcc(self):
        bcc = self.cleaned_data.get('bcc')
        if bcc and isinstance(bcc, str):
            return [email.strip() for email in bcc.split(',')]
        return bcc or []

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.recipients = [self.cleaned_data['recipient']]
        if commit:
            instance.save()
        return instance


class SMSForm(forms.ModelForm):
    """Form for sending SMS messages"""
    
    class Meta:
        model = SMS
        fields = ['recipient_phone', 'message', 'scheduled_send_time']
        widgets = {
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'maxlength': '160'}),
            'scheduled_send_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class CallLogForm(forms.ModelForm):
    """Form for logging phone calls"""
    
    class Meta:
        model = CallLog
        fields = [
            'call_type', 'direction', 'phone_number', 'contact_name',
            'duration_seconds', 'outcome', 'notes', 'follow_up_required'
        ]
        widgets = {
            'call_type': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_seconds': forms.NumberInput(attrs={'class': 'form-control'}),
            'outcome': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'follow_up_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmailSignatureForm(forms.ModelForm):
    """Form for managing email signatures"""
    class Meta:
        model = EmailSignature
        fields = ['name', 'content_html', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Signature Name'}),
            'content_html': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'HTML Content...'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WhatsAppTemplateForm(forms.ModelForm):
    """Form for creating and editing WhatsApp templates"""
    
    class Meta:
        model = WhatsAppTemplate
        fields = [
            'template_name', 'category', 'language', 'header_text', 
            'body_text', 'footer_text', 'buttons', 'variable_count', 
            'variable_examples', 'is_active'
        ]
        widgets = {
            'template_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. welcome_message'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. en'}),
            'header_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Header text (optional)'}),
            'body_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Template body with {{1}}, {{2}}...'}),
            'footer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Footer text (optional)'}),
            'buttons': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'JSON button configuration'}),
            'variable_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'variable_examples': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'JSON list of examples'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
