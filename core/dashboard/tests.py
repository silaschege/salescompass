from django.test import TestCase, RequestFactory
from django.urls import reverse
from core.models import User
from .views import CockpitView, ManagerDashboardView, SupportDashboardView, AdminDashboardView

class DashboardViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com', 
            password='password',
            is_staff=True # Admin access for admin dashboard test
        )
        self.client.login(email='test@example.com', password='password')

    def test_cockpit_view(self):
        response = self.client.get(reverse('dashboard:cockpit'))
        self.assertEqual(response.status_code, 200)

    def test_manager_dashboard_view(self):
        response = self.client.get(reverse('dashboard:manager_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_support_dashboard_view(self):
        response = self.client.get(reverse('dashboard:support_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_view(self):
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
