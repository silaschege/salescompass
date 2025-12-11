from django import forms
from .models import Report, ReportSchedule, ReportExport, ReportTemplate, ReportAnalytics, ReportSubscriber, ReportNotification, ReportType, ReportScheduleFrequency, ExportFormat, TemplateType, TemplateFormat, ReportAction, ReportFormat, SubscriptionType, NotificationChannel
from tenants.models import Tenant as TenantModel
from core.forms import DynamicChoiceWidget  # Import the DynamicChoiceWidget from core forms



class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_name', 'report_description', 'report_type_ref', 'query_config', 'report_is_active', 
                  'is_scheduled', 'schedule_frequency_ref', 'last_run', 'last_run_status']
        widgets = {
            'report_type_ref': DynamicChoiceWidget(choice_model=ReportType),
            'schedule_frequency_ref': DynamicChoiceWidget(choice_model=ReportScheduleFrequency),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['report_type_ref'].queryset = ReportType.objects.filter(tenant_id=self.tenant.id)
            self.fields['schedule_frequency_ref'].queryset = ReportScheduleFrequency.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['report_type_ref'].queryset = ReportType.objects.none()
            self.fields['schedule_frequency_ref'].queryset = ReportScheduleFrequency.objects.none()


class ReportScheduleForm(forms.ModelForm):
    class Meta:
        model = ReportSchedule
        fields = ['report', 'schedule_name', 'schedule_description', 'frequency_ref', 'recipients', 'schedule_is_active', 
                  'next_run', 'last_run']
        widgets = {
            'frequency_ref': DynamicChoiceWidget(choice_model=ReportScheduleFrequency),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['frequency_ref'].queryset = ReportScheduleFrequency.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['frequency_ref'].queryset = ReportScheduleFrequency.objects.none()


class ReportExportForm(forms.ModelForm):
    class Meta:
        model = ReportExport
        fields = ['report', 'export_format_ref', 'file', 'created_by', 'status', 'error_message', 
                  'completed_at']
        widgets = {
            'export_format_ref': DynamicChoiceWidget(choice_model=ExportFormat),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['export_format_ref'].queryset = ExportFormat.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['export_format_ref'].queryset = ExportFormat.objects.none()


class ReportTemplateForm(forms.ModelForm):
    class Meta:
        model = ReportTemplate
        fields = ['template_name', 'template_description', 'template_type_ref', 'template_format_ref', 'template_content', 
                  'template_is_active', 'created_by']
        widgets = {
            'template_type_ref': DynamicChoiceWidget(choice_model=TemplateType),
            'template_format_ref': DynamicChoiceWidget(choice_model=TemplateFormat),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['template_type_ref'].queryset = TemplateType.objects.filter(tenant_id=self.tenant.id)
            self.fields['template_format_ref'].queryset = TemplateFormat.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['template_type_ref'].queryset = TemplateType.objects.none()
            self.fields['template_format_ref'].queryset = TemplateFormat.objects.none()


class ReportAnalyticsForm(forms.ModelForm):
    class Meta:
        model = ReportAnalytics
        fields = ['report', 'user', 'action_ref', 'metadata']
        widgets = {
            'action_ref': DynamicChoiceWidget(choice_model=ReportAction),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['action_ref'].queryset = ReportAction.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['action_ref'].queryset = ReportAction.objects.none()


class ReportSubscriptionForm(forms.ModelForm):
    class Meta:
        model = ReportSubscriber
        fields = ['report', 'user', 'email', 'subscription_type_ref', 'report_format_ref', 'subscriber_is_active', 
                  'next_scheduled_send']
        widgets = {
            'subscription_type_ref': DynamicChoiceWidget(choice_model=SubscriptionType),
            'report_format_ref': DynamicChoiceWidget(choice_model=ReportFormat),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['subscription_type_ref'].queryset = SubscriptionType.objects.filter(tenant_id=self.tenant.id)
            self.fields['report_format_ref'].queryset = ReportFormat.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['subscription_type_ref'].queryset = SubscriptionType.objects.none()
            self.fields['report_format_ref'].queryset = ReportFormat.objects.none()


class ReportNotificationForm(forms.ModelForm):
    class Meta:
        model = ReportNotification
        fields = ['report_schedule', 'recipient_email', 'status', 'sent_at', 'error_message', 
                  'notification_channel_ref']
        widgets = {
            'notification_channel_ref': DynamicChoiceWidget(choice_model=NotificationChannel),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['notification_channel_ref'].queryset = NotificationChannel.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['notification_channel_ref'].queryset = NotificationChannel.objects.none()


class ReportTypeForm(forms.ModelForm):
    class Meta:
        model = ReportType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']


class ReportScheduleFrequencyForm(forms.ModelForm):
    class Meta:
        model = ReportScheduleFrequency
        fields = ['frequency_name', 'label', 'order', 'frequency_is_active', 'is_system']


class ExportFormatForm(forms.ModelForm):
    class Meta:
        model = ExportFormat
        fields = ['format_name', 'label', 'order', 'format_is_active', 'is_system']


class TemplateTypeForm(forms.ModelForm):
    class Meta:
        model = TemplateType
        fields = ['template_type_name', 'label', 'order', 'template_type_is_active', 'is_system']


class TemplateFormatForm(forms.ModelForm):
    class Meta:
        model = TemplateFormat
        fields = ['format_name', 'label', 'order', 'format_is_active', 'is_system']


class ReportActionForm(forms.ModelForm):
    class Meta:
        model = ReportAction
        fields = ['action_name', 'label', 'order', 'action_is_active', 'is_system']


class ReportFormatForm(forms.ModelForm):
    class Meta:
        model = ReportFormat
        fields = ['format_name', 'label', 'order', 'format_is_active', 'is_system']


class SubscriptionTypeForm(forms.ModelForm):
    class Meta:
        model = SubscriptionType
        fields = ['subscription_type_name', 'label', 'order', 'subscription_type_is_active', 'is_system']


class NotificationChannelForm(forms.ModelForm):
    class Meta:
        model = NotificationChannel
        fields = ['channel_name', 'label', 'order', 'channel_is_active', 'is_system']
