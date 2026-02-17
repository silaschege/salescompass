from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from .whatsapp_models import WhatsAppTemplate

User = get_user_model()

class WhatsAppTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test")
        self.user = User.objects.create_user(
            username="testuser", 
            email="test@example.com", 
            password="password",
            tenant=self.tenant
        )
        self.client.login(username="testuser", password="password")
        
        self.template = WhatsAppTemplate.objects.create(
            tenant=self.tenant,
            template_name="test_template",
            category="utility",
            language="en",
            body_text="Hello {{1}}",
            status="approved"
        )

    def test_whatsapp_template_list_view(self):
        url = reverse('communication:whatsapp_template_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test_template")

    def test_whatsapp_template_create_view(self):
        url = reverse('communication:whatsapp_template_create')
        data = {
            'template_name': 'new_template',
            'category': 'marketing',
            'language': 'en',
            'body_text': 'Promo for {{1}}',
            'variable_count': 1,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(WhatsAppTemplate.objects.filter(template_name='new_template').exists())

    def test_whatsapp_template_update_view(self):
        url = reverse('communication:whatsapp_template_edit', args=[self.template.id])
        data = {
            'template_name': 'updated_template',
            'category': 'utility',
            'language': 'en',
            'body_text': 'Updated body {{1}}',
            'variable_count': 1,
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.template.refresh_from_db()
        self.assertEqual(self.template.template_name, 'updated_template')

    def test_whatsapp_template_delete_view(self):
        url = reverse('communication:whatsapp_template_delete', args=[self.template.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WhatsAppTemplate.objects.filter(id=self.template.id).exists())
