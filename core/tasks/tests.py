from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
# Assuming workflows is in the same app, but if it's not found we might need to check where it is.
# Based on previous grep, tasks/utils.py might contain the logic, or tasks/workflows.py if it exists.
# The original code imported from salescompass.tasks.workflows.
# I'll try importing from .workflows first, if that fails I'll check file structure.
# Wait, I should check if workflows.py exists first.
# But for now I will assume it does or use a mock if I can't find it.
# Actually, let's check if workflows.py exists.
from tasks.models import Task

class TaskWorkflowTests(TestCase):
    def setUp(self):
        from core.models import User
        from tenants.models import TenantAwareModel as TenantModel
        # Create a dummy user and tenant context if needed
        # Since TenantModel is abstract or used as mixin, we usually need a tenant_id.
        self.user = User.objects.create(email='test@example.com', password='password')
        self.tenant_id = 'test_tenant'
        self.user.tenant_id = self.tenant_id
        self.user.save()

    def test_task_completion_without_account(self):
        """Test that task completion doesn't crash when no account is available."""
        task = Task.objects.create(
            title="Test Task",
            task_type="custom",  # No related objects required
            due_date=timezone.now() + timedelta(days=1),
            tenant_id=self.tenant_id,
            created_by=self.user
        )
        
        # Mark completed calls trigger_task_completion_workflows internally
        task.mark_completed(self.user)
        
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)
