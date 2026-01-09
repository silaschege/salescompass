
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add the project path to sys.path
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')

# Mock Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')

def test_sync_logic():
    print("Testing sync_workflow_from_builder_data logic...")
    
    # Mock models and data
    workflow = MagicMock()
    workflow.tenant_id = 1
    workflow.workflow_trigger_type = 'account.created'
    
    # Mock Drawflow JSON with a branch
    workflow.workflow_builder_data = {
        "drawflow": {
            "Home": {
                "data": {
                    "1": {
                        "id": 1,
                        "name": "trigger",
                        "data": {"event_type": "opportunity.won"},
                        "outputs": {"output_1": {"connections": [{"node": "2", "output": "input_1"}]}}
                    },
                    "2": {
                        "id": 2,
                        "name": "condition",
                        "data": {"field": "amount", "operator": "gt", "value": "1000"},
                        "outputs": {
                            "output_1": {"connections": [{"node": "3", "output": "input_1"}]}, # Yes
                            "output_2": {"connections": [{"node": "4", "output": "input_1"}]}  # No
                        },
                        "inputs": {"input_1": {"connections": [{"node": "1", "input": "output_1"}]}}
                    },
                    "3": {
                        "id": 3,
                        "name": "send_email",
                        "data": {"to": "high@value.com"},
                        "inputs": {"input_1": {"connections": [{"node": "2", "input": "output_1"}]}}
                    },
                    "4": {
                        "id": 4,
                        "name": "send_email",
                        "data": {"to": "low@value.com"},
                        "inputs": {"input_1": {"connections": [{"node": "2", "input": "output_2"}]}}
                    }
                }
            }
        }
    }

    # Patch the models to avoid DB calls during logic check
    with patch('automation.models.WorkflowTrigger.objects.create') as mock_trigger_create, \
         patch('automation.models.WorkflowAction.objects.create') as mock_action_create, \
         patch('automation.models.WorkflowBranch.objects.create') as mock_branch_create:
        
        from automation.utils import sync_workflow_from_builder_data
        
        # We need to return mock objects that have save() method
        def side_effect_create(*args, **kwargs):
            m = MagicMock()
            if 'workflow_action_type' in kwargs:
                m._type = 'action'
            elif 'branch_conditions' in kwargs:
                m._type = 'branch'
            else:
                m._type = 'trigger'
            return m
            
        mock_trigger_create.side_effect = side_effect_create
        mock_action_create.side_effect = side_effect_create
        mock_branch_create.side_effect = side_effect_create
        
        # Run sync (will clear related but let's mock that too)
        workflow.triggers.all().delete = MagicMock()
        workflow.workflow_actions.all().delete = MagicMock()
        workflow.workflow_branches.all().delete = MagicMock()
        
        sync_workflow_from_builder_data(workflow)
        
        print("Sync execution finished. Checking results...")
        
        # Check if objects were created
        print(f"Triggers created: {mock_trigger_create.call_count}")
        print(f"Actions created: {mock_action_create.call_count}")
        print(f"Branches created: {mock_branch_create.call_count}")
        
        # Verify hierarchy in one action
        # This is tricky because of the stateful nature of the sync function.
        # But we can at least see that create was called with correct parameters.
        
        assert mock_trigger_create.call_count == 1
        assert mock_branch_create.call_count == 1
        assert mock_action_create.call_count == 2
        
        print("Logic verification PASSED (basic counts)")

if __name__ == "__main__":
    test_sync_logic()
