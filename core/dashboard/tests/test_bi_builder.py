from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from accounts.models import Role
from leads.models import Lead, LeadStatus
import json

User = get_user_model()

class BIBuilderAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.role = Role.objects.create(name="Admin", tenant=self.tenant)
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password",
            tenant=self.tenant,
            role=self.role
        )
        self.client.force_login(self.user)
        
        # Create some data for preview
        self.status = LeadStatus.objects.create(label="New", tenant=self.tenant)
        Lead.objects.create(
            first_name="Test", last_name="Lead", 
            salary=50000, 
            status_ref=self.status,
            tenant=self.tenant
        )

    def test_dashboard_save_api(self):
        """Verify saving a dashboard via API."""
        url = reverse('dashboard:dashboard_save_api')
        payload = {
            'name': 'API Dashboard',
            'widgets': [{'type': 'bar', 'config': {}}],
            'layout': {'rows': 1}
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(payload), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
    def test_dashboard_preview_api_number(self):
        """Verify preview API for a number widget (Count)."""
        url = reverse('dashboard:dashboard_preview_api')
        payload = {
            'type': 'number',
            'model': 'leads.lead',
            'aggregation': 'count'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['value'], 1)
        
    def test_dashboard_preview_api_chart(self):
        """Verify preview API for a chart widget (Group By)."""
        url = reverse('dashboard:dashboard_preview_api')
        payload = {
            'type': 'bar',
            'model': 'leads.lead',
            'aggregation': 'sum',
            'agg_field': 'salary',
            'group_by': 'status_ref' # Categorical
        }
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertIn('datasets', data)
        self.assertEqual(data['datasets'][0]['data'][0], 50000)
