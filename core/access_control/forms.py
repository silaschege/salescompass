from django import forms
from .models import AccessControl, TenantAccessControl, RoleAccessControl, UserAccessControl
from .role_models import Role
from tenants.models import Tenant
from core.models import User

class AccessControlDefinitionForm(forms.ModelForm):
    """
    Form for defining a new system-wide Access Control (Permission/Feature).
    """
    class Meta:
        model = AccessControl
        fields = ['name', 'key', 'description', 'access_type', 'default_enabled']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'key': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'access_type': forms.Select(attrs={'class': 'form-select'}),
            'default_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RoleAccessAssignmentForm(forms.ModelForm):
    """
    Form for assigning an Access Control to a Role.
    """
    class Meta:
        model = RoleAccessControl
        fields = ['role', 'access_control', 'is_enabled', 'config_data']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'access_control': forms.Select(attrs={'class': 'form-select'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        assigned_ids = []
        if 'role' in self.data:
            try:
                role_id = int(self.data.get('role'))
                assigned_ids = RoleAccessControl.objects.filter(role_id=role_id).values_list('access_control_id', flat=True)
            except (ValueError, TypeError):
                pass
        elif 'role' in self.initial:
            role_id = self.initial.get('role')
            if role_id:
               assigned_ids = RoleAccessControl.objects.filter(role_id=role_id).values_list('access_control_id', flat=True)
               
        if assigned_ids:
             self.fields['access_control'].queryset = AccessControl.objects.exclude(id__in=assigned_ids).filter(access_type='permission').order_by('name')
        else:
             self.fields['access_control'].queryset = AccessControl.objects.filter(access_type='permission').order_by('name')


class UserAccessAssignmentForm(forms.ModelForm):
    """
    Form for assigning an Access Control to a User.
    """
    class Meta:
        model = UserAccessControl
        fields = ['user', 'access_control', 'is_enabled', 'config_data']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'access_control': forms.Select(attrs={'class': 'form-select'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        assigned_ids = []
        if 'user' in self.data:
            try:
                user_id = int(self.data.get('user'))
                assigned_ids = UserAccessControl.objects.filter(user_id=user_id).values_list('access_control_id', flat=True)
            except (ValueError, TypeError):
                pass
        elif 'user' in self.initial:
             user_id = self.initial.get('user')
             if user_id:
                assigned_ids = UserAccessControl.objects.filter(user_id=user_id).values_list('access_control_id', flat=True)
        
        if assigned_ids:
             self.fields['access_control'].queryset = AccessControl.objects.exclude(id__in=assigned_ids).filter(access_type='permission').order_by('name')
        else:
             self.fields['access_control'].queryset = AccessControl.objects.filter(access_type='permission').order_by('name')

class TenantAccessAssignmentForm(forms.ModelForm):
    """
    Form for assigning an existing Access Control to a Tenant.
    """
    class Meta:
        model = TenantAccessControl
        fields = ['tenant', 'access_control', 'is_enabled', 'config_data']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'access_control': forms.Select(attrs={'class': 'form-select'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Determine tenant from bound data or initial
        tenant_id = None
        if 'tenant' in self.data:
            try:
                tenant_id = int(self.data.get('tenant'))
            except (ValueError, TypeError):
                pass
        elif 'tenant' in self.initial:
            tenant_id = self.initial.get('tenant')
            
        if tenant_id:
            # Filter out access controls already assigned to this tenant
            assigned_ids = TenantAccessControl.objects.filter(tenant_id=tenant_id).values_list('access_control_id', flat=True)
            self.fields['access_control'].queryset = AccessControl.objects.exclude(id__in=assigned_ids).order_by('name')
        else:
            self.fields['access_control'].queryset = AccessControl.objects.all().order_by('name')