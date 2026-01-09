from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import TenantRole, TenantMember, Tenant
import json

User = get_user_model()

class RoleManagementTests(TestCase):
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(name='Test Tenant', domain_prefix='test')
        
        # Create user
        self.user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='password123',
            tenant=self.tenant
        )
        
        # Create a tenant role
        self.admin_role = TenantRole.objects.create(
            name='admin_role',
            label='Admin',
            tenant=self.tenant
        )
        
        # Create TenantMember for the user
        self.tenant_member = TenantMember.objects.create(
            user=self.user,
            role=self.admin_role,
            tenant=self.tenant
        )
        
        self.client.force_login(self.user)

    def test_role_create_view_context(self):
        """Test that the role creation view has the correct context for the matrix."""
        url = reverse('settings_app:role_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('resources', response.context)
        self.assertIn('actions', response.context)
        self.assertIn('accounts', response.context['resources'])
        self.assertIn('read', response.context['actions'])

    def test_role_create_success(self):
        """Test creating a role from the matrix."""
        url = reverse('settings_app:role_create')
        
        data = {
            'name': 'sales_rep',
            'label': 'Sales Representative',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to role list
        self.assertRedirects(response, reverse('settings_app:role_list'))
        
        # Verify role was created
        role = TenantRole.objects.get(name='sales_rep')
        self.assertEqual(role.tenant, self.tenant)

    def test_role_update_view_context(self):
        """Test that the role update view renders correctly."""
        role = TenantRole.objects.create(
            name='support_agent',
            label='Support Agent',
            tenant=self.tenant
        )
        
        url = reverse('settings_app:role_update', args=[role.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('resources', response.context)
        
        form = response.context['form']
        self.assertEqual(form.instance.name, 'support_agent')

    def test_role_assignment(self):
        """Test assigning a role to a user (TenantMember)."""
        # Create a TenantRole
        role = TenantRole.objects.create(
            name='junior_sales',
            label='Junior Sales',
            tenant=self.tenant
        )
        
        # Create a new user to assign to
        new_user = User.objects.get_or_create(
            username='newuser',
            defaults={
                'email': 'new@example.com',
                'password': 'password123',
                'tenant': self.tenant
            }
        )[0]
        
        # Create TenantMember for this user
        team_member = TenantMember.objects.create(
            user=new_user,
            role=role,
            tenant=self.tenant
        )
        
        self.assertEqual(team_member.role, role)
        self.assertEqual(team_member.user.email, 'new@example.com')

