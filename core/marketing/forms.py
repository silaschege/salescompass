from django import forms
from .models import Campaign, EmailTemplate, LandingPageBlock, MessageTemplate, EmailCampaign, CampaignStatus, EmailProvider, BlockType, EmailCategory, MessageType, MessageCategory
from tenants.models import Tenant as TenantModel
from core.forms import DynamicChoiceWidget  # Import the DynamicChoiceWidget from core forms





class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['campaign_name', 'campaign_description', 'status_ref', 'start_date', 'end_date', 'budget', 
                  'actual_cost', 'target_audience_size', 'actual_reach', 'owner', 'campaign_is_active']
        widgets = {
            'status_ref': DynamicChoiceWidget(choice_model=CampaignStatus),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['status_ref'].queryset = CampaignStatus.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['status_ref'].queryset = CampaignStatus.objects.none()


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['template_name', 'subject', 'content', 'preview_text', 'category_ref', 'template_is_active', 'created_by']
        widgets = {
            'category_ref': DynamicChoiceWidget(choice_model=EmailCategory),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['category_ref'].queryset = EmailCategory.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['category_ref'].queryset = EmailCategory.objects.none()


class LandingPageBlockForm(forms.ModelForm):
    class Meta:
        model = LandingPageBlock
        fields = ['landing_page', 'block_type_ref', 'content', 'order', 'block_is_active']
        widgets = {
            'block_type_ref': DynamicChoiceWidget(choice_model=BlockType),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['block_type_ref'].queryset = BlockType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['block_type_ref'].queryset = BlockType.objects.none()


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ['template_name', 'content', 'message_type_ref', 'category_ref', 'template_is_active', 'created_by']
        widgets = {
            'message_type_ref': DynamicChoiceWidget(choice_model=MessageType),
            'category_ref': DynamicChoiceWidget(choice_model=MessageCategory),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['message_type_ref'].queryset = MessageType.objects.filter(tenant_id=self.tenant.id)
            self.fields['category_ref'].queryset = MessageCategory.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['message_type_ref'].queryset = MessageType.objects.none()
            self.fields['category_ref'].queryset = MessageCategory.objects.none()


class EmailCampaignForm(forms.ModelForm):
    class Meta:
        model = EmailCampaign
        fields = ['campaign', 'campaign_name', 'subject', 'content', 'recipients', 'status', 
                  'scheduled_send_time', 'sent_at', 'email_provider_ref', 'tracking_enabled', 
                  'open_count', 'click_count', 'bounce_count', 'complaint_count', 'created_by']
        widgets = {
            'status': forms.Select(choices=[
                ('draft', 'Draft'), ('scheduled', 'Scheduled'), ('sending', 'Sending'),
                ('sent', 'Sent'), ('paused', 'Paused'), ('cancelled', 'Cancelled')
            ]),
            'email_provider_ref': DynamicChoiceWidget(choice_model=EmailProvider),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['status_ref'].queryset = CampaignStatus.objects.filter(tenant_id=self.tenant.id)
            self.fields['email_provider_ref'].queryset = EmailProvider.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['status_ref'].queryset = CampaignStatus.objects.none()
            self.fields['email_provider_ref'].queryset = EmailProvider.objects.none()


class CampaignStatusForm(forms.ModelForm):
    class Meta:
        model = CampaignStatus
        fields = ['status_name', 'label', 'order', 'status_is_active', 'is_system']


class EmailProviderForm(forms.ModelForm):
    class Meta:
        model = EmailProvider
        fields = ['provider_name', 'label', 'order', 'provider_is_active', 'is_system']


class BlockTypeForm(forms.ModelForm):
    class Meta:
        model = BlockType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']


class EmailCategoryForm(forms.ModelForm):
    class Meta:
        model = EmailCategory
        fields = ['category_name', 'label', 'order', 'category_is_active', 'is_system']


class MessageTypeForm(forms.ModelForm):
    class Meta:
        model = MessageType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']


class MessageCategoryForm(forms.ModelForm):
    class Meta:
        model = MessageCategory
        fields = ['category_name', 'label', 'order', 'category_is_active', 'is_system']
