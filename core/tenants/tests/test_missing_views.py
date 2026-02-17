from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant, NotificationTemplate, TenantLifecycleWorkflow

User = get_user_model()

class MissingViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create Tenant
        self.tenant = Tenant.objects.create(name='Test Tenant', subdomain='test')
        
        # Create User
        self.user = User.objects.create_superuser(
            username='admin', 
            email='admin@example.com', 
            password='password123',
            tenant=self.tenant
        )
        self.client.force_login(self.user)

    def test_notification_template_views(self):
        # List View
        url = reverse('tenants:notification_template_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/notification_template_list.html')

        # Create View
        url = reverse('tenants:notification_template_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/notification_template_form.html')

        data = {
            'name': 'Test Template',
            'subject': 'Test Subject',
            'message_body': 'Test Body',
            'notification_type': 'email',
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationTemplate.objects.count(), 1)
        
        template = NotificationTemplate.objects.first()
        self.assertEqual(template.name, 'Test Template')

        # Update View
        url = reverse('tenants:notification_template_update', kwargs={'pk': template.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data['name'] = 'Updated Template'
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        template.refresh_from_db()
        self.assertEqual(template.name, 'Updated Template')

        # Delete View
        url = reverse('tenants:notification_template_delete', kwargs={'pk': template.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/notification_template_confirm_delete.html')
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NotificationTemplate.objects.count(), 0)

    def test_lifecycle_workflow_views(self):
        # List View (Uses shared template lifecycle_workflows.html)
        url = reverse('tenants:lifecycle_workflows')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/lifecycle_workflows.html')

        # Create View
        url = reverse('tenants:lifecycle_workflow_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/lifecycle_workflow_form.html')

        data = {
            'name': 'Onboarding Workflow',
            'description': 'Test Description',
            'workflow_type': 'onboarding',
            'is_active': True,
            'steps': '[]',
            'created_by': self.user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TenantLifecycleWorkflow.objects.count(), 1)
        
        workflow = TenantLifecycleWorkflow.objects.first()
        self.assertEqual(workflow.name, 'Onboarding Workflow')
        self.assertEqual(workflow.created_by, self.user)

        # Detail View
        url = reverse('tenants:lifecycle_workflow_detail', kwargs={'pk': workflow.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/lifecycle_workflow_detail.html')

        # Update View
        url = reverse('tenants:lifecycle_workflow_update', kwargs={'pk': workflow.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data['name'] = 'Updated Workflow'
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        workflow.refresh_from_db()
        self.assertEqual(workflow.name, 'Updated Workflow')

        # Delete View
        url = reverse('tenants:lifecycle_workflow_delete', kwargs={'pk': workflow.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tenants/lifecycle_workflow_confirm_delete.html')
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TenantLifecycleWorkflow.objects.count(), 0)
