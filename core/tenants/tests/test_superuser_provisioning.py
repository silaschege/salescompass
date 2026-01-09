from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from billing.models import Plan, Subscription

User = get_user_model()

class SuperuserProvisioningTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create Superuser
        self.superuser = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='password123'
        )
        self.client.force_login(self.superuser)
        
        # Create Plan
        self.plan = Plan.objects.create(name='Enterprise', price=99.99, is_active=True)
        self.url = reverse('tenants:provision_new')

    def test_provisioning_flow(self):
        # 1. Access Page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # 2. Submit Valid Form
        data = {
            'email': 'newclient@acme.com',
            'first_name': 'Road',
            'last_name': 'Runner',
            'password': 'initialPassword123!',
            'company_name': 'Acme Corp',
            'subdomain': 'acme-corp',
            'plan': self.plan.id
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302) # Success redirect

        # 3. Verify Creation
        # Tenant
        tenant = Tenant.objects.get(subdomain='acme-corp')
        self.assertEqual(tenant.name, 'Acme Corp')
        self.assertEqual(tenant.plan, self.plan)
        
        # User
        user = User.objects.get(email='newclient@acme.com')
        self.assertEqual(user.first_name, 'Road')
        self.assertTrue(user.check_password('initialPassword123!'))
        self.assertEqual(user.tenant, tenant)
        self.assertEqual(tenant.tenant_admin, user)
        
        # Subscription
        sub = Subscription.objects.get(tenant=tenant)
        self.assertEqual(sub.subscription_plan, self.plan)
        self.assertTrue(sub.subscription_is_active)

    def test_non_superuser_access(self):
        self.client.logout()
        user = User.objects.create_user(username='normal', email='normal@example.com', password='pw')
        self.client.force_login(user)
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403) # Permission Denied
