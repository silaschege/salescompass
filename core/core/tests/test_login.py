from django.test import TestCase, Client
from django.urls import reverse
from core.models import User
from tenants.models import Tenant

class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name='Test Tenant', domain='test.com')
        self.user = User.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='password123',
            tenant_id=str(self.tenant.id)
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'email': 'test@test.com',
            'password': 'password123'
        }, follow=True)
        
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertRedirects(response, reverse('dashboard:cockpit'))

    def test_login_failure(self):
        response = self.client.post(reverse('login'), {
            'email': 'test@test.com',
            'password': 'wrongpassword'
        })
        
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, "Invalid email or password")
