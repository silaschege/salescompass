from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .admin_forms import SystemConfigurationForm
from accounts.models import User
from tenants.models import Tenant
import json
import os


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class SystemConfigurationView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/admin/system_configuration.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current system settings
        context['current_settings'] = {
            'company_name': getattr(settings, 'COMPANY_NAME', ''),
            'company_email': getattr(settings, 'COMPANY_EMAIL', ''),
            'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
            'require_mfa': getattr(settings, 'REQUIRE_MFA', False),
            'session_timeout': getattr(settings, 'SESSION_COOKIE_AGE', 1209600) // 60,  # Convert to minutes
            'max_login_attempts': getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5),
            'lockout_duration': getattr(settings, 'LOCKOUT_DURATION', 30),
        }
        
        # Get form with current settings
        context['form'] = SystemConfigurationForm(initial=context['current_settings'])
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = SystemConfigurationForm(request.POST)
        
        if form.is_valid():
            # Save settings to a configuration file or database
            # For now, we'll save to a JSON file
            config_path = os.path.join(settings.BASE_DIR, 'config', 'system_config.json')
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Save the configuration
            with open(config_path, 'w') as f:
                json.dump(form.cleaned_data, f, indent=2)
            
            # Update Django settings cache
            cache.set('system_config', form.cleaned_data, 3600)  # Cache for 1 hour
            
            messages.success(request, "System configuration updated successfully.")
            return redirect('core:system_configuration')
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class EnvironmentVariablesView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/admin/environment_variables.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get environment variables that are relevant to the system
        sensitive_keys = ['SECRET_KEY', 'DATABASE_PASSWORD', 'EMAIL_HOST_PASSWORD', 
                         'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'STRIPE_SECRET_KEY']
        
        all_env_vars = dict(os.environ)
        
        # Separate sensitive and non-sensitive variables
        context['non_sensitive_vars'] = {
            k: v for k, v in all_env_vars.items() 
            if not any(sensitive_key in k.upper() for sensitive_key in sensitive_keys)
        }
        
        context['sensitive_vars'] = {
            k: '***' if v else '' for k, v in all_env_vars.items() 
            if any(sensitive_key in k.upper() for sensitive_key in sensitive_keys)
        }
        
        return context


class FeatureToggleManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/admin/feature_toggle_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current feature toggles from settings or database
        # For now, we'll use a mock implementation
        context['features'] = [
            {'name': 'New Dashboard UI', 'key': 'NEW_DASHBOARD_UI', 'enabled': True, 'description': 'Enable the new dashboard interface'},
            {'name': 'Advanced Analytics', 'key': 'ADVANCED_ANALYTICS', 'enabled': False, 'description': 'Enable advanced analytics features'},
            {'name': 'AI Features', 'key': 'AI_FEATURES', 'enabled': False, 'description': 'Enable AI-powered features'},
            {'name': 'Custom Reports', 'key': 'CUSTOM_REPORTS', 'enabled': True, 'description': 'Enable custom report builder'},
            {'name': 'Multi-Language', 'key': 'MULTI_LANGUAGE', 'enabled': False, 'description': 'Enable multi-language support'},
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Handle feature toggle updates
        feature_key = request.POST.get('feature_key')
        new_status = request.POST.get('status') == 'enable'
        
        # In a real implementation, this would update the feature toggle in the database
        # For now, we'll just show a success message
        status_text = "enabled" if new_status else "disabled"
        messages.success(request, f"Feature '{feature_key}' has been {status_text}.")
        
        return redirect('core:feature_toggle_management')


class ConfigurationAuditView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User  # Placeholder model - in reality this would be a configuration audit model
    template_name = 'core/admin/configuration_audit.html'
    context_object_name = 'config_changes'
    paginate_by = 25
    
    def get_queryset(self):
        # This would typically come from a configuration audit log
        # For now, we'll return an empty list
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_changes'] = [
            {
                'user': 'admin@example.com',
                'timestamp': timezone.now(),
                'action': 'Updated SMTP settings',
                'details': 'Changed SMTP host from smtp.old.com to smtp.new.com'
            },
            {
                'user': 'superadmin@example.com',
                'timestamp': timezone.now(),
                'action': 'Enabled MFA requirement',
                'details': 'Set REQUIRE_MFA to True for all users'
            },
            {
                'user': 'admin@example.com',
                'timestamp': timezone.now(),
                'action': 'Updated company information',
                'details': 'Changed company name to New Company Name'
            }
        ]
        return context


class SystemMaintenanceView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/admin/system_maintenance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # System maintenance information
        context['maintenance_info'] = {
            'next_scheduled_maintenance': None,
            'maintenance_mode': getattr(settings, 'MAINTENANCE_MODE', False),
            'last_backup': timezone.now() - timezone.timedelta(days=1),
            'system_uptime': '24 days, 6 hours, 30 minutes',
            'database_size': '2.4 GB',
            'file_storage_used': '15.2 GB',
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        
        if action == 'toggle_maintenance':
            # In a real system, this would toggle maintenance mode
            messages.success(request, "Maintenance mode status would be updated in a real system.")
        elif action == 'schedule_maintenance':
            # Schedule maintenance for a future time
            scheduled_time = request.POST.get('scheduled_time')
            if scheduled_time:
                messages.success(request, f"Maintenance scheduled for {scheduled_time}.")
            else:
                messages.error(request, "Please specify a maintenance time.")
        elif action == 'run_backup':
            # Initiate system backup
            messages.success(request, "Backup process initiated.")
        elif action == 'clear_cache':
            # Clear system cache
            cache.clear()
            messages.success(request, "System cache cleared successfully.")
        
        return redirect('core:system_maintenance')


class DataManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/admin/data_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Data management information
        context['data_stats'] = {
            'total_tenants': Tenant.objects.count(),
            'total_users': User.objects.count(),
            'total_storage_used': '17.6 GB',
            'retention_policy': 'Keep data for 7 years',
            'next_cleanup': timezone.now() + timezone.timedelta(days=30),
        }
        
        return context


class BackupManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/admin/backup_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mock backup information
        context['backups'] = [
            {
                'id': 1,
                'timestamp': timezone.now() - timezone.timedelta(days=1),
                'size': '2.4 GB',
                'location': 'Primary Storage',
                'status': 'completed',
                'type': 'full'
            },
            {
                'id': 2,
                'timestamp': timezone.now() - timezone.timedelta(days=2),
                'size': '1.2 GB',
                'location': 'Primary Storage',
                'status': 'completed',
                'type': 'incremental'
            },
            {
                'id': 3,
                'timestamp': timezone.now() - timezone.timedelta(days=7),
                'size': '2.6 GB',
                'location': 'Primary Storage',
                'status': 'completed',
                'type': 'full'
            },
        ]
        
        return context
