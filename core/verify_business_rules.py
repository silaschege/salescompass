import os
import django
import sys
import logging

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from core.models import User
from tenants.models import Tenant
from automation.models import AutomationRule
from automation.business_rules import BusinessRuleEngine

def verify():
    print("Starting Business Rules Verification...")

    # 1. Setup Data
    try:
        tenant, _ = Tenant.objects.get_or_create(
            name="Verification Tenant", 
            defaults={'subdomain': 'verify-rules', 'slug': 'verify-rules'}
        )
        
        # Create a test rule
        # Rule: If amount > 1000, create a task
        conditions = [
            {'field': 'opportunity.amount', 'operator': 'gt', 'value': 1000}
        ]
        
        actions = [
            {
                'type': 'create_task',
                'config': {
                    'title': 'High Value Opportunity detected',
                    'description': 'Please follow up immediately.'
                }
            }
        ]
        
        rule, created = AutomationRule.objects.update_or_create(
            automation_rule_name="Test High Value Rule",
            tenant=tenant,
            defaults={
                'automation_rule_description': 'Test rule for verification',
                'trigger_type': 'event_based',
                'conditions': conditions,
                'actions': actions,
                'automation_rule_is_active': True
            }
        )
        
        print(f"Created rule: {rule.automation_rule_name}")
        
    except Exception as e:
        print(f"Error setting up data: {e}")
        return

    # 2. Test Evaluation (True Case)
    try:
        engine = BusinessRuleEngine()
        
        payload_pass = {
            'opportunity': {
                'amount': 5000,
                'name': 'Big Deal'
            }
        }
        
        context_pass = {'payload': payload_pass, 'tenant_id': tenant.id}
        
        print("\nTesting Evaluation (Should Pass)...")
        result = engine.evaluate_rule(rule, context_pass)
        
        if result:
            print("PASS: Rule evaluated to True as expected.")
        else:
            print("FAIL: Rule evaluated to False unexpectedly.")
            
    except Exception as e:
        print(f"Error testing evaluation (pass): {e}")

    # 3. Test Evaluation (False Case)
    try:
        payload_fail = {
            'opportunity': {
                'amount': 500,
                'name': 'Small Deal'
            }
        }
        
        context_fail = {'payload': payload_fail, 'tenant_id': tenant.id}
        
        print("\nTesting Evaluation (Should Fail)...")
        result = engine.evaluate_rule(rule, context_fail)
        
        if not result:
            print("PASS: Rule evaluated to False as expected.")
        else:
            print("FAIL: Rule evaluated to True unexpectedly.")
            
    except Exception as e:
        print(f"Error testing evaluation (fail): {e}")

    # 4. Test Execution
    try:
        print("\nTesting Execution...")
        
        # Count tasks before
        from tasks.models import Task
        initial_tasks = Task.objects.filter(tenant=tenant).count()
        
        success = engine.execute_rule(rule, context_pass)
        
        if success:
            final_tasks = Task.objects.filter(tenant=tenant).count()
            if final_tasks > initial_tasks:
                print("PASS: Rule executed successfully and Task was created.")
            else:
                 print("FAIL: Rule execution reported success but Task count did not increase.")
        else:
            print("FAIL: Rule execution failed.")
            
    except Exception as e:
         print(f"Error testing execution: {e}")

if __name__ == '__main__':
    verify()
