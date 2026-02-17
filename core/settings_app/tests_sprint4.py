from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from core.models import Role
from settings_app.models import CustomField, ModuleLabel, AssignmentRule
import json

User = get_user_model()


class CustomFieldFormTests(TestCase):
    """Test custom field form submission, validation, and success."""
    
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_staff=True
        )
        self.client.login(username='admin@test.com', password='testpass123')
    
    def test_custom_field_create_success(self):
        """Test successful custom field creation."""
        data = {
            'model_name': 'Lead',
            'field_name': 'industry_sector',
            'field_label': 'Industry Sector',
            'field_type': 'select',
            'is_required': True,
            'options': 'Technology\nFinance\nHealthcare',
            'help_text': 'Select your industry',
            'default_value': '',
        }
        
        response = self.client.post(
            reverse('settings_app:custom_field_create'),
            data=data
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify field was created
        field = CustomField.objects.filter(
            tenant_id=self.tenant.id,
            field_name='industry_sector'
        ).first()
        self.assertIsNotNone(field)
        self.assertEqual(field.field_label, 'Industry Sector')
        self.assertEqual(field.field_type, 'select')
        self.assertTrue(field.is_required)
        print("✓ Custom field created successfully")
    
    def test_custom_field_validation_errors(self):
        """Test validation errors display correctly."""
        # Missing required field
        data = {
            'model_name': '',  # Required field missing
            'field_name': 'test_field',
            'field_label': 'Test Field',
            'field_type': 'text',
        }
        
        response = self.client.post(
            reverse('settings_app:custom_field_create'),
            data=data
        )
        
        # Should return to form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error')
        print("✓ Validation errors displayed correctly")
    
    def test_custom_field_duplicate_prevention(self):
        """Test that duplicate field names are prevented."""
        # Create initial field
        CustomField.objects.create(
            tenant_id=self.tenant.id,
            model_name='Lead',
            field_name='test_field',
            field_label='Test Field',
            field_type='text'
        )
        
        # Try to create duplicate
        data = {
            'model_name': 'Lead',
            'field_name': 'test_field',
            'field_label': 'Test Field 2',
            'field_type': 'text',
        }
        
        response = self.client.post(
            reverse('settings_app:custom_field_create'),
            data=data
        )
        
        # Should show error (unique constraint)
        self.assertIn(response.status_code, [200, 400])
        print("✓ Duplicate field prevention working")


class ModuleLabelFormTests(TestCase):
    """Test module label form submission and validation."""
    
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_staff=True
        )
        self.client.login(username='admin@test.com', password='testpass123')
    
    def test_module_label_create_success(self):
        """Test successful module label creation."""
        data = {
            'module_key': 'leads',
            'custom_label': 'Prospect',
            'custom_label_plural': 'Prospects',
        }
        
        response = self.client.post(
            reverse('settings_app:module_label_create'),
            data=data
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify label was created
        label = ModuleLabel.objects.filter(
            tenant_id=self.tenant.id,
            module_key='leads'
        ).first()
        self.assertIsNotNone(label)
        self.assertEqual(label.custom_label, 'Prospect')
        self.assertEqual(label.custom_label_plural, 'Prospects')
        print("✓ Module label created successfully")
    
    def test_module_label_without_plural(self):
        """Test module label creation without plural form."""
        data = {
            'module_key': 'opportunities',
            'custom_label': 'Deal',
            'custom_label_plural': '',
        }
        
        response = self.client.post(
            reverse('settings_app:module_label_create'),
            data=data
        )
        
        # Should still succeed
        self.assertEqual(response.status_code, 302)
        
        label = ModuleLabel.objects.filter(
            tenant_id=self.tenant.id,
            module_key='opportunities'
        ).first()
        self.assertIsNotNone(label)
        self.assertEqual(label.custom_label, 'Deal')
        print("✓ Module label without plural works")


class AssignmentRuleFormTests(TestCase):
    """Test assignment rule form submission and validation."""
    
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_staff=True
        )
        self.assignee1 = User.objects.create_user(
            username='user1@test.com',
            email='user1@test.com',
            password='testpass123',
            tenant=self.tenant
        )
        self.assignee2 = User.objects.create_user(
            username='user2@test.com',
            email='user2@test.com',
            password='testpass123',
            tenant=self.tenant
        )
        self.client.login(username='admin@test.com', password='testpass123')
    
    def test_assignment_rule_create_success(self):
        """Test successful assignment rule creation."""
        data = {
            'name': 'US Leads Rule',
            'module': 'leads',
            'rule_type': 'round_robin',
            'criteria': '{"country": "US"}',
            'assignees': [self.assignee1.id, self.assignee2.id],
            'priority': 10,
            'is_active': True,
        }
        
        response = self.client.post(
            reverse('settings_app:assignment_rule_create'),
            data=data
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify rule was created
        rule = AssignmentRule.objects.filter(
            tenant_id=self.tenant.id,
            name='US Leads Rule'
        ).first()
        self.assertIsNotNone(rule)
        self.assertEqual(rule.module, 'leads')
        self.assertEqual(rule.rule_type, 'round_robin')
        self.assertEqual(rule.priority, 10)
        self.assertEqual(rule.assignees.count(), 2)
        print("✓ Assignment rule created successfully")
    
    def test_assignment_rule_invalid_json(self):
        """Test validation with invalid JSON criteria."""
        data = {
            'name': 'Test Rule',
            'module': 'leads',
            'rule_type': 'criteria',
            'criteria': '{invalid json}',  # Invalid JSON
            'assignees': [self.assignee1.id],
            'priority': 5,
            'is_active': True,
        }
        
        response = self.client.post(
            reverse('settings_app:assignment_rule_create'),
            data=data
        )
        
        # Should show error
        self.assertIn(response.status_code, [200, 400])
        print("✓ Invalid JSON validation working")


class TenantSettingsFormTests(TestCase):
    """Test tenant settings form submission and validation."""
    
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_staff=True,
            is_superuser=True
        )
        self.client.login(username='admin@test.com', password='testpass123')
    
    def test_tenant_settings_update_colors(self):
        """Test updating tenant color settings."""
        data = {
            'name': self.tenant.name,
            'domain': 'test.example.com',
            'primary_color': '#ff0000',
            'secondary_color': '#00ff00',
            'business_hours': '{}',
            'default_currency': 'USD',
            'date_format': '%Y-%m-%d',
            'time_zone': 'UTC',
        }
        
        response = self.client.post(
            reverse('settings_app:tenant_settings'),
            data=data
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify settings were updated
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.primary_color, '#ff0000')
        self.assertEqual(self.tenant.secondary_color, '#00ff00')
        print("✓ Tenant colors updated successfully")
    
    def test_tenant_settings_business_hours(self):
        """Test updating business hours JSON."""
        business_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": "closed",
            "sunday": "closed"
        }
        
        data = {
            'name': self.tenant.name,
            'domain': 'test.example.com',
            'primary_color': '#6f42c1',
            'secondary_color': '#e3e6f3',
            'business_hours': json.dumps(business_hours),
            'default_currency': 'USD',
            'date_format': '%Y-%m-%d',
            'time_zone': 'America/New_York',
        }
        
        response = self.client.post(
            reverse('settings_app:tenant_settings'),
            data=data
        )
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify business hours were saved
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.business_hours, business_hours)
        self.assertEqual(self.tenant.time_zone, 'America/New_York')
        print("✓ Business hours updated successfully")


