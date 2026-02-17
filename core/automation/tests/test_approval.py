
import os
import django
import sys

# Set up Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from automation.models import Workflow, WorkflowAction, WorkflowExecution, WorkflowApproval
from automation.engine import WorkflowEngine
from django.contrib.auth import get_user_model
from tenants.models import Tenant

User = get_user_model()

def test_approval_workflow():
    print("Testing Approval Workflow...")
    
    # Ensure a tenant and user exist
    tenant, _ = Tenant.objects.get_or_create(name="Test Tenant", domain="test")
    user, _ = User.objects.get_or_create(username="testuser", email="test@example.com", tenant_id=tenant.id)
    tenant_id = tenant.id
    
    # 1. Create a workflow with an approval step
    workflow = Workflow.objects.create(
        workflow_name="Approval Test Workflow",
        workflow_trigger_type="test_event",
        workflow_is_active=True,
        tenant_id=tenant_id
    )
    
    # Step 1: Normal action
    action1 = WorkflowAction.objects.create(
        workflow=workflow,
        workflow_action_name="Action 1",
        action_type="send_email",
        parameters={"to": "test@example.com", "subject": "Hello", "body": "Step 1"},
        workflow_action_order=1,
        tenant_id=tenant_id
    )
    
    # Step 2: Approval action
    action2 = WorkflowAction.objects.create(
        workflow=workflow,
        workflow_action_name="Approval Required",
        action_type="approval",
        parameters={},
        workflow_action_order=2,
        tenant_id=tenant_id
    )
    
    # Step 3: Action after approval
    action3 = WorkflowAction.objects.create(
        workflow=workflow,
        workflow_action_name="Action 2",
        action_type="send_email",
        parameters={"to": "test@example.com", "subject": "Hello", "body": "Step 3 (Post Approval)"},
        workflow_action_order=3,
        tenant_id=tenant_id
    )
    
    engine = WorkflowEngine()
    context = {"payload": {"test": "data"}, "tenant_id": tenant_id}
    
    print("Starting workflow...")
    success = engine.execute_workflow(workflow.id, context)
    
    # Check if paused
    execution = WorkflowExecution.objects.filter(workflow=workflow).last()
    print(f"Workflow status: {execution.workflow_execution_status}")
    
    approval = WorkflowApproval.objects.filter(workflow_execution=execution).last()
    if approval and execution.workflow_execution_status == 'waiting_for_approval':
        print("Workflow successfully paused for approval.")
    else:
        print("FAILED: Workflow did not pause for approval.")
        return

    # 2. Approve and Resume
    print("Approving and resuming...")
    approval.approval_status = 'approved'
    approval.save()
    
    resumed_success = engine.resume_workflow(execution.id)
    
    execution.refresh_from_db()
    print(f"Resumed workflow status: {execution.workflow_execution_status}")
    
    if execution.workflow_execution_status == 'completed':
        print("Workflow successfully completed after approval!")
    else:
        print(f"FAILED: Workflow status is {execution.workflow_execution_status}")

if __name__ == "__main__":
    test_approval_workflow()
