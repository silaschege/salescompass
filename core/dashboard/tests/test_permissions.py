from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from dashboard.models import DashboardWidget

User = get_user_model()

class WidgetPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create widgets
        self.public_widget = DashboardWidget.objects.create(
            widget_type='public_widget',
            name='Public Widget',
            is_active=True
        )
        
        self.restricted_widget = DashboardWidget.objects.create(
            widget_type='restricted_widget',
            name='Restricted Widget',
            required_permission='dashboard.view_restricted',
            is_active=True
        )
        
        # Create permission
        content_type = ContentType.objects.get_for_model(DashboardWidget)
        self.permission = Permission.objects.create(
            codename='view_restricted',
            name='Can view restricted widget',
            content_type=content_type,
        )

    def test_widget_filtering_without_permission(self):
        """Test that restricted widgets are hidden from users without permission."""
        user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(user)
        
        response = self.client.get('/dashboard/wizard/step1/')
        self.assertEqual(response.status_code, 200)
        
        available_modules = response.context['available_modules']
        
        # User should see public widget but not restricted widget
        self.assertTrue(any(w.widget_type == 'public_widget' for w in available_modules))
        self.assertFalse(any(w.widget_type == 'restricted_widget' for w in available_modules))
        
    def test_widget_filtering_with_permission(self):
        """Test that restricted widgets are shown to users with permission."""
        user = User.objects.create_user(username='permitteduser', password='password')
        user.user_permissions.add(self.permission)
        self.client.force_login(user)
        
        response = self.client.get('/dashboard/wizard/step1/')
        self.assertEqual(response.status_code, 200)
        
        available_modules = response.context['available_modules']
        
        # User should see both widgets
        self.assertTrue(any(w.widget_type == 'public_widget' for w in available_modules))
        self.assertTrue(any(w.widget_type == 'restricted_widget' for w in available_modules))
        
    def test_all_widgets_shown_when_no_permission_required(self):
        """Test that widgets without required_permission are visible to all users."""
        user = User.objects.create_user(username='basicuser', password='password')
        self.client.force_login(user)
        
        response = self.client.get('/dashboard/wizard/step1/')
        self.assertEqual(response.status_code, 200)
        
        available_modules = response.context['available_modules']
        
        # User should see the public widget
        self.assertTrue(any(w.widget_type == 'public_widget' for w in available_modules))
