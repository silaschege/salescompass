from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from tenants.models import Tenant
from accounts.models import Role, RoleAppPermission
from core.apps_registry import AVAILABLE_APPS

User = get_user_model()

class AppSettingsTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Tenant
        self.tenant = Tenant.objects.create(name='Acme Corp', slug='acme-corp')
        
        # Create Roles
        self.manager_role = Role.objects.create(name='Manager')
        self.sales_role = Role.objects.create(name='Sales Agent')
        
        # Create Users
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password',
            role=self.manager_role,
            tenant_id=str(self.tenant.id)
        )
        
    def test_app_settings_view_access(self):
        # Manager should not access settings
        self.client.force_login(self.manager_user)
        response = self.client.get(reverse('core:app_settings'))
        self.assertEqual(response.status_code, 403)
        
        # Superuser should access settings
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('core:app_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('configurable_apps', response.context)
        
    def test_permission_enforcement(self):
        # Identify a test app (e.g., 'reachout' -> leads:lead_list)
        test_app = next(app for app in AVAILABLE_APPS if app['id'] == 'reachout')
        
        # confirm manager sees it by default (or based on logic)
        self.client.force_login(self.manager_user)
        response = self.client.get(reverse('core:app_selection'))
        grouped_apps = response.context['grouped_apps']
        all_app_ids = [app['id'] for group in grouped_apps.values() for app in group]
        
        # Depending on logic, Reachout might be visible. 
        # Actually checking view logic: 'reachout' is in 'customer' category if URL resolves.
        # Assuming URL resolves for test (leads:lead_list usually exists)
        self.assertIn('reachout', all_app_ids)
        
        # Now Explicitly Hide it
        RoleAppPermission.objects.create(
            role=self.manager_role,
            app_identifier='reachout',
            is_visible=False
        )
        
        # Check again
        response = self.client.get(reverse('core:app_selection'))
        grouped_apps = response.context['grouped_apps']
        all_app_ids = [app['id'] for group in grouped_apps.values() for app in group]
        self.assertNotIn('reachout', all_app_ids)
        
    def test_update_permissions_via_view(self):
        self.client.force_login(self.superuser)
        
        test_app_id = 'accounts'
        field_name = f"perm_{self.manager_role.id}_{test_app_id}"
        
        # Post to disable (checkbox not sent means False/Off?)
        # Wait, the view logic: request.POST.get(field_name) == 'on'
        # So providing it as 'on' sets True. Omitted sets False (is_visible=False).
        
        # Case 1: Hide 'accounts' for Manager (omit from POST)
        response = self.client.post(reverse('core:app_settings'), {
            # Send other fields if validation requires, but here we just iterate roles/apps
        })
        self.assertEqual(response.status_code, 200)
        
        perm = RoleAppPermission.objects.get(role=self.manager_role, app_identifier=test_app_id)
        self.assertFalse(perm.is_visible)
        
        # Case 2: Show 'accounts' for Manager
        response = self.client.post(reverse('core:app_settings'), {
            field_name: 'on'
        })
        self.assertEqual(response.status_code, 200)
        
        perm.refresh_from_db()
        self.assertTrue(perm.is_visible)
