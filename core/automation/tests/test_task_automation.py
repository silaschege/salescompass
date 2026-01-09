from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from automation.models import Workflow, WorkflowAction, WorkflowExecution
from automation.engine import WorkflowEngine
from tasks.models import Task
from leads.models import Lead, LeadSource
from tenants.models import Tenant

User = get_user_model()

class AutomaticTaskCreationTests(TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()
        
        # Setup Tenant and User
        self.tenant = Tenant.objects.create(name='Test Tenant', slug='test-tenant')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
        self.admin = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            tenant=self.tenant
        )

        # Setup Lead Source (required for Lead)
        self.source = LeadSource.objects.create(
            source_name='Website',
            tenant=self.tenant
        )
        
        # Setup Context Object (Lead)
        self.lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            owner=self.user,
            lead_score=50,
            source_ref=self.source,
            tenant=self.tenant
        )

        self.workflow = Workflow.objects.create(
            name='Test Task Automation',
            trigger_type='lead.update',
            is_active=True,
            tenant=self.tenant,
            created_by=self.user
        )

    def test_resolve_context_object(self):
        """Test resolving object from payload."""
        payload = {'lead_id': self.lead.id}
        obj = self.engine._resolve_context_object(payload)
        self.assertEqual(obj, self.lead)

        payload_invalid = {'lead_id': 99999}
        obj_invalid = self.engine._resolve_context_object(payload_invalid)
        self.assertIsNone(obj_invalid)

    def test_calculate_due_date(self):
        """Test relative due date calculation."""
        # 2 days relative
        rule_days = {'type': 'relative', 'value': 2, 'unit': 'days'}
        date = self.engine._calculate_due_date(rule_days)
        expected = timezone.now() + timedelta(days=2)
        # Check delta is small (execution time)
        self.assertTrue(abs((date - expected).total_seconds()) < 5)

        # 3 hours relative
        rule_hours = {'type': 'relative', 'value': 3, 'unit': 'hours'}
        date_hours = self.engine._calculate_due_date(rule_hours)
        expected_hours = timezone.now() + timedelta(hours=3)
        self.assertTrue(abs((date_hours - expected_hours).total_seconds()) < 5)

    def test_resolve_assignee(self):
        """Test assignee resolution."""
        # Owner rule
        rule_owner = {'type': 'owner', 'fallback_user_id': self.admin.id}
        assignee_id = self.engine._resolve_assignee(rule_owner, self.lead, self.tenant.id)
        self.assertEqual(assignee_id, self.user.id)

        # Explicit user rule
        rule_user = {'type': 'user', 'value': self.admin.id}
        assignee_id_user = self.engine._resolve_assignee(rule_user, self.lead, self.tenant.id)
        self.assertEqual(assignee_id_user, self.admin.id)
        
        # Fallback (context object has no owner or is None)
        rule_fallback = {'type': 'owner', 'fallback_user_id': self.admin.id}
        assignee_id_fallback = self.engine._resolve_assignee(rule_fallback, None, self.tenant.id)
        self.assertEqual(assignee_id_fallback, self.admin.id)

    def test_create_task_action_full_flow(self):
        """Test full task creation via execute_action."""
        action = WorkflowAction.objects.create(
            workflow=self.workflow,
            action_type='create_task',
            parameters={
                'title': 'Call {{ object.first_name }}',
                'description': 'Score is {{ object.lead_score }}',
                'due_date_rule': {'type': 'relative', 'value': 1, 'unit': 'days'},
                'assignee_rule': {'type': 'owner', 'fallback_user_id': self.admin.id}
            },
            tenant=self.tenant
        )

        context = {
            'payload': {'lead_id': self.lead.id},
            'tenant_id': self.tenant.id
        }
        
        # Create execution log (required by execute_action signature in some versions, 
        # but execute_action in engine.py uses execution_log argument?
        # Checking engine.py: execute_action(self, action, context, execution=None)
        # It seems it doesn't strictly require execution log for create_task,
        # but let's see if we need it. engine.py implementation:
        # tenant_id = context.get('tenant_id') or action.tenant_id
        # ... logic ...
        # So execution is optional.
        
        success = self.engine.execute_action(action, context)
        self.assertTrue(success)

        # Verify Task Created
        task = Task.objects.filter(title='Call John').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.description, 'Score is 50')
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.related_object, self.lead) 
        # Check due date is approx 1 day from now
        expected_due = timezone.now() + timedelta(days=1)
        if task.due_date:
             # task.due_date might be date or datetime depending on model
             # Assuming datetime based on engine logic
             self.assertTrue(abs((task.due_date - expected_due).total_seconds()) < 60)
