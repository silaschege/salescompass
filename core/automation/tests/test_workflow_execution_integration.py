from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from automation.models import Workflow, WorkflowAction, WorkflowExecution
from automation.engine import WorkflowEngine
import json
from unittest.mock import patch

User = get_user_model()

class WorkflowExecutionIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        self.save_url = reverse('automation:save_workflow')

    @patch('automation.engine.WorkflowEngine.execute_action')
    def test_workflow_execution_from_builder_config(self, mock_execute_action):
        """
        Test that a workflow saved via the builder can be executed by the engine.
        """
        # 1. Simulate saving a workflow via the builder
        workflow_data = {
            "drawflow": {
                "Home": {
                    "data": {
                        "1": {
                            "id": 1,
                            "name": "trigger",
                            "data": {"event_type": "lead.created"},
                            "class": "trigger",
                            "html": "...",
                            "typenode": "vue",
                            "inputs": {},
                            "outputs": {"output_1": {"connections": [{"node": "2", "output": "input_1"}]}},
                            "pos_x": 100,
                            "pos_y": 100
                        },
                        "2": {
                            "id": 2,
                            "name": "send_email",
                            "data": {
                                "to": "test@example.com",
                                "subject": "Test Subject",
                                "body": "Test Body"
                            },
                            "class": "action",
                            "html": "...",
                            "typenode": "vue",
                            "inputs": {"input_1": {"connections": [{"node": "1", "input": "output_1"}]}},
                            "outputs": {},
                            "pos_x": 400,
                            "pos_y": 100
                        }
                    }
                }
            }
        }

        payload = {
            "name": "Integration Test Workflow",
            "workflow_data": workflow_data
        }

        response = self.client.post(
            self.save_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        workflow_id = response.json()['workflow_id']
        workflow = Workflow.objects.get(id=workflow_id)

        # Verify WorkflowActions were created (this is what the current engine uses)
        self.assertEqual(workflow.workflow_actions.count(), 1)
        action = workflow.workflow_actions.first()
        self.assertEqual(action.action_type, 'send_email')
        self.assertEqual(action.parameters['to'], 'test@example.com')

        # 2. Trigger the workflow via the engine
        engine = WorkflowEngine()
        event_type = 'lead.created'
        payload = {'id': 1, 'name': 'Test Lead'}
        event = {
            'event_type': event_type,
            'payload': payload,
            'tenant_id': self.user.tenant_id if hasattr(self.user, 'tenant_id') else None
        }
        
        # We need to ensure the workflow is active and matches the trigger
        self.assertTrue(workflow.is_active)
        self.assertEqual(workflow.trigger_type, event_type)

        # Evaluate triggers
        triggered_workflows = engine.evaluate_trigger(event)
        self.assertIn(workflow, triggered_workflows)

        # Execute workflow
        success = engine.execute_workflow(workflow.id, event)
        self.assertTrue(success)

        # 3. Verify execution
        # Check if execute_action was called
        mock_execute_action.assert_called()
        call_args = mock_execute_action.call_args
        self.assertEqual(call_args[0][0], action) # First arg is the action object
        self.assertEqual(call_args[0][1], event) # Second arg is the context

        # Check execution log
        execution = WorkflowExecution.objects.filter(workflow=workflow).first()
        self.assertIsNotNone(execution)
        self.assertEqual(execution.status, 'completed')
