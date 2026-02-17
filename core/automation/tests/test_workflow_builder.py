from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from automation.models import Workflow, WorkflowAction
import json

User = get_user_model()

class WorkflowBuilderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.url = reverse('automation:save_workflow')

    def test_save_workflow_with_builder_data(self):
        """Test saving a workflow with visual builder data."""
        
        # Mock Drawflow export data
        workflow_data = {
            "drawflow": {
                "Home": {
                    "data": {
                        "1": {
                            "id": 1,
                            "name": "trigger",
                            "data": {"event_type": "opportunity.won"},
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
                                "to": "client@example.com",
                                "subject": "Deal Won!",
                                "body": "Congratulations."
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
            "name": "Visual Workflow Test",
            "workflow_data": workflow_data
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Verify Workflow created
        workflow = Workflow.objects.get(id=response_data['workflow_id'])
        self.assertEqual(workflow.name, "Visual Workflow Test")
        self.assertEqual(workflow.trigger_type, "opportunity.won")
        self.assertEqual(workflow.builder_data, workflow_data)
        
        # Verify WorkflowAction created (backward compatibility)
        action = WorkflowAction.objects.get(workflow=workflow)
        self.assertEqual(action.action_type, "send_email")
        self.assertEqual(action.parameters['to'], "client@example.com")

    def test_save_workflow_missing_name(self):
        payload = {
            "workflow_data": {}
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
