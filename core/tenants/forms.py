from django import forms
from django.forms.widgets import Select
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from core.models import User
from .models import (
    Tenant, TenantSettings, TenantFeatureEntitlement, Setting, SettingGroup, 
    SettingType, TenantCloneHistory, WhiteLabelSettings, TenantUsageMetric, 
    OverageAlert, NotificationTemplate, Notification, AlertThreshold, TenantDataIsolationAudit, 
    TenantDataIsolationViolation, DataResidencySettings, TenantRole, 
    TenantTerritory, TenantMember, TenantLifecycleEvent, TenantMigrationRecord,
    TenantDataPreservation, TenantDataRestoration, TenantDataPreservationStrategy,
    TenantDataPreservationSchedule, AutomatedTenantLifecycleRule,
    AutomatedTenantLifecycleEvent, TenantLifecycleWorkflow,
    TenantLifecycleWorkflowExecution, TenantSuspensionWorkflow,
    TenantTerminationWorkflow
)



class TenantSignupForm(UserCreationForm):
    company_name = forms.CharField(max_length=255, label="Company Name")
    email = forms.EmailField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'company_name')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class OnboardingUserSignupForm(UserCreationForm):
    """
    Form for Step 1 of Onboarding Wizard - User Creation only.
    Does NOT require company/tenant info yet.
    """
    email = forms.EmailField(required=True, label="Email Access")
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"] # Use email as username
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class SuperuserProvisionForm(forms.Form):
    """
    Form for Superusers to provision a new Tenant and Admin User.
    """
    # User Details
    email = forms.EmailField(required=True, label="Admin Email")
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Initial Password")
    
    # Tenant Details
    company_name = forms.CharField(required=True, max_length=255)
    subdomain = forms.SlugField(required=True, max_length=255, help_text="Unique subdomain for the tenant")
    plan = forms.ModelChoiceField(
        queryset=None, # Populated in __init__
        required=True,
        empty_label="Select a Plan"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from billing.models import Plan
        self.fields['plan'].queryset = Plan.objects.filter(is_active=True)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email
        
    def clean_subdomain(self):
        subdomain = self.cleaned_data.get('subdomain')
        if Tenant.objects.filter(subdomain=subdomain).exists():
            raise ValidationError("This subdomain is already in use.")
        return subdomain
 
class TenantBrandingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantSettings
        fields = ['logo', 'primary_color', 'secondary_color', 'time_zone', 'date_format', 'default_currency']
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
        }

class TenantDomainForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Tenant
        fields = ['domain', 'subdomain']
        help_texts = {
            'domain': 'Custom domain for your tenant (e.g., mycompany.com)',
            'subdomain': 'Subdomain for your tenant (e.g., mycompany)',
        }

class TenantSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Tenant
        fields = ['name', 'description', 'primary_color', 'secondary_color', 'user_limit', 'storage_limit_mb', 'api_call_limit']

class FeatureToggleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    feature_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter feature name (e.g., Advanced Analytics)'
        })
    )
    enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter description or notes about this feature toggle'
        }),
        required=False
    )

class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['group', 'setting_name', 'setting_label', 'setting_description', 'setting_type', 'value_text', 'value_number', 'value_boolean', 'is_required', 'is_visible', 'order']
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['group'].queryset = SettingGroup.objects.filter(tenant=tenant)

class SettingGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = SettingGroup
        fields = ['setting_group_name', 'setting_group_description', 'setting_group_is_active']

class SettingTypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = SettingType
        fields = ['setting_type_name', 'label', 'order', 'setting_type_is_active', 'is_system']

