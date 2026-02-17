from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import AuditLog

User = get_user_model()


class AuditLogsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )
        
        # Create test audit logs
        AuditLog.objects.create(
            user_id=self.user.id,
            user_email=self.user.email,
            tenant_id=1,
            action_type='USER_LOGIN',
            resource_type='User',
            resource_id='1',
            description='User logged in',
            severity='info',
            ip_address='127.0.0.1'
        )
        AuditLog.objects.create(
            user_id=self.user.id,
            user_email=self.user.email,
            tenant_id=1,
            action_type='DATA_UPDATE',
            resource_type='Lead',
            resource_id='1',
            description='Lead updated',
            severity='warning',
            ip_address='127.0.0.1',
            state_before={'status': 'new'},
            state_after={'status': 'contacted'}
        )

    def test_dashboard_access_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('audit_logs:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit_logs/dashboard.html')

    def test_dashboard_access_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('audit_logs:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_log_list_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('audit_logs:log_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'USER_LOGIN')

    def test_log_list_filtering(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('audit_logs:log_list') + '?action_type=LOGIN')
        self.assertEqual(response.status_code, 200)

    def test_log_detail_view(self):
        self.client.force_login(self.superuser)
        log = AuditLog.objects.first()
        response = self.client.get(reverse('audit_logs:log_detail', args=[log.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, log.user_email)

    def test_recent_actions_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('audit_logs:recent_actions'))
        self.assertEqual(response.status_code, 200)

    def test_critical_events_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('audit_logs:critical_events'))
        self.assertEqual(response.status_code, 200)

    def test_state_changes_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('audit_logs:state_changes'))
        self.assertEqual(response.status_code, 200)
        # Should show the log with state changes
        self.assertContains(response, 'DATA_UPDATE')

    def test_export_view_get(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('audit_logs:export_logs'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'audit_logs/export_form.html')

    def test_export_csv(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse('audit_logs:export_logs'), {
            'format': 'csv'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_export_json(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse('audit_logs:export_logs'), {
            'format': 'json'
        })
        self.assertEqual(response.status_code, 200)
