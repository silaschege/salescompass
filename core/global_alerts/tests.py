from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Alert
from .utils import get_active_alerts, get_alert_statistics

User = get_user_model()


class AlertModelTests(TestCase):
    def setUp(self):
        self.alert = Alert.objects.create(
            title='Test Alert',
            message='Test message',
            alert_type='general',
            severity='info',
            is_global=True,
            created_by='admin'
        )

    def test_alert_creation(self):
        self.assertEqual(self.alert.title, 'Test Alert')
        self.assertTrue(self.alert.is_active)

    def test_is_currently_active(self):
        self.assertTrue(self.alert.is_currently_active())

    def test_css_class(self):
        self.assertEqual(self.alert.css_class, 'alert-info')


class AlertViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )
        
        self.alert = Alert.objects.create(
            title='Test Alert',
            message='Test message',
            is_global=True,
            created_by='admin'
        )

    def test_dashboard_access_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('global_alerts:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_access_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('global_alerts:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_alert_list_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('global_alerts:alert_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Alert')

    def test_alert_create_view(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse('global_alerts:alert_create'), {
            'title': 'New Alert',
            'message': 'New message',
            'alert_type': 'general',
            'severity': 'info',
            'is_global': True,
            'is_dismissible': True,
            'show_on_all_pages': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Alert.objects.filter(title='New Alert').exists())

    def test_active_alerts_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('global_alerts:active_alerts'))
        self.assertEqual(response.status_code, 200)


class AlertUtilsTests(TestCase):
    def setUp(self):
        Alert.objects.create(
            title='Active Alert',
            message='Message',
            is_active=True,
            created_by='admin'
        )

    def test_get_active_alerts(self):
        alerts = get_active_alerts()
        self.assertEqual(alerts.count(), 1)

    def test_get_alert_statistics(self):
        stats = get_alert_statistics()
        self.assertEqual(stats['total_alerts'], 1)
        self.assertEqual(stats['active_alerts'], 1)
