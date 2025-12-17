from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from accounts.models import Role

User = get_user_model()

class LeadsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        
        # Create a basic role for the user
        self.role = Role.objects.create(name="Admin", tenant=self.tenant)
        
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password",
            tenant=self.tenant,
            role=self.role
        )
        self.client.force_login(self.user)

    def test_lead_list_view(self):
        """
        Verify Lead List View returns 200 and uses the correct template.
        """
        response = self.client.get(reverse('leads:lead_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads/lead_list.html')
        self.assertTemplateUsed(response, 'core/patterns/list_view.html')
        self.assertContains(response, "Leads") # Page title block
        self.assertContains(response, "New Lead") # Action button

    def test_lead_create_view(self):
        """
        Verify Lead Create View returns 200 and uses the correct template.
        """
        response = self.client.get(reverse('leads:lead_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads/lead_form.html')
        self.assertTemplateUsed(response, 'core/patterns/form_view.html')
        self.assertContains(response, "New Lead") # Page title block
        self.assertContains(response, "Create Lead") # Button text
