from django.test import TestCase, Client
from django.urls import reverse
from core.models import User
from tenants.models import Tenant, TenantFeatureEntitlement
from django.contrib.messages import get_messages

class FeatureTogglesTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True
        )
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            tenant=self.tenant
        )
        self.client.login(username="testuser", password="password123")
        self.url = reverse('tenants:feature_toggles')

    def test_feature_toggles_view_get(self):
        """Test that the view renders correctly with a selected tenant"""
        response = self.client.get(self.url, {'tenant_id': self.tenant.id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/feature_toggles.html')
        self.assertIn('tenant', response.context)
        self.assertEqual(response.context['tenant'].id, self.tenant.id)

    def test_add_feature_toggle(self):
        """Test adding a new feature toggle via POST"""
        data = {
            'tenant_id': self.tenant.id,
            'feature_name': 'test_feature',
            'enabled': True,
            'description': 'A test feature toggle'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200) # FormView returns 200 if success_url is redirect but it stays on same page if not overridden or handled
        
        # Verify entitlement was created
        entitlement = TenantFeatureEntitlement.objects.get(tenant=self.tenant, feature_name='test_feature')
        self.assertTrue(entitlement.is_enabled)
        self.assertEqual(entitlement.notes, 'A test feature toggle')
        self.assertEqual(entitlement.feature_key, 'test_feature')

    def test_update_feature_toggle(self):
        """Test updating an existing feature toggle"""
        # First create an entitlement
        TenantFeatureEntitlement.objects.create(
            tenant=self.tenant,
            feature_key='test_feature',
            feature_name='test_feature',
            is_enabled=False
        )
        
        data = {
            'tenant_id': self.tenant.id,
            'feature_name': 'test_feature',
            'enabled': True,
            'description': 'Updated description'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        
        # Verify entitlement was updated
        entitlement = TenantFeatureEntitlement.objects.get(tenant=self.tenant, feature_name='test_feature')
        self.assertTrue(entitlement.is_enabled)
        self.assertEqual(entitlement.notes, 'Updated description')
