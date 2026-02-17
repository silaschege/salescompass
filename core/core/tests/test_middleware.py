from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from core.middleware import ThreadLocalUserMiddleware, get_current_user

User = get_user_model()

class MiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='middleware_test', email='mw@test.com', password='pw')
        self.middleware = ThreadLocalUserMiddleware(lambda x: x)

    def test_current_user_storage(self):
        """Test that middleware stores user in thread locals."""
        request = self.factory.get('/')
        request.user = self.user
        
        # Process request
        self.middleware.process_request(request)
        
        # Check if user is available
        self.assertEqual(get_current_user(), self.user)
        
        # Process response (should clear user)
        self.middleware.process_response(request, None)
        
        # Check if user is cleared (or at least not the same, depending on implementation details of thread locals cleanup)
        # Our implementation deletes it, so getattr returns None
        self.assertIsNone(get_current_user())


class DataVisibilityMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        from core.middleware import DataVisibilityMiddleware
        from core.models import Role
        
        self.role_team = Role.objects.create(
            name="Team Visibility",
            permissions=[],
            data_visibility_rules={'lead': 'team_only', 'account': 'own_only'}
        )
        self.user = User.objects.create_user(
            username='vis_test',
            email='vis@test.com',
            password='pw',
            role=self.role_team
        )
        self.middleware = DataVisibilityMiddleware(lambda x: x)

    def test_visibility_context_injection(self):
        """Test that middleware injects visibility_context into user."""
        request = self.factory.get('/')
        request.user = self.user
        
        # Process request
        self.middleware.process_request(request)
        
        # Check if visibility_context is set
        self.assertTrue(hasattr(request.user, 'visibility_context'))
        self.assertEqual(request.user.visibility_context['lead'], 'team_only')
        self.assertEqual(request.user.visibility_context['account'], 'own_only')

    def test_superuser_visibility_context(self):
        """Test that superuser gets 'all' visibility."""
        superuser = User.objects.create_superuser(
            username='super',
            email='super@test.com',
            password='pw'
        )
        request = self.factory.get('/')
        request.user = superuser
        
        self.middleware.process_request(request)
        
        self.assertTrue(hasattr(request.user, 'visibility_context'))
        self.assertEqual(request.user.visibility_context['default'], 'all')

    def test_no_role_default_visibility(self):
        """Test that user without role gets default 'own_only'."""
        user_no_role = User.objects.create_user(
            username='norole',
            email='norole@test.com',
            password='pw'
        )
        request = self.factory.get('/')
        request.user = user_no_role
        
        self.middleware.process_request(request)
        
        self.assertTrue(hasattr(request.user, 'visibility_context'))
        self.assertEqual(request.user.visibility_context['default'], 'own_only')

