from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from tenants.models import Tenant

from core.models import Role

User = get_user_model()

class AppSelectionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password',
            first_name='Admin',
            last_name='User'
        )
        
        # Create Tenant
        self.tenant = Tenant.objects.create(name='Acme Corp', slug='acme-corp')
        
        # Create Roles
        self.manager_role = Role.objects.create(name='Manager')
        self.sales_role = Role.objects.create(name='Sales Agent')
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password',
            role=self.manager_role,
            tenant_id=str(self.tenant.id),
            first_name='Manager',
            last_name='User'
        )
        
        self.sales_user = User.objects.create_user(
            username='sales',
            email='sales@example.com',
            password='password',
            role=self.sales_role,
            tenant_id=str(self.tenant.id),
            first_name='Sales',
            last_name='User'
        )

    def test_superuser_sees_control_plane_apps(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('app_selection'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']
        app_names = [app['name'] for app in apps]
        
        self.assertIn('Tenants', app_names)
        self.assertIn('Billing', app_names)
        self.assertIn('Register Customer', app_names) # Should see app plane too
        
        user_info = response.context['user_info']
        self.assertEqual(user_info['company'], 'SalesCompass Internal')
        self.assertEqual(user_info['role'], 'Superuser')

    def test_manager_sees_manager_apps(self):
        self.client.force_login(self.manager_user)
        response = self.client.get(reverse('app_selection'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']
        app_names = [app['name'] for app in apps]
        
        self.assertNotIn('Tenants', app_names) # Control plane
        self.assertIn('Register Customer', app_names)
        self.assertIn('Reports', app_names)
        self.assertIn('Settings', app_names)
        
        user_info = response.context['user_info']
        self.assertEqual(user_info['company'], 'Acme Corp')
        self.assertEqual(user_info['role'], 'Manager')

    def test_sales_agent_sees_sales_apps(self):
        self.client.force_login(self.sales_user)
        response = self.client.get(reverse('app_selection'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']
        app_names = [app['name'] for app in apps]
        
        self.assertNotIn('Tenants', app_names)
        self.assertNotIn('Settings', app_names) # Manager only
        self.assertIn('Sale', app_names)
        self.assertIn('Reachout', app_names) # All users
        
        user_info = response.context['user_info']
        self.assertEqual(user_info['company'], 'Acme Corp')
        self.assertEqual(user_info['role'], 'Sales Agent')
