from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .models import User
from audit_logs.models import AuditLog
from accounts.models import Role
from tenants.models import Tenant


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to require superuser access"""
    def test_func(self):
        return self.request.user.is_superuser


class SecurityDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/security_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Security statistics
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['suspended_users'] = User.objects.filter(is_active=False).count()
        context['users_with_mfa'] = User.objects.filter(mfa_enabled=True).count()
        
        # Recent security events
        context['recent_security_events'] = AuditLog.objects.filter(
            Q(action_type__icontains='LOGIN') |
            Q(action_type__icontains='AUTH') |
            Q(action_type__icontains='PERMISSION') |
            Q(action_type__icontains='ACCESS') |
            Q(severity__in=['critical', 'error'])
        ).order_by('-timestamp')[:10]
        
        # Security trends
        context['security_trends'] = {
            'logins_today': AuditLog.objects.filter(
                action_type__icontains='LOGIN',
                timestamp__date=timezone.now().date()
            ).count(),
            'failed_attempts_today': AuditLog.objects.filter(
                action_type__icontains='LOGIN_FAILED',
                timestamp__date=timezone.now().date()
            ).count(),
            'permission_changes_today': AuditLog.objects.filter(
                action_type__icontains='PERMISSION',
                timestamp__date=timezone.now().date()
            ).count(),
        }
        
        return context


class IPWhitelistManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/ip_whitelist_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mock IP whitelist data
        context['whitelisted_ips'] = [
            {'id': 1, 'ip_address': '192.168.1.0/24', 'description': 'Corporate network', 'created_at': '2023-05-15'},
            {'id': 2, 'ip_address': '10.0.0.0/8', 'description': 'Internal systems', 'created_at': '2023-06-20'},
            {'id': 3, 'ip_address': '203.0.113.45', 'description': 'Trusted partner', 'created_at': '2023-07-10'},
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        
        if action == 'add':
            ip_address = request.POST.get('ip_address')
            description = request.POST.get('description')
            
            # In a real implementation, this would add the IP to a whitelist model
            messages.success(request, f"IP address {ip_address} added to whitelist.")
            
        elif action == 'remove':
            ip_id = request.POST.get('ip_id')
            # In a real implementation, this would remove the IP from the whitelist
            messages.success(request, f"IP address removed from whitelist.")
        
        return redirect('core:ip_whitelist_management')


class SecurityEventMonitoringView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = AuditLog
    template_name = 'core/security/security_event_monitoring.html'
    context_object_name = 'security_events'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = AuditLog.objects.filter(
            Q(action_type__icontains='LOGIN') |
            Q(action_type__icontains='AUTH') |
            Q(action_type__icontains='PERMISSION') |
            Q(action_type__icontains='ACCESS') |
            Q(severity__in=['critical', 'error'])
        ).order_by('-timestamp')
        
        # Apply filters
        severity = self.request.GET.get('severity')
        action_type = self.request.GET.get('action_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if severity:
            queryset = queryset.filter(severity=severity)
        if action_type:
            queryset = queryset.filter(action_type__icontains=action_type)
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['severities'] = ['critical', 'error', 'warning', 'info']
        context['action_types'] = [
            'LOGIN', 'LOGIN_FAILED', 'LOGOUT', 'PERMISSION', 
            'ACCESS', 'ACCESS_DENIED', 'DATA_MODIFICATION'
        ]
        return context


class IntrusionDetectionView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/intrusion_detection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mock intrusion detection data
        context['alerts'] = [
            {
                'id': 1,
                'timestamp': timezone.now() - timezone.timedelta(minutes=15),
                'type': 'Multiple failed login attempts',
                'severity': 'high',
                'source_ip': '198.51.100.25',
                'user': 'johndoe@example.com',
                'description': '5 failed login attempts within 5 minutes'
            },
            {
                'id': 2,
                'timestamp': timezone.now() - timezone.timedelta(minutes=30),
                'type': 'Unusual access pattern',
                'severity': 'medium',
                'source_ip': '203.0.113.45',
                'user': 'janedoe@example.com',
                'description': 'Access from unusual location'
            },
            {
                'id': 3,
                'timestamp': timezone.now() - timezone.timedelta(hours=2),
                'type': 'Privilege escalation attempt',
                'severity': 'high',
                'source_ip': '192.0.2.100',
                'user': 'system',
                'description': 'Attempt to access restricted resources'
            }
        ]
        
        context['statistics'] = {
            'total_alerts': len(context['alerts']),
            'high_severity': 2,
            'medium_severity': 1,
            'resolved_alerts': 5,
            'open_alerts': 3
        }
        
        return context


class SecureCredentialManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/secure_credential_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mock credential management data
        context['api_keys'] = [
            {
                'id': 1,
                'name': 'Production API Key',
                'key_prefix': 'prod_...',
                'created_at': '2023-01-15',
                'last_used': '2023-05-10',
                'status': 'active'
            },
            {
                'id': 2,
                'name': 'Development API Key',
                'key_prefix': 'dev_...',
                'created_at': '2023-03-20',
                'last_used': '2023-05-12',
                'status': 'active'
            },
            {
                'id': 3,
                'name': 'Legacy API Key',
                'key_prefix': 'legacy_...',
                'created_at': '2022-11-05',
                'last_used': '2023-01-15',
                'status': 'expired'
            }
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        
        if action == 'create':
            key_name = request.POST.get('key_name')
            # In a real implementation, this would create a new API key
            messages.success(request, f"API key '{key_name}' created successfully.")
            
        elif action == 'revoke':
            key_id = request.POST.get('key_id')
            # In a real implementation, this would revoke the API key
            messages.success(request, f"API key revoked.")
        
        return redirect('core:secure_credential_management')


class ComplianceDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/compliance_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Compliance statistics
        context['compliance_stats'] = {
            'gdpr_compliant_users': User.objects.filter(
                profile__consent_gdpr=True
            ).count() if hasattr(User, 'profile') else 0,
            'total_users': User.objects.count(),
            'data_retention_compliant': True,  # Mock value
            'audit_logs_available': True,  # Mock value
            'security_training_completed': 15,  # Mock value
            'total_employees': 25,  # Mock value
        }
        
        # Compliance requirements status
        context['requirements'] = [
            {
                'name': 'GDPR',
                'status': 'compliant',
                'last_audited': '2023-04-15',
                'next_review': '2023-10-15',
                'description': 'General Data Protection Regulation'
            },
            {
                'name': 'SOC2',
                'status': 'compliant',
                'last_audited': '2023-03-20',
                'next_review': '2023-09-20',
                'description': 'Service Organization Control 2'
            },
            {
                'name': 'CCPA',
                'status': 'partially_compliant',
                'last_audited': '2023-05-01',
                'next_review': '2023-11-01',
                'description': 'California Consumer Privacy Act'
            },
            {
                'name': 'HIPAA',
                'status': 'not_applicable',
                'last_audited': 'N/A',
                'next_review': 'N/A',
                'description': 'Health Insurance Portability and Accountability Act'
            }
        ]
        
        return context


class DataPrivacyManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/data_privacy_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Data privacy controls
        context['privacy_settings'] = {
            'gdpr_enabled': True,
            'ccpa_enabled': True,
            'data_portability_enabled': True,
            'right_to_deletion_enabled': True,
            'consent_management_enabled': True
        }
        
        # Privacy requests
        context['privacy_requests'] = [
            {
                'id': 1,
                'user_email': 'user1@example.com',
                'request_type': 'data_portability',
                'status': 'pending',
                'submitted_at': timezone.now() - timezone.timedelta(days=2)
            },
            {
                'id': 2,
                'user_email': 'user2@example.com',
                'request_type': 'right_to_deletion',
                'status': 'in_progress',
                'submitted_at': timezone.now() - timezone.timedelta(days=1)
            },
            {
                'id': 3,
                'user_email': 'user3@example.com',
                'request_type': 'consent_withdrawal',
                'status': 'completed',
                'submitted_at': timezone.now() - timezone.timedelta(days=5)
            }
        ]
        
        return context


class SecurityPolicyManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/security_policy_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Security policies
        context['policies'] = [
            {
                'id': 1,
                'name': 'Password Policy',
                'description': 'Minimum 12 characters, uppercase, lowercase, number, special character',
                'status': 'active',
                'last_updated': '2023-04-10'
            },
            {
                'id': 2,
                'name': 'MFA Policy',
                'description': 'Mandatory MFA for admin users',
                'status': 'active',
                'last_updated': '2023-03-15'
            },
            {
                'id': 3,
                'name': 'Access Policy',
                'description': 'Role-based access control with regular reviews',
                'status': 'active',
                'last_updated': '2023-05-01'
            },
            {
                'id': 4,
                'name': 'Network Policy',
                'description': 'IP whitelisting for admin access',
                'status': 'draft',
                'last_updated': '2023-05-10'
            }
        ]
        
        return context


class VulnerabilityManagementView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    template_name = 'core/security/vulnerability_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Vulnerability data
        context['vulnerabilities'] = [
            {
                'id': 1,
                'name': 'Outdated Library CVE-2023-1234',
                'severity': 'high',
                'status': 'open',
                'discovered': '2023-05-10',
                'description': 'Security vulnerability in authentication library'
            },
            {
                'id': 2,
                'name': 'Weak Password Hashing',
                'severity': 'medium',
                'status': 'in_progress',
                'discovered': '2023-04-25',
                'description': 'Using outdated hashing algorithm'
            },
            {
                'id': 3,
                'name': 'Missing Input Validation',
                'severity': 'low',
                'status': 'resolved',
                'discovered': '2023-04-15',
                'description': 'Potential for injection attacks'
            }
        ]
        
        return context
