from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import TenantUsage, ResourceLimit

User = get_user_model()

class InfrastructureViewTests(TestCase):
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
        
        # Create some dummy data
        self.tenant_usage = TenantUsage.objects.create(
            tenant_id=1,
            api_calls_count=500,
            api_calls_limit=1000,
            storage_used_gb=5.0,
            storage_limit_gb=10.0,
            active_db_connections=5,
            max_db_connections=20
        )
        self.resource_limit = ResourceLimit.objects.create(
            tenant_id=1,
            is_throttled=False
        )

    def test_dashboard_access_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'infrastructure/dashboard.html')

    def test_dashboard_access_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('infrastructure:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_tenant_usage_list_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:tenant_usage'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tenant Usage Overview')
        self.assertContains(response, '500 / 1000')

    def test_api_calls_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:api_calls'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'API Usage Monitoring')

    def test_storage_usage_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:storage_usage'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Storage Usage Monitoring')

    def test_db_connections_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:db_connections'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Database Connection Monitoring')

    def test_throttled_tenants_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:throttled_tenants'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Throttled Tenants')

    def test_resource_limit_update_view(self):
        self.client.force_login(self.superuser)
        url = reverse('infrastructure:resource_limit_update', args=[self.resource_limit.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test update
        response = self.client.post(url, {
            'is_throttled': True,
            'throttle_reason': 'Abuse detected',
            'custom_api_limit': 2000
        })
        self.assertEqual(response.status_code, 302) # Redirects on success
        
        self.resource_limit.refresh_from_db()
        self.assertTrue(self.resource_limit.is_throttled)
        self.assertEqual(self.resource_limit.throttle_reason, 'Abuse detected')
        self.assertEqual(self.resource_limit.custom_api_limit, 2000)

    def test_system_health_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:system_health'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'System Health Monitoring')

    def test_performance_metrics_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:performance_metrics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Performance Metrics')

    def test_resource_alerts_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('infrastructure:resource_alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resource Alerts')
