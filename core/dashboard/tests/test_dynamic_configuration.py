from django.test import TestCase
from django.contrib.auth import get_user_model
from dashboard.model_introspection import get_available_models, get_model_fields
from dashboard.query_builder import build_queryset, apply_aggregation
from tasks.models import Task, TaskStatus
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class DynamicConfigurationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.status_todo = TaskStatus.objects.create(name='todo', label='To Do')
        self.status_done = TaskStatus.objects.create(name='completed', label='Completed', is_closed=True)
        
        # Create tasks
        Task.objects.create(title='Task 1', status_ref=self.status_todo, due_date=timezone.now(), assigned_to=self.user)
        Task.objects.create(title='Task 2', status_ref=self.status_todo, due_date=timezone.now(), assigned_to=self.user)
        Task.objects.create(title='Task 3', status_ref=self.status_done, due_date=timezone.now(), assigned_to=self.user)

    def test_model_introspection(self):
        """Test that models are correctly discovered."""
        models = get_available_models()
        self.assertTrue(any(m['id'] == 'tasks' for m in models))
        
        fields = get_model_fields('tasks')
        field_names = [f['name'] for f in fields]
        self.assertIn('title', field_names)
        self.assertIn('status_ref', field_names)
        self.assertIn('due_date', field_names)

    def test_query_builder_filtering(self):
        """Test queryset filtering."""
        # Filter by status = todo
        filters = [{
            'field': 'status_ref__name',
            'operator': 'exact',
            'value': 'todo'
        }]
        
        qs = build_queryset('tasks', filters=filters)
        self.assertEqual(qs.count(), 2)
        
        # Filter by status = completed
        filters = [{
            'field': 'status_ref__name',
            'operator': 'exact',
            'value': 'completed'
        }]
        
        qs = build_queryset('tasks', filters=filters)
        self.assertEqual(qs.count(), 1)

    def test_query_builder_aggregation(self):
        """Test aggregation."""
        qs = build_queryset('tasks')
        count = apply_aggregation(qs, 'count')
        self.assertEqual(count, 3)
