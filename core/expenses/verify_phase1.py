import os
import django
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

import sys
sys.path.append(os.path.join(os.getcwd(), 'core'))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from expenses.models import (
    ExpenseCategory, ExpenseReport, ExpenseLine, 
    ExpenseApprovalWorkflow, ExpenseApprovalStep, ExpensePolicy
)
from expenses.services import ApprovalService, PolicyService, ExpenseAccountingService
from tenants.models import Tenant

User = get_user_model()

def run_verification():
    print("Starting Expenses Phase 1 Verification...")
    
    # Setup Data
    # Ensure we have a tenant
    tenant = Tenant.objects.first()
    if not tenant:
        print("No tenant found. Creating 'Test Tenant'...")
        tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant", domain_url="test.local")
    
    user = User.objects.first()
    if not user:
        print("No user found. Creating 'admin'...")
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        
    if not user.tenant:
        print(f"User {user.username} has no tenant. Assigning {tenant.name}...")
        user.tenant = tenant
        user.save()
        
    print(f"Using User: {user.username}, Tenant: {tenant}")

    # 1. Setup Approval Workflow
    print("\n1. Setting up Approval Workflow...")
    workflow, created = ExpenseApprovalWorkflow.objects.get_or_create(
        tenant=tenant, 
        name="Standard Corporate Workflow",
        defaults={'is_active': True}
    )
    
    step1, _ = ExpenseApprovalStep.objects.get_or_create(
        workflow=workflow,
        step_order=1,
        tenant=tenant,
        defaults={'name': 'Manager Approval', 'min_amount': Decimal('0')}
    )
    
    step2, _ = ExpenseApprovalStep.objects.get_or_create(
        workflow=workflow,
        step_order=2,
        tenant=tenant,
        defaults={'name': 'Finance Review', 'min_amount': Decimal('1000')}
    )
    print("Workflow created with 2 steps.")

    # 2. Setup Policy
    print("\n2. Setting up Expense Policy...")
    category, _ = ExpenseCategory.objects.get_or_create(
        tenant=tenant, 
        name="Meals",
        defaults={'gl_account': None} # Mock GL for now
    )
    
    policy, _ = ExpensePolicy.objects.get_or_create(
        tenant=tenant,
        category=category,
        defaults={
            'name': 'Meal Limit',
            'max_amount_per_transaction': Decimal('5000'),
            'action_on_violation': 'block'
        }
    )
    # Ensure strict enforcement for test
    policy.max_amount_per_transaction = Decimal('5000')
    policy.action_on_violation = 'block'
    policy.save()
    print("Policy 'Meal Limit' set to 5000 (Block).")

    # 3. Test Policy Blocking
    print("\n3. Testing Policy Blocking...")
    report = ExpenseReport.objects.create(
        tenant=tenant,
        employee=user,
        report_number=f"TEST-{timezone.now().strftime('%H%M%S')}",
        title="Excessive Meal"
    )
    
    line = ExpenseLine.objects.create(
        tenant=tenant,
        report=report,
        category=category,
        date=timezone.now().date(),
        description="Fancy Dinner",
        amount=Decimal('6000') # Exceeds 5000
    )
    
    violations = PolicyService.validate_line(line)
    print(f"Violations found: {violations}")
    
    is_blocked, warnings = PolicyService.check_report_policies(report)
    if is_blocked:
        print("SUCCESS: Report submission blocked as expected.")
    else:
        print("FAILURE: Report submission NOT blocked.")

    # 4. Test Approval Workflow
    print("\n4. Testing Approval Workflow...")
    # Fix the amount to be compliant
    line.amount = Decimal('2000') # Compliant, triggering Step 1 & 2 (> 1000)
    line.save()
    
    # Submit
    report = ApprovalService.submit_report(report, user)
    print(f"Report Status after Submit: {report.status}")
    print(f"Current Step: {report.current_step}")
    
    if report.status == 'pending_approval' and report.current_step == step1:
        print("SUCCESS: Report moved to Step 1.")
    else:
        print(f"FAILURE: Expected Step 1, got {report.current_step}")

    # Approve Step 1
    ApprovalService.approve_step(report, user)
    print(f"Report Status after Step 1 Approval: {report.status}")
    print(f"Current Step: {report.current_step}")
    
    if report.current_step == step2:
         print("SUCCESS: Report moved to Step 2.")
    else:
         print(f"FAILURE: Expected Step 2, got {report.current_step}")
         
    # Approve Step 2 (Final)
    ApprovalService.approve_step(report, user)
    print(f"Report Status after Step 2 Approval: {report.status}")
    
    if report.status == 'approved':
        print("SUCCESS: Report fully approved.")
    else:
        print("FAILURE: Report not approved.")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"ERROR: {e}")