class TemplateRenderingTests(TestCase):
    """Test that templates render correctly."""
    
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_staff=True
        )
        self.client.login(username='admin@test.com', password='testpass123')
    
    def test_custom_field_form_renders(self):
        """Test custom field form template renders."""
        response = self.client.get(reverse('settings_app:custom_field_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Custom Field')
        self.assertContains(response, 'Module')
        self.assertContains(response, 'Field Type')
        print("✓ Custom field form renders correctly")
    
    def test_custom_field_list_renders(self):
        """Test custom field list template renders."""
        response = self.client.get(reverse('settings_app:custom_field_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Custom Fields')
        print("✓ Custom field list renders correctly")
    
    def test_module_label_form_renders(self):
        """Test module label form template renders."""
        response = self.client.get(reverse('settings_app:module_label_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Module Label')
        self.assertContains(response, 'Module')
        print("✓ Module label form renders correctly")
    
    def test_module_label_list_renders(self):
        """Test module label list template renders."""
        response = self.client.get(reverse('settings_app:module_label_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Module Labels')
        print("✓ Module label list renders correctly")
    
    def test_assignment_rule_form_renders(self):
        """Test assignment rule form template renders."""
        response = self.client.get(reverse('settings_app:assignment_rule_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assignment Rule')
        self.assertContains(response, 'Rule Type')
        print("✓ Assignment rule form renders correctly")
    
    def test_tenant_settings_form_renders(self):
        """Test tenant settings form template renders."""
        response = self.client.get(reverse('settings_app:tenant_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tenant Settings')
        self.assertContains(response, 'Branding')
        print("✓ Tenant settings form renders correctly")
