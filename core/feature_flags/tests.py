from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import FeatureFlag, FeatureTarget
from .utils import is_feature_enabled, calculate_adoption_rate

User = get_user_model()


class FeatureFlagModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        self.user.id = 50  # For consistent hashing
        self.user.save()
        
        self.flag = FeatureFlag.objects.create(
            key='test_feature',
            name='Test Feature',
            description='Test description',
            is_active=True,
            rollout_percentage=50,
            created_by='admin'
        )

    def test_feature_flag_enabled_100_percent(self):
        self.flag.rollout_percentage = 100
        self.flag.save()
        self.assertTrue(self.flag.is_enabled_for_user(self.user))

    def test_feature_flag_disabled_0_percent(self):
        self.flag.rollout_percentage = 0
        self.flag.save()
        self.assertFalse(self.flag.is_enabled_for_user(self.user))

    def test_feature_flag_inactive(self):
        self.flag.is_active = False
        self.flag.save()
        self.assertFalse(self.flag.is_enabled_for_user(self.user))


class FeatureFlagViewTests(TestCase):
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
        
        self.flag = FeatureFlag.objects.create(
            key='test_feature',
            name='Test Feature',
            is_active=True,
            rollout_percentage=100,
            created_by='admin'
        )

    def test_dashboard_access_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('feature_flags:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_access_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('feature_flags:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_flag_list_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('feature_flags:flag_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Feature')

    def test_flag_create_view(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse('feature_flags:flag_create'), {
            'key': 'new_feature',
            'name': 'New Feature',
            'description': 'New description',
            'is_active': False,
            'rollout_percentage': 0
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FeatureFlag.objects.filter(key='new_feature').exists())

    def test_flag_detail_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('feature_flags:flag_detail', args=[self.flag.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Feature')

    def test_flag_update_view(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse('feature_flags:flag_update', args=[self.flag.pk]), {
            'name': 'Updated Feature',
            'description': 'Updated description',
            'is_active': True,
            'rollout_percentage': 75
        })
        self.assertEqual(response.status_code, 302)
        flag = FeatureFlag.objects.get(pk=self.flag.pk)
        self.assertEqual(flag.name, 'Updated Feature')

    def test_active_flags_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('feature_flags:active_flags'))
        self.assertEqual(response.status_code, 200)

    def test_percentage_rollout_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('feature_flags:percentage_rollout'))
        self.assertEqual(response.status_code, 200)


class FeatureFlagUtilsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        self.flag = FeatureFlag.objects.create(
            key='test_feature',
            name='Test Feature',
            is_active=True,
            rollout_percentage=100,
            created_by='admin'
        )

    def test_is_feature_enabled(self):
        self.assertTrue(is_feature_enabled('test_feature', self.user))

    def test_is_feature_enabled_nonexistent(self):
        self.assertFalse(is_feature_enabled('nonexistent', self.user))

    def test_calculate_adoption_rate(self):
        adoption = calculate_adoption_rate(self.flag)
        self.assertEqual(adoption['rollout_percentage'], 100)
        self.assertEqual(adoption['is_active'], True)
