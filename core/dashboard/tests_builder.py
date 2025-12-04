from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from dashboard.models import DashboardConfig, DashboardWidget
import json

User = get_user_model()

class DashboardBuilderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            tenant_id='test-tenant-001'
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        # Create some test widgets
        DashboardWidget.objects.create(
            widget_type='revenue',
            name='Revenue Chart',
            description='Shows revenue',
            template_path='dashboard/widgets/revenue.html',
            default_span=6
        )
        DashboardWidget.objects.create(
            widget_type='pipeline',
            name='Sales Pipeline',
            description='Shows pipeline',
            template_path='dashboard/widgets/pipeline.html',
            default_span=6
        )
        
    def test_builder_view_access(self):
        """Test accessing the builder view."""
        response = self.client.get(reverse('dashboard:builder'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/builder.html')
        
    def test_save_dashboard(self):
        """Test saving a new dashboard."""
        data = {
            'name': 'Test Dashboard',
            'is_default': True,
            'layout': {
                'rows': [
                    {'cols': [{'widget': 'revenue', 'span': 6}]}
                ]
            }
        }
        
        response = self.client.post(
            reverse('dashboard:save_dashboard'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify db
        dashboard = DashboardConfig.objects.get(name='Test Dashboard')
        self.assertTrue(dashboard.is_default)
        self.assertEqual(dashboard.layout['rows'][0]['cols'][0]['widget'], 'revenue')
        
    def test_render_dashboard(self):
        """Test rendering a saved dashboard."""
        dashboard = DashboardConfig.objects.create(
            user=self.user,
            name='Render Test',
            layout={
                'rows': [
                    {'cols': [{'widget': 'revenue', 'span': 6}]}
                ]
            }
        )
        
        response = self.client.get(reverse('dashboard:render', kwargs={'pk': dashboard.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/render.html')
        self.assertEqual(response.context['dashboard'], dashboard)
        
    def test_update_dashboard(self):
        """Test updating an existing dashboard."""
        dashboard = DashboardConfig.objects.create(
            user=self.user,
            name='Original Name',
            layout={}
        )
        
        data = {
            'dashboard_id': dashboard.id,
            'name': 'Updated Name',
            'layout': {'rows': []}
        }
        
        response = self.client.post(
            reverse('dashboard:save_dashboard'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.name, 'Updated Name')
