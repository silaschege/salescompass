import json
from typing import Dict, Any
from django.db import transaction
from django.utils import timezone
from .models import Automation, AutomationExecutionLog, Workflow, WorkflowTrigger, WorkflowAction, WorkflowBranch
from .engine import execute_automation, execute_automations_sync
from .tasks import execute_automation_task
from django.conf import settings

def emit_event(trigger_type: str, payload: Dict[str, Any]) -> None:
    """
    Emit an event that can trigger automations.
    
    Usage:
        emit_event('account.created', {
            'account_id': account.id,
            'account_name': account.name,
            'industry': account.industry,
            'tenant_id': account.tenant_id,
        })
    """
  
    
    # Add timestamp to payload
    payload['event_timestamp'] = timezone.now().isoformat()
    payload['trigger_type'] = trigger_type
    
    # Execute automations synchronously or asynchronously
    if getattr(settings, 'AUTOMATION_ASYNC', False):
        # Use Celery for async execution
        execute_automation_task.delay(trigger_type, payload)
    else:
        # Execute synchronously
        execute_automations_sync(trigger_type, payload)



def get_available_triggers() -> list:
    """Get list of all available trigger types."""
    from core.plugin_registry import registry
    triggers = [trigger for trigger in registry.automation_triggers]
    return sorted(triggers)


def validate_trigger_payload(trigger_type: str, payload: Dict[str, Any]) -> bool:
    """Validate payload against expected schema for trigger type."""
    # Implementation can be extended with JSON schema validation
    required_fields = {
        'account.created': ['account_id', 'tenant_id'],
        'opportunity.stage_changed': ['opportunity_id', 'old_stage', 'new_stage', 'tenant_id'],
        'case.csat_submitted': ['case_id', 'csat_score', 'tenant_id'],
    }
    
    if trigger_type in required_fields:
        for field in required_fields[trigger_type]:
            if field not in payload:
                return False
    return True



def sync_workflow_from_builder_data(workflow: Workflow) -> None:
    """
    Synchronize WorkflowAction, WorkflowTrigger and WorkflowBranch models 
    from the workflow_builder_data (Drawflow JSON).
    """
    if not workflow.workflow_builder_data:
        return

    from django.db import transaction
    
    with transaction.atomic():
        # Clear existing related models to rebuild from JSON
        workflow.triggers.all().delete()
        workflow.workflow_actions.all().delete()
        workflow.workflow_branches.all().delete()

        drawflow = workflow.workflow_builder_data.get('drawflow', {})
        home = drawflow.get('Home', {})
        nodes = home.get('data', {})

        if not nodes:
            return

        # Map node IDs to created objects
        node_to_obj = {}
        
        # 1. Create Triggers
        for node_id, node in nodes.items():
            if node.get('name') == 'trigger':
                data = node.get('data', {})
                trigger = WorkflowTrigger.objects.create(
                    workflow=workflow,
                    workflow_trigger_event=data.get('event_type', workflow.workflow_trigger_type),
                    workflow_trigger_conditions=data.get('conditions', {}),
                    tenant_id=workflow.tenant_id
                )
                node_to_obj[node_id] = trigger

        # 2. Create Branches (Conditions)
        for node_id, node in nodes.items():
            if node.get('name') == 'condition':
                data = node.get('data', {})
                branch = WorkflowBranch.objects.create(
                    workflow=workflow,
                    branch_name=f"Condition {node_id}",
                    branch_conditions={
                        data.get('field', 'unknown'): {
                            'operator': data.get('operator', 'eq'),
                            'value': data.get('value', '')
                        }
                    },
                    tenant_id=workflow.tenant_id
                )
                node_to_obj[node_id] = branch

        # 3. Create Actions
        for node_id, node in nodes.items():
            name = node.get('name')
            if name not in ['trigger', 'condition', 'end']:
                data = node.get('data', {})
                
                # Resolve Action Type
                action_type = name
                if name == 'action':
                    action_type = data.get('action_type', 'unknown')
                
                # Resolve Parameters
                # Prefer 'config' if available (new UI), otherwise use whole data
                parameters = data.get('config', data)
                
                action = WorkflowAction.objects.create(
                    workflow=workflow,
                    workflow_action_type=action_type,
                    workflow_action_parameters=parameters,
                    tenant_id=workflow.tenant_id
                )
                node_to_obj[node_id] = action

        # 4. Set Hierarchy and Order (Parent/Branch relationships)
        # Traverse graph starting from triggers to assign orders and parent branches
        visited = set()
        queue = []
        
        # Initialize queue with triggers
        for node_id, node in nodes.items():
            if node.get('name') == 'trigger':
                queue.append((node_id, None, None, 0)) # (node_id, parent_branch, branch_val, order)
        
        while queue:
            node_id, parent_branch, branch_val, order = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            node = nodes.get(node_id)
            if not node:
                continue
                
            obj = node_to_obj.get(node_id)
            if obj:
                # Update object with hierarchy and order
                if isinstance(obj, WorkflowAction):
                    obj.branch = parent_branch
                    obj.branch_value = branch_val
                    obj.workflow_action_order = order
                    obj.save()
                elif isinstance(obj, WorkflowBranch):
                    obj.parent_branch = parent_branch
                    obj.parent_branch_value = branch_val
                    obj.branch_order = order
                    obj.save()
            
            # Follow connections
            outputs = node.get('outputs', {})
            for output_name, output_data in outputs.items():
                connections = output_data.get('connections', [])
                
                # If this node is a branch/condition, children will have a new parent branch
                new_parent = obj if isinstance(obj, WorkflowBranch) else parent_branch
                new_branch_val = (output_name == 'output_1') if isinstance(obj, WorkflowBranch) else branch_val
                
                # If we are staying in the same branch, increment order
                # If we are entering a new branch, reset order to 0
                new_order = 0 if isinstance(obj, WorkflowBranch) else order + 1
                
                for conn in connections:
                    queue.append((conn.get('node'), new_parent, new_branch_val, new_order))
