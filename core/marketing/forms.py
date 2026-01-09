from django import forms
from django.forms import inlineformset_factory
from .models import Campaign, EmailTemplate, LandingPageBlock, MessageTemplate, EmailCampaign, CampaignStatus, EmailProvider, BlockType, EmailCategory, MessageType, MessageCategory, EmailIntegration
from tenants.models import Tenant as TenantModel
from core.forms import DynamicChoiceWidget  # Import the DynamicChoiceWidget from core forms

from .models import (Campaign, EmailTemplate, LandingPageBlock, MessageTemplate, EmailCampaign, 
                     CampaignStatus, EmailProvider, BlockType, EmailCategory, MessageType, 
                     MessageCategory, EmailIntegration, ABTest, ABTestVariant, ABAutomatedTest)


class BootstrapFormMixin:
    """
    Mixin to add Bootstrap classes to form fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-select'
            else:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'


class CampaignForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['campaign_name', 'campaign_description', 'status_ref', 'start_date', 'end_date', 'budget', 
                  'actual_cost', 'target_audience_size', 'actual_reach', 'owner', 'campaign_is_active']
        widgets = {
            'status_ref': DynamicChoiceWidget(choice_model=CampaignStatus),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['status_ref'].queryset = CampaignStatus.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['status_ref'].queryset = CampaignStatus.objects.none()


class EmailTemplateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['template_name', 'subject', 'content', 'preview_text', 'category_ref', 'template_is_active', 'created_by']
        widgets = {
            'category_ref': DynamicChoiceWidget(choice_model=EmailCategory),
            'content': forms.Textarea(attrs={'rows': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['category_ref'].queryset = EmailCategory.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['category_ref'].queryset = EmailCategory.objects.none()


class LandingPageBlockForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LandingPageBlock
        fields = ['landing_page', 'block_type_ref', 'content', 'order', 'block_is_active']
        widgets = {
            'block_type_ref': DynamicChoiceWidget(choice_model=BlockType),
            'content': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['block_type_ref'].queryset = BlockType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['block_type_ref'].queryset = BlockType.objects.none()


class MessageTemplateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ['template_name', 'content', 'message_type_ref', 'category_ref', 'template_is_active', 'created_by']
        widgets = {
            'message_type_ref': DynamicChoiceWidget(choice_model=MessageType),
            'category_ref': DynamicChoiceWidget(choice_model=MessageCategory),
            'content': forms.Textarea(attrs={'rows': 5}),
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


class EmailCampaignForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EmailCampaign
        fields = ['campaign', 'campaign_name', 'subject', 'content', 'recipients', 'status', 
                  'scheduled_send_time', 'sent_at', 'email_provider_ref', 'tracking_enabled', 
                  'created_by']
        widgets = {
            'status': forms.Select(choices=[
                ('draft', 'Draft'), ('scheduled', 'Scheduled'), ('sending', 'Sending'),
                ('sent', 'Sent'), ('paused', 'Paused'), ('cancelled', 'Cancelled')
            ]),
            'email_provider_ref': DynamicChoiceWidget(choice_model=EmailProvider),
            'content': forms.Textarea(attrs={'rows': 10}),
            'scheduled_send_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recipients': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['email_provider_ref'].queryset = EmailProvider.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['email_provider_ref'].queryset = EmailProvider.objects.none()


class CampaignStatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CampaignStatus
        fields = ['status_name', 'label', 'order', 'status_is_active', 'is_system']


class EmailProviderForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EmailProvider
        fields = ['provider_name', 'label', 'order', 'provider_is_active', 'is_system']


class BlockTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BlockType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']


class EmailCategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EmailCategory
        fields = ['category_name', 'label', 'order', 'category_is_active', 'is_system']


class MessageTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MessageType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']


class MessageCategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MessageCategory
        fields = ['category_name', 'label', 'order', 'category_is_active', 'is_system']


class EmailIntegrationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EmailIntegration
        fields = ['user', 'provider', 'provider_ref', 'email_address', 'api_key', 'integration_is_active']
        widgets = {
            'provider_ref': DynamicChoiceWidget(choice_model=EmailProvider),
            'api_key': forms.PasswordInput(render_value=True),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['provider_ref'].queryset = EmailProvider.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['provider_ref'].queryset = EmailProvider.objects.none()


class ABTestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ABTest
        fields = ['name', 'description', 'campaign', 'is_active', 'auto_winner', 'confidence_level']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'campaign': DynamicChoiceWidget(choice_model=Campaign),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['campaign'].queryset = Campaign.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['campaign'].queryset = Campaign.objects.none()


class ABTestVariantForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ABTestVariant
        fields = ['variant', 'assignment_rate', 'email_template', 'landing_page', 
                  'question_text', 'follow_up_question', 'delivery_delay_hours']
        widgets = {
            'email_template': DynamicChoiceWidget(choice_model=EmailTemplate),
            'landing_page': DynamicChoiceWidget(choice_model=LandingPageBlock),
            'question_text': forms.Textarea(attrs={'rows': 3}),
            'follow_up_question': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['email_template'].queryset = EmailTemplate.objects.filter(tenant_id=self.tenant.id)
            self.fields['landing_page'].queryset = LandingPageBlock.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['email_template'].queryset = EmailTemplate.objects.none()
            self.fields['landing_page'].queryset = LandingPageBlock.objects.none()


class ABAutomatedTestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ABAutomatedTest
        fields = ['test_name', 'test_description', 'campaign', 'variant_a', 'variant_b',
                  'status', 'start_date', 'end_date', 'sample_size', 'winner', 'winning_metric']
        widgets = {
            'test_description': forms.Textarea(attrs={'rows': 4}),
            'campaign': DynamicChoiceWidget(choice_model=Campaign),
            'variant_a': DynamicChoiceWidget(choice_model=EmailTemplate),
            'variant_b': DynamicChoiceWidget(choice_model=EmailTemplate),
            'status': forms.Select(choices=[
                ('draft', 'Draft'), ('running', 'Running'), ('completed', 'Completed'),
                ('cancelled', 'Cancelled')
            ]),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['campaign'].queryset = Campaign.objects.filter(tenant_id=self.tenant.id)
            self.fields['variant_a'].queryset = EmailTemplate.objects.filter(tenant_id=self.tenant.id)
            self.fields['variant_b'].queryset = EmailTemplate.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['campaign'].queryset = Campaign.objects.none()
            self.fields['variant_a'].queryset = EmailTemplate.objects.none()
            self.fields['variant_b'].queryset = EmailTemplate.objects.none()


# FormSets
ABTestVariantCreateFormSet = inlineformset_factory(
    ABTest, ABTestVariant,
    form=ABTestVariantForm,
    extra=2,
    can_delete=False
)

ABTestVariantUpdateFormSet = inlineformset_factory(
    ABTest, ABTestVariant,
    form=ABTestVariantForm,
    extra=0,
    can_delete=False
)