# New form for onboarding process
class OnboardingTenantInfoForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    company_name = forms.CharField(
        max_length=255,
        label="Company Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company name'
        })
    )
    company_description = forms.CharField(
        max_length=500,
        required=False,
        label="Company Description",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of your business',
            'rows': 3
        })
    )
    industry = forms.ChoiceField(
        choices=[
            ('', 'Select your industry'),
            ('technology', 'Technology'),
            ('healthcare', 'Healthcare'),
            ('finance', 'Finance'),
            ('retail', 'Retail'),
            ('manufacturing', 'Manufacturing'),
            ('consulting', 'Consulting'),
            ('education', 'Education'),
            ('other', 'Other')
        ],
        label="Industry",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    company_size = forms.ChoiceField(
        choices=[
            ('', 'Select company size'),
            ('1-10', '1-10 employees'),
            ('11-50', '11-50 employees'),
            ('51-200', '51-200 employees'),
            ('201-500', '201-500 employees'),
            ('501-1000', '501-1000 employees'),
            ('1000+', '1000+ employees')
        ],
        label="Company Size",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    primary_email = forms.EmailField(
        label="Primary Contact Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@company.com'
        })
    )



class OnboardingBrandingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    logo = forms.ImageField(
        required=False,
        label="Upload Logo",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    primary_color = forms.CharField(
        max_length=7,
        label="Primary Brand Color",
        initial="#6f42c1",
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-control form-control-color'
        })
    )
    secondary_color = forms.CharField(
        max_length=7,
        label="Secondary Brand Color",
        initial="#007bff",
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-control form-control-color'
        })
    )
    timezone = forms.ChoiceField(
        choices=[
            ('UTC', 'UTC'),
            ('US/Eastern', 'US/Eastern'),
            ('US/Central', 'US/Central'),
            ('US/Mountain', 'US/Mountain'),
            ('US/Pacific', 'US/Pacific'),
            ('Europe/London', 'Europe/London'),
            ('Europe/Paris', 'Europe/Paris'),
            ('Asia/Tokyo', 'Asia/Tokyo'),
            ('Asia/Shanghai', 'Asia/Shanghai'),
            ('Asia/Kolkata', 'Asia/Kolkata'),
        ],
        label="Timezone",
        initial="UTC",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_format = forms.ChoiceField(
        choices=[
            ('%Y-%m-%d', 'YYYY-MM-DD (ISO)'),
            ('%m/%d/%Y', 'MM/DD/YYYY (US)'),
            ('%d/%m/%Y', 'DD/MM/YYYY (EU)'),
            ('%m-%d-%Y', 'MM-DD-YYYY (US)'),
            ('%d-%m-%Y', 'DD-MM-YYYY (EU)'),
        ],
        label="Date Format",
        initial="%Y-%m-%d",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    currency = forms.ChoiceField(
        choices=[
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound'),
            ('JPY', 'Japanese Yen'),
            ('CAD', 'Canadian Dollar'),
            ('AUD', 'Australian Dollar'),
            ('CHF', 'Swiss Franc'),
            ('CNY', 'Chinese Yuan'),
            ('INR', 'Indian Rupee'),
            ('KES', 'Kenyan Shilling'),
        ],
        label="Default Currency",
        initial="USD",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TenantExportForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    """Form for selecting data to export"""
    EXPORT_CHOICES = [
        ('leads', 'Leads'),
        ('opportunities', 'Opportunities'),
        ('accounts', 'Accounts'),
        ('contacts', 'Contacts'),
        ('tasks', 'Tasks'),
        ('cases', 'Cases'),
        ('products', 'Products'),
        ('proposals', 'Proposals'),
        ('settings', 'Settings'),
        ('users', 'Users'),
    ]
    
    data_types = forms.MultipleChoiceField(
        choices=EXPORT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Select data types to export",
        required=True
    )
    
    format_type = forms.ChoiceField(
        choices=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
            ('excel', 'Excel'),
        ],
        label="Export format",
        initial="json"
    )
    
    include_attachments = forms.BooleanField(
        required=False,
        label="Include file attachments",
        help_text="Include uploaded files and attachments in the export"
    )




class TenantImportForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    """Form for importing tenant data"""
    import_file = forms.FileField(
        label="Import File",
        help_text="Upload a previously exported data file (JSON, CSV, or Excel)"
    )
    
    import_type = forms.ChoiceField(
        choices=[
            ('leads', 'Leads'),
            ('opportunities', 'Opportunities'),
            ('accounts', 'Accounts'),
            ('contacts', 'Contacts'),
            ('tasks', 'Tasks'),
            ('cases', 'Cases'),
            ('products', 'Products'),
            ('proposals', 'Proposals'),
            ('settings', 'Settings'),
            ('users', 'Users'),
            ('all', 'All Data'),
        ],
        label="Import type",
        initial="all"
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        label="Overwrite existing data",
        help_text="Replace existing records with imported data"
    )
    
    validate_data = forms.BooleanField(
        required=False,
        label="Validate data before import",
        help_text="Check data integrity before importing"
    )


class TenantCloneForm(forms.Form):
    """Form for cloning a tenant"""
    CLONE_TYPE_CHOICES = [
        ('full_copy', 'Full Copy'),
        ('template_based', 'Template Based'),
        ('minimal_setup', 'Minimal Setup'),
        ('data_migration', 'Data Migration'),
    ]
    
    clone_type = forms.ChoiceField(
        choices=CLONE_TYPE_CHOICES,
        label="Clone Type",
        initial="template_based",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    source_tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
        label="Source Tenant",
        empty_label="Select a source tenant",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    new_tenant_name = forms.CharField(
        max_length=255,
        label="New Tenant Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the name for the new tenant'
        })
    )
    
    new_tenant_slug = forms.SlugField(
        max_length=255,
        label="New Tenant Slug",
        help_text="URL-friendly identifier for the new tenant",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., new-company-name'
        })
    )
    
    include_users = forms.BooleanField(
        required=False,
        label="Include Users",
        initial=True,
        help_text="Copy user accounts from the source tenant"
    )
    
    include_settings = forms.BooleanField(
        required=False,
        label="Include Settings",
        initial=True,
        help_text="Copy tenant settings and configurations"
    )
    
    include_data = forms.BooleanField(
        required=False,
        label="Include Data",
        initial=True,
        help_text="Copy all business data (leads, opportunities, etc.)"
    )
    
    include_custom_fields = forms.BooleanField(
        required=False,
        label="Include Custom Fields",
        initial=True,
        help_text="Copy custom field definitions"
    )
    
    clone_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe the purpose of this clone'
        }),
        required=False,
        label="Description",
        help_text="Optional description of this clone operation"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter tenants based on user's access (for superusers, show all; for regular users, show only their tenant)
        if user and not user.is_superuser:
            self.fields['source_tenant'].queryset = Tenant.objects.filter(id=user.tenant_id)




