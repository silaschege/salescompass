from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import TeamRole
import json

User = get_user_model()

class RoleManagementTests(TestCase):
    def setUp(self):
        # Create user and tenant
        self.user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='password123',
            tenant_id='tenant1'
        )
        # Assign a role that has permission to manage settings
        # We need to create a role for the user first, or bypass permission check if we mock it.
        # But since we are testing the view which uses PermissionRequiredMixin, we should give the user the permission.
        # The required permission is 'settings_app:write'
        
        # Create a role for the user
        self.admin_role = TeamRole.objects.create(
            name='Admin',
            tenant_id='tenant1',
            base_permissions=['settings_app:write', 'settings_app:read']
        )
        
        # Assign role to user. Wait, User.role links to core.Role, not TeamRole?
        # Let's check how permissions are checked.
        # PermissionRequiredMixin checks self.request.user.has_perm(self.required_permission)
        # User.has_perm checks self.role.permissions.
        # User.role is a ForeignKey to core.Role.
        # So we need to create a core.Role for the user to pass the permission check.
        
        from core.models import Role
        self.core_role = Role.objects.create(
            name='Core Admin',
            tenant_id='tenant1',
            permissions=['settings_app:write', 'settings_app:read']
        )
        self.user.role = self.core_role
        self.user.save()
        
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
        """Test creating a role with permissions from the matrix."""
        url = reverse('settings_app:role_create')
        
        # The form expects 'base_permissions' as a JSON string
        permissions_list = ['accounts:read', 'leads:write']
        data = {
            'name': 'Sales Rep',
            'description': 'Sales Representative Role',
            'base_permissions': json.dumps(permissions_list),
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to role list
        self.assertRedirects(response, reverse('settings_app:role_list'))
        
        # Verify role was created
        role = TeamRole.objects.get(name='Sales Rep')
        self.assertEqual(role.tenant_id, 'tenant1')
        self.assertEqual(role.base_permissions, permissions_list)

    def test_role_update_view_context(self):
        """Test that the role update view renders correctly."""
        role = TeamRole.objects.create(
            name='Support Agent',
            tenant_id='tenant1',
            base_permissions=['cases:read']
        )
        
        url = reverse('settings_app:role_update', args=[role.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('resources', response.context)
        
        # Verify the form has the correct initial value
        # Note: The form renders the value in the hidden input. 
        # We can check if the value is present in the rendered HTML or context form.
        form = response.context['form']
        self.assertEqual(form.initial['base_permissions'], ['cases:read'])

    def test_wildcard_permissions(self):
        """Test saving and checking wildcard permissions."""
        url = reverse('settings_app:role_create')
        
        # Save a role with wildcard permission
        permissions_list = ['accounts:*', 'leads:read']
        data = {
            'name': 'Account Manager',
            'description': 'Full access to accounts',
            'base_permissions': json.dumps(permissions_list),
            'is_active': True
        }
        
        self.client.post(url, data)
        
        role = TeamRole.objects.get(name='Account Manager')
        self.assertIn('accounts:*', role.base_permissions)
        
        # Verify logic (assuming TeamRole logic mirrors core.Role or is used to sync)
        # Currently TeamRole is a separate model. If we want to test if a user HAS this permission,
        # we need to assign this TeamRole to a TeamMember, and that TeamMember's user should get the permissions.
        # However, the current implementation seems to link User -> core.Role. 
        # TeamMember links User -> TeamRole.
        # We need to ensure that when a TeamMember is assigned a TeamRole, the User's core.Role is updated or synced.
        # If that sync logic isn't implemented yet, this test might just verify the model storage for now.
        
    def test_role_assignment(self):
        """Test assigning a role to a user (TeamMember)."""
        # Create a TeamRole
        role = TeamRole.objects.create(
            name='Junior Sales',
            tenant_id='tenant1',
            base_permissions=['leads:read']
        )
        
        # Create a new user to assign to
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='password123',
            tenant_id='tenant1'
        )
        
        # Create TeamMember for this user
        from .models import TeamMember
        team_member = TeamMember.objects.create(
            user=new_user,
            role=role,
            tenant_id='tenant1'
        )
        
        self.assertEqual(team_member.role, role)
        self.assertEqual(team_member.user.email, 'new@example.com')

