from django import forms
from django.contrib.auth.models import Permission
from access_control.role_models import Role


class SystemConfigurationForm(forms.Form):
    # General settings
    company_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter company name'
    }))
    company_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter company email'
    }))
    company_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter company phone'
    }))
    
    # User management settings
    require_mfa = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    password_min_length = forms.IntegerField(
        min_value=8, 
        max_value=128, 
        initial=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '8',
            'max': '128'
        })
    )
    password_require_uppercase = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    password_require_lowercase = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    password_require_numbers = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    password_require_special = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    
    # Session settings
    session_timeout = forms.IntegerField(
        min_value=1, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        }),
        help_text="Session timeout in minutes"
    )
    max_login_attempts = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        }),
        help_text="Max login attempts before lockout"
    )
    lockout_duration = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        }),
        help_text="Lockout duration in minutes"
    )
    
    # Email settings
    smtp_host = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'SMTP server host'
    }))
    smtp_port = forms.IntegerField(
        min_value=1, 
        max_value=65535, 
        required=False, 
        initial=587,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '65535'
        })
    )
    smtp_username = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'SMTP username'
    }))
    smtp_use_tls = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    smtp_use_ssl = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values from current settings
        from django.conf import settings
        self.fields['session_timeout'].initial = getattr(settings, 'SESSION_COOKIE_AGE', 1209600) // 60  # Convert to minutes
        self.fields['company_name'].initial = getattr(settings, 'COMPANY_NAME', '')
        self.fields['company_email'].initial = getattr(settings, 'COMPANY_EMAIL', '')
        self.fields['company_phone'].initial = getattr(settings, 'COMPANY_PHONE', '')


class RoleManagementForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ('name', 'description', 'tenant', 'is_system_role', 'is_assignable')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DataExportForm(forms.Form):
    EXPORT_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    include_sensitive = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    data_types = forms.MultipleChoiceField(
        choices=[
            ('users', 'Users'),
            ('accounts', 'Accounts'),
            ('leads', 'Leads'),
            ('opportunities', 'Opportunities'),
            ('activities', 'Activities'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True
    )


class DataRetentionForm(forms.Form):
    retention_period = forms.ChoiceField(
        choices=[
            ('30', '30 days'),
            ('90', '90 days'),
            ('180', '180 days'),
            ('365', '1 year'),
            ('730', '2 years'),
            ('never', 'Never delete'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    auto_purge = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    notify_before_purge = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    notification_days = forms.IntegerField(
        min_value=1,
        max_value=30,
        initial=7,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '30'
        })
    )


class SystemBackupForm(forms.Form):
    BACKUP_TYPE_CHOICES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
        ('database_only', 'Database Only'),
        ('files_only', 'Files Only'),
    ]
    
    backup_type = forms.ChoiceField(
        choices=BACKUP_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    storage_location = forms.ChoiceField(
        choices=[
            ('local', 'Local Storage'),
            ('s3', 'Amazon S3'),
            ('gcs', 'Google Cloud Storage'),
            ('azure', 'Microsoft Azure'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    encrypt_backup = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    retention_days = forms.IntegerField(
        min_value=1,
        max_value=3650,  # 10 years max
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '3650'
        })
    )
    notify_completion = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