class WhiteLabelSettingsForm(forms.ModelForm):
    """Form for managing white-label branding settings"""
    class Meta:
        model = WhiteLabelSettings
        fields = [
            'logo', 'logo_small', 'favicon', 'brand_image',
            'primary_color', 'secondary_color', 'accent_color', 'background_color',
            'brand_name', 'tagline', 'copyright_text',
            'custom_domain', 'subdomain',
            'show_brand_name', 'show_logo', 'show_tagline',
            'privacy_policy_url', 'terms_of_service_url', 'support_url',
            'login_background_color', 'login_text_color',
            'is_active'
        ]
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'login_background_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'login_text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
            'custom_domain': forms.TextInput(attrs={'class': 'form-control'}),
            'subdomain': forms.TextInput(attrs={'class': 'form-control'}),
            'privacy_policy_url': forms.URLInput(attrs={'class': 'form-control'}),
            'terms_of_service_url': forms.URLInput(attrs={'class': 'form-control'}),
            'support_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # If we have a tenant, we can customize the form based on it
        if tenant:
            # Pre-populate brand name if not already set
            if not self.instance.pk and not self.instance.brand_name:
                self.fields['brand_name'].initial = tenant.name


class TenantUsageMetricForm(forms.ModelForm):
    """Form for managing tenant usage metrics"""
    class Meta:
        model = TenantUsageMetric
        fields = ['metric_type', 'value', 'unit', 'period_start', 'period_end']
        widgets = {
            'metric_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'period_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'period_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            # Limit to current tenant
            self.instance.tenant = tenant





class TenantUsageReportForm(forms.Form):
    """Form for generating usage reports"""
    METRIC_CHOICES = [
        ('users_active', 'Active Users'),
        ('users_total', 'Total Users'),
        ('storage_used_mb', 'Storage Used (MB)'),
        ('api_calls', 'API Calls'),
        ('records_created', 'Records Created'),
        ('records_updated', 'Records Updated'),
        ('records_deleted', 'Records Deleted'),
        ('logins', 'Login Count'),
        ('sessions', 'Active Sessions'),
        ('emails_sent', 'Emails Sent'),
        ('files_uploaded', 'Files Uploaded'),
        ('data_exported', 'Data Exported'),
        ('reports_generated', 'Reports Generated'),
        ('integrations_active', 'Active Integrations'),
    ]
    
    metric_type = forms.ChoiceField(
        choices=METRIC_CHOICES,
        label="Metric Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    start_date = forms.DateTimeField(
        label="Start Date",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    end_date = forms.DateTimeField(
        label="End Date",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    include_trend = forms.BooleanField(
        required=False,
        label="Include Trend Analysis",
        initial=True
    )
    
    include_comparison = forms.BooleanField(
        required=False,
        label="Include Period Comparison",
        initial=False
    )


class TenantFeatureEntitlementForm(forms.ModelForm):
    """Form for managing tenant feature entitlements"""
    class Meta:
        model = TenantFeatureEntitlement
        fields = ['feature_key', 'feature_name', 'is_enabled', 'entitlement_type', 'trial_start_date', 'trial_end_date', 'notes']
        widgets = {
            'feature_key': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., advanced_reporting'}),
            'feature_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Advanced Reporting'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'entitlement_type': forms.Select(attrs={'class': 'form-select'}),
            'trial_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'trial_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FeatureAccessForm(forms.Form):
    """Form for checking feature access"""
    feature_key = forms.CharField(
        max_length=255,
        label="Feature Key",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter feature key to check access'})
    )



class BulkFeatureEntitlementForm(forms.Form):
    """Form for bulk feature entitlement management"""
    features_json = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': '''[
    {"feature_key": "advanced_analytics", "feature_name": "Advanced Analytics", "is_enabled": true, "entitlement_type": "premium"},
    {"feature_key": "ai_predictions", "feature_name": "AI Predictions", "is_enabled": false, "entitlement_type": "trial"}
]'''
        }),
        help_text="JSON array of feature entitlements"
    )
    
    def clean_features_json(self):
        import json
        data = self.cleaned_data['features_json']
        try:
            features = json.loads(data)
            if not isinstance(features, list):
                raise forms.ValidationError("JSON must be an array of feature objects")
            for feature in features:
                if not isinstance(feature, dict):
                    raise forms.ValidationError("Each feature must be an object")
                if 'feature_key' not in feature:
                    raise forms.ValidationError("Each feature must have a 'feature_key'")
            return features
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format")


class OverageAlertForm(forms.ModelForm):
    """Form for managing overage alerts"""
    class Meta:
        model = OverageAlert
        fields = ['metric_type', 'threshold_value', 'current_value', 'threshold_percentage', 'alert_level', 'is_resolved']
        widgets = {
            'metric_type': forms.Select(attrs={'class': 'form-select'}),
            'threshold_value': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'threshold_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'alert_level': forms.Select(attrs={'class': 'form-select'}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationForm(forms.ModelForm):
    """Form for managing notifications"""
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type', 'severity', 'delivery_method']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'delivery_method': forms.Select(attrs={'class': 'form-select'}),
        }



class AlertThresholdForm(forms.ModelForm):
    """Form for managing alert thresholds"""
    class Meta:
        model = AlertThreshold
        fields = ['metric_type', 'threshold_percentage', 'alert_level', 'is_active']
        widgets = {
            'metric_type': forms.Select(attrs={'class': 'form-select'}),
            'threshold_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'min': '0', 'max': '100'}),
            'alert_level': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TenantDataIsolationAuditForm(forms.ModelForm):
    """Form for creating tenant data isolation audits"""
    class Meta:
        model = TenantDataIsolationAudit
        fields = ['audit_type', 'notes']
        widgets = {
            'audit_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class TenantDataIsolationViolationForm(forms.ModelForm):
    """Form for managing data isolation violations"""
    class Meta:
        model = TenantDataIsolationViolation
        fields = ['violation_type', 'severity', 'description', 'resolution_status']
        widgets = {
            'violation_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resolution_status': forms.Select(attrs={'class': 'form-select'}),
        }


class DataIsolationAuditFilterForm(forms.Form):
    """Form for filtering data isolation audits"""
    AUDIT_TYPE_CHOICES = [
        ('', 'All Types'),
        ('automated', 'Automated'),
        ('manual', 'Manual'),
        ('compliance', 'Compliance'),
        ('security', 'Security'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
        ('in_progress', 'In Progress'),
    ]
    
    audit_type = forms.ChoiceField(
        choices=AUDIT_TYPE_CHOICES,
        required=False,
        label="Audit Type",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Status",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateTimeField(
        required=False,
        label="Date From",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    date_to = forms.DateTimeField(
        required=False,
        label="Date To",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
        


class DataResidencySettingsForm(forms.ModelForm):
    class Meta:
        model = DataResidencySettings
        fields = [
            'primary_region', 'allowed_regions', 'encryption_enabled', 
            'encryption_key_location', 'encryption_key_region', 
            'data_retention_period_months', 'gdpr_compliant', 
            'hipaa_compliant', 'backup_regions', 'allow_cross_region_transfer',
            'export_format', 'legal_requirements', 'is_active'
        ]
        widgets = {
            'primary_region': forms.Select(attrs={'class': 'form-control'}),
            'allowed_regions': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
            'encryption_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'encryption_key_location': forms.Select(attrs={'class': 'form-control'}),
            'encryption_key_region': forms.Select(attrs={'class': 'form-control'}),
            'data_retention_period_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'gdpr_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hipaa_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'backup_regions': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
            'allow_cross_region_transfer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'export_format': forms.Select(attrs={'class': 'form-control'}),
            'legal_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text to fields
        self.fields['allowed_regions'].help_text = "Hold Ctrl/Cmd to select multiple regions"
        self.fields['backup_regions'].help_text = "Hold Ctrl/Cmd to select multiple regions for backups"
        
        # Customize choices for regions
        region_choices = DataResidencySettings.DATA_REGIONS
        self.fields['primary_region'].choices = region_choices
        self.fields['encryption_key_region'].choices = region_choices
         
        # Make sure allowed_regions field is a MultipleChoiceField
        self.fields['allowed_regions'] = forms.MultipleChoiceField(
            choices=region_choices,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            help_text="Select regions where data is allowed to be stored/processed"
        )
        
        self.fields['backup_regions'] = forms.MultipleChoiceField(
            choices=region_choices,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            help_text="Select regions for backups"
        )


class TenantMemberForm(forms.ModelForm):
    """
    Form for managing tenant members with tenant-aware filtering.
    """
    class Meta:
        model = TenantMember
        fields = [
            'user', 'role', 'territory', 'manager', 'status', 
            'hire_date', 'termination_date', 'quota_amount', 
            'quota_period', 'commission_rate', 'phone'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'termination_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'quota_period': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'territory': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'quota_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            # Filter choices by tenant
            self.fields['role'].queryset = TenantRole.objects.filter(tenant=tenant)
            self.fields['territory'].queryset = TenantTerritory.objects.filter(tenant=tenant)
            self.fields['manager'].queryset = TenantMember.objects.filter(tenant=tenant)
            
            # If creating, filter by users in tenant who don't have a member record yet
            if not self.instance.pk:
                existing_member_users = TenantMember.objects.filter(tenant=tenant).values_list('user_id', flat=True)
                self.fields['user'].queryset = User.objects.filter(tenant=tenant).exclude(id__in=existing_member_users)
            else:
                self.fields['user'].queryset = User.objects.filter(id=self.instance.user_id)
                self.fields['user'].disabled = True


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


class SettingTypeForm(forms.ModelForm):
    class Meta:
        model = SettingType
        fields = ['setting_type_name', 'label', 'order', 'setting_type_is_active', 'is_system']


class TenantLifecycleEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantLifecycleEvent
        fields = ['tenant', 'event_type', 'old_value', 'new_value', 'reason', 'triggered_by', 'ip_address']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'old_value': forms.TextInput(attrs={'class': 'form-control'}),
            'new_value': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'triggered_by': forms.Select(attrs={'class': 'form-select'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TenantMigrationRecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantMigrationRecord
        fields = ['source_tenant', 'destination_tenant', 'migration_type', 'status', 'completed_at', 'initiated_by', 'completed_by', 'progress_percentage', 'total_records', 'processed_records', 'failed_records', 'error_log', 'migration_notes']
        widgets = {
            'source_tenant': forms.Select(attrs={'class': 'form-select'}),
            'destination_tenant': forms.Select(attrs={'class': 'form-select'}),
            'migration_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'initiated_by': forms.Select(attrs={'class': 'form-select'}),
            'completed_by': forms.Select(attrs={'class': 'form-select'}),
            'progress_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_records': forms.NumberInput(attrs={'class': 'form-control'}),
            'processed_records': forms.NumberInput(attrs={'class': 'form-control'}),
            'failed_records': forms.NumberInput(attrs={'class': 'form-control'}),
            'error_log': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'migration_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TenantDataPreservationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantDataPreservation
        fields = ['tenant', 'preservation_type', 'status', 'description', 'backup_location', 'file_size_mb', 'preservation_date', 'expires_at', 'created_by', 'retention_period_days', 'modules_included', 'notes']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'preservation_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'backup_location': forms.TextInput(attrs={'class': 'form-control'}),
            'file_size_mb': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preservation_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
            'retention_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'modules_included': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



class TenantDataRestorationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantDataRestoration
        fields = ['tenant', 'preservation_record', 'status', 'completed_at', 'completed_by', 'notes']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'preservation_record': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'completed_by': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



class TenantDataPreservationStrategyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantDataPreservationStrategy
        fields = ['name', 'description', 'is_active', 'preservation_frequency', 'retention_period_days', 'modules_to_preserve', 'storage_location', 'compression_enabled', 'encryption_enabled', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preservation_frequency': forms.Select(attrs={'class': 'form-select'}),
            'retention_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'modules_to_preserve': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control'}),
            'compression_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'encryption_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
        }


class TenantDataPreservationScheduleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantDataPreservationSchedule
        fields = ['strategy', 'tenant', 'next_scheduled_run', 'last_run', 'is_active']
        widgets = {
            'strategy': forms.Select(attrs={'class': 'form-select'}),
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'next_scheduled_run': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'last_run': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AutomatedTenantLifecycleRuleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = AutomatedTenantLifecycleRule
        fields = ['name', 'description', 'is_active', 'condition_type', 'condition_field', 'condition_operator', 'condition_value', 'action_type', 'action_parameters', 'evaluation_frequency', 'last_evaluated', 'next_evaluation', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'condition_type': forms.Select(attrs={'class': 'form-select'}),
            'condition_field': forms.TextInput(attrs={'class': 'form-control'}),
            'condition_operator': forms.Select(attrs={'class': 'form-select'}),
            'condition_value': forms.TextInput(attrs={'class': 'form-control'}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'action_parameters': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'evaluation_frequency': forms.Select(attrs={'class': 'form-select'}),
            'last_evaluated': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'next_evaluation': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
        }


class AutomatedTenantLifecycleEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = AutomatedTenantLifecycleEvent
        fields = ['rule', 'tenant', 'event_type', 'status', 'details', 'triggered_at', 'executed_by']
        widgets = {
            'rule': forms.Select(attrs={'class': 'form-select'}),
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'triggered_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'executed_by': forms.Select(attrs={'class': 'form-select'}),
        }


class TenantLifecycleWorkflowForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantLifecycleWorkflow
        fields = ['name', 'description', 'workflow_type', 'is_active', 'steps', 'created_by']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'workflow_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'steps': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
        }


class TenantLifecycleWorkflowExecutionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantLifecycleWorkflowExecution
        fields = ['workflow', 'tenant', 'status', 'completed_at', 'executed_by', 'current_step', 'total_steps', 'progress_percentage', 'execution_log', 'error_message']
        widgets = {
            'workflow': forms.Select(attrs={'class': 'form-select'}),
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'executed_by': forms.Select(attrs={'class': 'form-select'}),
            'current_step': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_steps': forms.NumberInput(attrs={'class': 'form-control'}),
            'progress_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'execution_log': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'error_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TenantSuspensionWorkflowForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantSuspensionWorkflow
        fields = ['tenant', 'status', 'initiated_by', 'approved_by', 'suspension_reason', 'approval_notes', 'completed_at', 'approved_at', 'steps_completed', 'total_steps']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'initiated_by': forms.Select(attrs={'class': 'form-select'}),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
            'suspension_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'approval_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'approved_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'steps_completed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'total_steps': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TenantTerminationWorkflowForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = TenantTerminationWorkflow
        fields = ['tenant', 'status', 'initiated_by', 'approved_by', 'termination_reason', 'approval_notes', 'completed_at', 'approved_at', 'steps_completed', 'total_steps', 'data_preservation_required', 'data_preservation_record']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'initiated_by': forms.Select(attrs={'class': 'form-select'}),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
            'termination_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'approval_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'approved_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'steps_completed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'total_steps': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_preservation_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_preservation_record': forms.Select(attrs={'class': 'form-select'}),
        }


class NotificationTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    """Form for managing notification templates"""
    class Meta:
        model = NotificationTemplate
        fields = ['name', 'subject', 'message_body', 'notification_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }




class TenantTerritoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    """Form for managing tenant territories"""
    class Meta:
        model = TenantTerritory
        fields = ['name', 'description', 'region_code', 'country_codes', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'region_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country_codes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '["US", "CA", "MX"]'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_country_codes(self):
        """Validate that country_codes is a valid JSON array of country codes"""
        import json
        country_codes_input = self.cleaned_data.get('country_codes')
        if country_codes_input:
            try:
                # Try parsing as JSON
                countries = json.loads(country_codes_input)
                if not isinstance(countries, list):
                    raise forms.ValidationError("Country codes must be a JSON array")
                # Validate each country code is a valid ISO code (2-3 letters)
                for country in countries:
                    if not isinstance(country, str) or len(country) < 2 or len(country) > 3:
                        raise forms.ValidationError(f"'{country}' is not a valid country code")
                return countries
            except json.JSONDecodeError:
                raise forms.ValidationError("Country codes must be valid JSON array")
        return []


class TenantRoleForm(forms.ModelForm):
    """Form for managing tenant roles"""
    class Meta:
        model = TenantRole
        fields = ['name', 'description', 'is_system_role', 'is_assignable', 'permissions', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_system_role': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_assignable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permissions': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            # Limit permissions to those relevant to the application
            from django.contrib.auth.models import Permission
            self.fields['permissions'].queryset = Permission.objects.all()