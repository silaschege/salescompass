from django import forms
from django.forms.widgets import Select
from .models import (
    SystemConfiguration, SystemEventLog, SystemHealthCheck, MaintenanceWindow, 
    PerformanceMetric, SystemNotification, SystemConfigType, SystemConfigCategory, 
    SystemEventType, SystemEventSeverity, HealthCheckType, HealthCheckStatus, 
    MaintenanceStatus, MaintenanceType, PerformanceMetricType, PerformanceEnvironment, 
    NotificationType, NotificationPriority, ModuleLabel, ModuleChoice, 
    ModelChoice, FieldType, AssignmentRuleType
)

from .models_audit import DynamicChoiceAuditMixin
from tenants.models import Tenant as TenantModel
 

class DynamicChoiceWidget(Select):
    """Custom widget for dynamic choices that loads choices from the database"""
    def __init__(self, choice_model, *args, **kwargs):
        self.choice_model = choice_model
        super().__init__(*args, **kwargs)
    
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # Add data attributes for JavaScript to load choices dynamically
        attrs['data-dynamic-choice-model'] = self.choice_model._meta.label_lower
        return attrs


class SystemConfigurationForm(forms.ModelForm):
    class Meta:
        model = SystemConfiguration
        fields = ['key', 'value', 'description', 'data_type', 'category', 'is_sensitive', 'updated_by']
        widgets = {
            'data_type': DynamicChoiceWidget(choice_model=SystemConfigType),
            'category': DynamicChoiceWidget(choice_model=SystemConfigCategory),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['data_type_ref'].queryset = SystemConfigType.objects.filter(tenant_id=self.tenant.id)
            self.fields['category_ref'].queryset = SystemConfigCategory.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['data_type_ref'].queryset = SystemConfigType.objects.none()
            self.fields['category_ref'].queryset = SystemConfigCategory.objects.none()


class SystemEventLogForm(forms.ModelForm):
    class Meta:
        model = SystemEventLog
        fields = ['event_type', 'severity', 'message', 'details', 'user', 'ip_address']
        widgets = {
            'event_type': DynamicChoiceWidget(choice_model=SystemEventType),
            'severity': DynamicChoiceWidget(choice_model=SystemEventSeverity),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['event_type_ref'].queryset = SystemEventType.objects.filter(tenant_id=self.tenant.id)
            self.fields['severity_ref'].queryset = SystemEventSeverity.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['event_type_ref'].queryset = SystemEventType.objects.none()
            self.fields['severity_ref'].queryset = SystemEventSeverity.objects.none()


class SystemHealthCheckForm(forms.ModelForm):
    class Meta:
        model = SystemHealthCheck
        fields = ['check_type', 'status', 'value', 'unit', 'threshold_critical', 'threshold_warning', 'details']
        widgets = {
            'check_type': DynamicChoiceWidget(choice_model=HealthCheckType),
            'status': DynamicChoiceWidget(choice_model=HealthCheckStatus),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['check_type_ref'].queryset = HealthCheckType.objects.filter(tenant_id=self.tenant.id)
            self.fields['status_ref'].queryset = HealthCheckStatus.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['check_type_ref'].queryset = HealthCheckType.objects.none()
            self.fields['status_ref'].queryset = HealthCheckStatus.objects.none()


class MaintenanceWindowForm(forms.ModelForm):
    class Meta:
        model = MaintenanceWindow
        fields = ['title', 'description', 'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end', 
                  'status', 'maintenance_type', 'affected_components', 'estimated_downtime_minutes']
        widgets = {
            'status': DynamicChoiceWidget(choice_model=MaintenanceStatus),
            'maintenance_type': DynamicChoiceWidget(choice_model=MaintenanceType),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['status_ref'].queryset = MaintenanceStatus.objects.filter(tenant_id=self.tenant.id)
            self.fields['maintenance_type_ref'].queryset = MaintenanceType.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['status_ref'].queryset = MaintenanceStatus.objects.none()
            self.fields['maintenance_type_ref'].queryset = MaintenanceType.objects.none()


class PerformanceMetricForm(forms.ModelForm):
    class Meta:
        model = PerformanceMetric
        fields = ['metric_type', 'value', 'unit', 'component', 'environment', 'tenant']
        widgets = {
            'metric_type': DynamicChoiceWidget(choice_model=PerformanceMetricType),
            'environment': DynamicChoiceWidget(choice_model=PerformanceEnvironment),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['metric_type_ref'].queryset = PerformanceMetricType.objects.filter(tenant_id=self.tenant.id)
            self.fields['environment_ref'].queryset = PerformanceEnvironment.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['metric_type_ref'].queryset = PerformanceMetricType.objects.none()
            self.fields['environment_ref'].queryset = PerformanceEnvironment.objects.none()


class SystemNotificationForm(forms.ModelForm):
    class Meta:
        model = SystemNotification
        fields = ['title', 'message', 'notification_type', 'priority', 'start_datetime', 'end_datetime', 
                  'is_active', 'is_dismissible']
        widgets = {
            'notification_type': DynamicChoiceWidget(choice_model=NotificationType),
            'priority': DynamicChoiceWidget(choice_model=NotificationPriority),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['notification_type_ref'].queryset = NotificationType.objects.filter(tenant_id=self.tenant.id)
            self.fields['priority_ref'].queryset = NotificationPriority.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['notification_type_ref'].queryset = NotificationType.objects.none()
            self.fields['priority_ref'].queryset = NotificationPriority.objects.none()


class SystemConfigTypeForm(forms.ModelForm):
    class Meta:
        model = SystemConfigType
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class SystemConfigCategoryForm(forms.ModelForm):
    class Meta:
        model = SystemConfigCategory
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class SystemEventTypeForm(forms.ModelForm):
    class Meta:
        model = SystemEventType
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class SystemEventSeverityForm(forms.ModelForm):
    class Meta:
        model = SystemEventSeverity
        fields = ['name', 'display_name', 'description', 'color', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class HealthCheckTypeForm(forms.ModelForm):
    class Meta:
        model = HealthCheckType
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class HealthCheckStatusForm(forms.ModelForm):
    class Meta:
        model = HealthCheckStatus
        fields = ['name', 'display_name', 'description', 'color', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class MaintenanceStatusForm(forms.ModelForm):
    class Meta:
        model = MaintenanceStatus
        fields = ['name', 'display_name', 'description', 'color', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class MaintenanceTypeForm(forms.ModelForm):
    class Meta:
        model = MaintenanceType
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class PerformanceMetricTypeForm(forms.ModelForm):
    class Meta:
        model = PerformanceMetricType
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class PerformanceEnvironmentForm(forms.ModelForm):
    class Meta:
        model = PerformanceEnvironment
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class NotificationTypeForm(forms.ModelForm):
    class Meta:
        model = NotificationType
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


class NotificationPriorityForm(forms.ModelForm):
    class Meta:
        model = NotificationPriority
        fields = ['name', 'display_name', 'description', 'color', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance._current_user = self.user
        if commit:
            instance.save()
        return instance


# Business Metrics Forms
class CLVMetricForm(forms.Form):
    """
    Form for CLV metric calculations
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Start date for CLV calculation"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="End date for CLV calculation"
    )
    customer_segment = forms.ChoiceField(
        choices=[
            ('all', 'All Customers'),
            ('premium', 'Premium'),
            ('standard', 'Standard'),
            ('basic', 'Basic'),
        ],
        initial='all',
        help_text="Customer segment to calculate CLV for"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class CACMetricForm(forms.Form):
    """
    Form for CAC metric calculations
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Start date for CAC calculation"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="End date for CAC calculation"
    )
    marketing_channel = forms.ChoiceField(
        choices=[
            ('all', 'All Channels'),
            ('email', 'Email Marketing'),
            ('social', 'Social Media'),
            ('paid_ads', 'Paid Ads'),
            ('content', 'Content Marketing'),
            ('seo', 'SEO'),
            ('referral', 'Referral'),
            ('event', 'Events'),
            ('direct', 'Direct Traffic'),
        ],
        initial='all',
        help_text="Marketing channel to calculate CAC for"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class SalesVelocityMetricForm(forms.Form):
    """
    Form for sales velocity metric calculations
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Start date for sales velocity calculation"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="End date for sales velocity calculation"
    )
    opportunity_stage = forms.ChoiceField(
        choices=[
            ('all', 'All Stages'),
            ('prospecting', 'Prospecting'),
            ('qualification', 'Qualification'),
            ('needs_analysis', 'Needs Analysis'),
            ('proposal', 'Proposal'),
            ('negotiation', 'Negotiation'),
            ('closed_won', 'Closed Won'),
            ('closed_lost', 'Closed Lost'),
        ],
        initial='all',
        help_text="Opportunity stage to calculate velocity for"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class ROIMetricForm(forms.Form):
    """
    Form for ROI metric calculations
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Start date for ROI calculation"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="End date for ROI calculation"
    )
    metric_type = forms.ChoiceField(
        choices=[
            ('overall', 'Overall ROI'),
            ('channel_specific', 'Channel-Specific ROI'),
            ('product_specific', 'Product-Specific ROI'),
            ('campaign_specific', 'Campaign-Specific ROI'),
        ],
        initial='overall',
        help_text="Type of ROI to calculate"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class ConversionFunnelMetricForm(forms.Form):
    """
    Form for conversion funnel metric calculations
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Start date for conversion funnel calculation"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="End date for conversion funnel calculation"
    )
    funnel_stage = forms.ChoiceField(
        choices=[
            ('all', 'All Stages'),
            ('lead', 'Lead Generation'),
            ('marketing_qualified', 'Marketing Qualified'),
            ('sales_qualified', 'Sales Qualified'),
            ('opportunity', 'Opportunity Created'),
            ('demo', 'Demo Given'),
            ('proposal', 'Proposal Sent'),
            ('won', 'Deal Won'),
        ],
        initial='all',
        help_text="Funnel stage to calculate conversion rates for"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class BusinessMetricsExportForm(forms.Form):
    """
    Form for exporting business metrics
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Start date for metrics export"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="End date for metrics export"
    )
    metric_types = forms.MultipleChoiceField(
        choices=[
            ('clv', 'Customer Lifetime Value'),
            ('cac', 'Customer Acquisition Cost'),
            ('sales_velocity', 'Sales Velocity'),
            ('roi', 'Return on Investment'),
            ('conversion_funnel', 'Conversion Funnel'),
        ],
        initial=['clv', 'cac', 'sales_velocity'],
        widget=forms.CheckboxSelectMultiple,
        help_text="Select metrics to include in export"
    )
    export_format = forms.ChoiceField(
        choices=[
            ('csv', 'CSV'),
            ('excel', 'Excel'),
            ('pdf', 'PDF'),
            ('json', 'JSON'),
        ],
        initial='csv',
        help_text="Format to export metrics in"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data

class ModuleLabelForm(forms.ModelForm):
    class Meta:
        model = ModuleLabel
        fields = ['module_key', 'module_key_ref', 'custom_label', 'module_label_is_active']
        widgets = {
            'module_key_ref': DynamicChoiceWidget(choice_model=ModuleChoice),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            if 'module_key_ref' in self.fields:
                self.fields['module_key_ref'].queryset = ModuleChoice.objects.filter(tenant_id=self.tenant.id)
        else:
            if 'module_key_ref' in self.fields:
                self.fields['module_key_ref'].queryset = ModuleChoice.objects.none()


class ModuleChoiceForm(forms.ModelForm):
    class Meta:
        model = ModuleChoice
        fields = ['module_choice_name', 'label', 'order', 'module_choice_is_active', 'is_system']


class ModelChoiceForm(forms.ModelForm):
    class Meta:
        model = ModelChoice
        fields = ['model_choice_name', 'label', 'order', 'model_choice_is_active', 'is_system']


class FieldTypeForm(forms.ModelForm):
    class Meta:
        model = FieldType
        fields = ['field_type_name', 'label', 'order', 'field_type_is_active', 'is_system']


class AssignmentRuleTypeForm(forms.ModelForm):
    class Meta:
        model = AssignmentRuleType
        fields = ['rule_type_name', 'label', 'order', 'rule_type_is_active', 'is_system']
