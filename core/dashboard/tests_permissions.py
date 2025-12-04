from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from dashboard.models import DashboardConfig, DashboardWidget
import json

User = get_user_model()

class DashboardPermissionTests(TestCase):
    def setUp(self):
        # Create Superuser
        self.superuser = User.objects.create_superuser(
            username='superuser',
            email='superadmin@salescompass.com',
            password='password123'
        )
        
        # Create Admin (Staff)
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@acme.com',
            password='password123',
            is_staff=True
        )
        
        # Create Standard User
        self.standard_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123'
        )
        
        self.client = Client()
        
        # Create a test widget
        DashboardWidget.objects.create(
            widget_type='revenue',
            name='Revenue Chart',
            description='Shows revenue',
            template_path='dashboard/widgets/revenue.html',
            default_span=6
        )

    def test_superuser_can_build_dashboard(self):
        """Test that a superuser can access the builder and save a dashboard."""
        self.client.force_login(self.superuser)
        
        # 1. Access Builder
        response = self.client.get(reverse('dashboard:builder'))
        self.assertEqual(response.status_code, 200, "Superuser should be able to access builder")
        
        # 2. Save Dashboard
        data = {
            'name': 'Super Dashboard',
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
        
        self.assertEqual(response.status_code, 200, "Superuser should be able to save dashboard")
        self.assertTrue(response.json()['success'])
        
        # Verify DB
        self.assertTrue(DashboardConfig.objects.filter(user=self.superuser, name='Super Dashboard').exists())

    def test_admin_can_build_dashboard(self):
        """Test that an admin (staff) user can access the builder and save a dashboard."""
        self.client.force_login(self.admin_user)
        
        # 1. Access Builder
        response = self.client.get(reverse('dashboard:builder'))
        self.assertEqual(response.status_code, 200, "Admin should be able to access builder")
        
        # 2. Save Dashboard
        data = {
            'name': 'Admin Dashboard',
            'is_default': False,
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
        
        self.assertEqual(response.status_code, 200, "Admin should be able to save dashboard")
        self.assertTrue(response.json()['success'])
        
        # Verify DB
        self.assertTrue(DashboardConfig.objects.filter(user=self.admin_user, name='Admin Dashboard').exists())

    def test_standard_user_can_build_dashboard(self):
        """Test that a standard user can access the builder and save a dashboard."""
        self.client.force_login(self.standard_user)
        
        # 1. Access Builder
        response = self.client.get(reverse('dashboard:builder'))
        self.assertEqual(response.status_code, 200, "Standard user should be able to access builder")
        
        # 2. Save Dashboard
        data = {
            'name': 'User Dashboard',
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
        
        self.assertEqual(response.status_code, 200, "Standard user should be able to save dashboard")
        self.assertTrue(response.json()['success'])
        
        # Verify DB
        self.assertTrue(DashboardConfig.objects.filter(user=self.standard_user, name='User Dashboard').exists())
