from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import User, Role
from tenants.models import Tenant


class UserCreationForm(BaseUserCreationForm):
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        help_text="Assign user to a specific tenant (optional for superusers)"
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        help_text="Assign a role to the user (optional)"
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Set user as active/inactive"
    )
    is_staff = forms.BooleanField(
        required=False,
        help_text="Allow user to access admin site"
    )
    is_superuser = forms.BooleanField(
        required=False,
        help_text="Grant superuser privileges"
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'tenant', 'role', 'is_active', 'is_staff', 'is_superuser')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        help_text="Assign user to a specific tenant"
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        help_text="Assign a role to the user"
    )
    is_active = forms.BooleanField(
        required=False,
        help_text="Set user as active/inactive"
    )
    is_staff = forms.BooleanField(
        required=False,
        help_text="Allow user to access admin site"
    )
    is_superuser = forms.BooleanField(
        required=False,
        help_text="Grant superuser privileges"
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'tenant', 'role', 'is_active', 'is_staff', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email field read-only to prevent changing it to an existing one
        self.fields['email'].widget.attrs['readonly'] = True


class BulkUserUpdateForm(forms.Form):
    ACTION_CHOICES = [
        ('activate', 'Activate Users'),
        ('deactivate', 'Deactivate Users'),
        ('delete', 'Delete Users'),
        ('change_tenant', 'Change Tenant'),
        ('change_role', 'Change Role'),
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, required=True)
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False
    )
    user_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )


class UserInvitationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        max_length=254,
        help_text="Email address for the new user"
    )
    first_name = forms.CharField(
        label='First Name',
        max_length=30,
        required=False
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=150,
        required=False
    )
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
        required=True,
        help_text="Assign user to a specific tenant"
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=True,
        help_text="Assign a role to the user"
    )
    send_invite = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Send invitation email to user"
    )


class RoleManagementForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ('name', 'description', 'permissions')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit permission choices to relevant permissions
        from django.contrib.auth.models import Permission
        self.fields['permissions'].queryset = Permission.objects.select_related('content_type').all()


class SystemConfigurationForm(forms.Form):
    # General settings
    company_name = forms.CharField(max_length=255, required=False)
    company_email = forms.EmailField(required=False)
    company_phone = forms.CharField(max_length=20, required=False)
    
    # User management settings
    require_mfa = forms.BooleanField(required=False)
    password_min_length = forms.IntegerField(min_value=8, max_value=128, initial=8)
    password_require_uppercase = forms.BooleanField(required=False)
    password_require_lowercase = forms.BooleanField(required=False)
    password_require_numbers = forms.BooleanField(required=False)
    password_require_special = forms.BooleanField(required=False)
    
    # Session settings
    session_timeout = forms.IntegerField(min_value=1, help_text="Session timeout in minutes")
    max_login_attempts = forms.IntegerField(min_value=1, help_text="Max login attempts before lockout")
    lockout_duration = forms.IntegerField(min_value=1, help_text="Lockout duration in minutes")
    
    # Email settings
    smtp_host = forms.CharField(max_length=255, required=False)
    smtp_port = forms.IntegerField(min_value=1, max_value=65535, required=False, initial=587)
    smtp_username = forms.CharField(max_length=255, required=False)
    smtp_use_tls = forms.BooleanField(required=False, initial=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values from current settings
        from django.conf import settings
        self.fields['session_timeout'].initial = getattr(settings, 'SESSION_COOKIE_AGE', 1209600) // 60 # Convert to minutes
