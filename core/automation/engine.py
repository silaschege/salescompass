import logging
import time
from typing import Any, Dict, List, Optional
from django.db import transaction
from .models import Automation, AutomationCondition, AutomationAction, AutomationExecutionLog

logger = logging.getLogger(__name__)

def evaluate_automation(automation: Automation, payload: Dict[str, Any]) -> bool:
    """
    Evaluate if an automation should execute based on its conditions.
    """
    if not automation.is_active:
        return False

    try:
        # Evaluate all conditions
        for condition in automation.conditions.filter(is_active=True):
            if not _evaluate_condition(condition, payload):
                return False
        return True
    except Exception as e:
        logger.error(f"Error evaluating conditions for automation {automation.id}: {e}")
        return False


def _evaluate_condition(condition: AutomationCondition, payload: Dict[str, Any]) -> bool:
    """Evaluate a single condition against the payload."""
    try:
        actual_value = _get_nested_value(payload, condition.field_path)
        expected_value = condition.value
        
        if condition.operator == 'eq':
            return actual_value == expected_value
        elif condition.operator == 'ne':
            return actual_value != expected_value
        elif condition.operator == 'gt':
            return float(actual_value) > float(expected_value)
        elif condition.operator == 'lt':
            return float(actual_value) < float(expected_value)
        elif condition.operator == 'gte':
            return float(actual_value) >= float(expected_value)
        elif condition.operator == 'lte':
            return float(actual_value) <= float(expected_value)
        elif condition.operator == 'in':
            return actual_value in expected_value
        elif condition.operator == 'contains':
            return expected_value in str(actual_value)
        elif condition.operator == 'regex':
            import re
            return bool(re.search(expected_value, str(actual_value)))
        else:
            return False
    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"Condition evaluation failed for {condition.id}: {e}")
        return False


def _get_nested_value(data: Dict, path: str) -> Any:
    """Get nested value from dict using dot notation."""
    keys = path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif hasattr(current, key):
            current = getattr(current, key)
        else:
            return None
    return current


def execute_action(action: AutomationAction, payload: Dict[str, Any], execution_log: AutomationExecutionLog) -> bool:
    """Execute a single action type."""
    try:
        config = action.config
        
        if action.action_type == 'send_email':
            from django.core.mail import send_mail
            send_mail(
                subject=config['subject'],
                message=config.get('body', ''),
                from_email=config.get('from_email', 'noreply@salescompass.com'),
                recipient_list=[config['to']] if isinstance(config['to'], str) else config['to']
            )
            
        elif action.action_type == 'create_task':
            from apps.tasks.models import Task
            Task.objects.create(
                title=config['title'],
                description=config.get('description', ''),
                due_date=config.get('due_date'),
                assigned_to_id=config.get('assigned_to_id'),
                tenant_id=execution_log.tenant_id
            )
            
        elif action.action_type == 'update_field':
            from django.apps import apps
            model_name = config['model']
            instance_id = config['instance_id']
            field_name = config['field_name']
            new_value = config['new_value']
            
            model = apps.get_model(*model_name.split('.'))
            instance = model.objects.get(id=instance_id)
            setattr(instance, field_name, new_value)
            instance.save()
            
        elif action.action_type == 'run_function':
            from importlib import import_module
            module_path, func_name = config['function'].rsplit('.', 1)
            module = import_module(module_path)
            func = getattr(module, func_name)
            func(**config.get('args', {}))
            
        elif action.action_type == 'create_case':
            from apps.cases.models import Case
            Case.objects.create(
                subject=config['subject'],
                description=config['description'],
                account_id=config['account_id'],
                priority=config.get('priority', 'medium'),
                tenant_id=execution_log.tenant_id
            )
            
        elif action.action_type == 'assign_owner':
            # Update owner field on specified model
            from django.apps import apps
            model = apps.get_model(*config['model'].split('.'))
            instance = model.objects.get(id=config['instance_id'])
            instance.owner_id = config['owner_id']
            instance.save()
            
        elif action.action_type == 'send_slack_message':
            import requests
            requests.post(
                config['webhook_url'],
                json={'text': config['message']}
            )
            
        elif action.action_type == 'webhook':
            import requests
            requests.post(
                config['url'],
                json=payload,
                headers=config.get('headers', {})
            )
            
        else:
            raise ValueError(f"Unknown action type: {action.action_type}")
            
        return True
        
    except Exception as e:
        execution_log.error_message = str(e)
        execution_log.status = 'failed'
        execution_log.save(update_fields=['error_message', 'status'])
        logger.error(f"Action execution failed for {action.id}: {e}")
        return False


def execute_automation(automation: Automation, payload: Dict[str, Any], user: Optional[Any] = None) -> bool:
    """Execute an automation with all its actions."""
    start_time = time.time()
    
    with transaction.atomic():
        # Create execution log
        execution_log = AutomationExecutionLog.objects.create(
            automation=automation,
            trigger_payload=payload,
            executed_by=user,
            tenant_id=getattr(user, 'tenant_id', None) or payload.get('tenant_id')
        )
        
        try:
            execution_log.status = 'conditions_evaluated'
            execution_log.save(update_fields=['status'])
            
            # Evaluate conditions
            if not evaluate_automation(automation, payload):
                execution_log.status = 'skipped'
                execution_log.save(update_fields=['status'])
                return False
            
            execution_log.status = 'executing'
            execution_log.save(update_fields=['status'])
            
            # Execute all actions
            for action in automation.actions.filter(is_active=True).order_by('order'):
                if not execute_action(action, payload, execution_log):
                    return False
            
            execution_log.status = 'completed'
            execution_time = int((time.time() - start_time) * 1000)
            execution_log.execution_time_ms = execution_time
            execution_log.save(update_fields=['status', 'execution_time_ms'])
            
            return True
            
        except Exception as e:
            execution_log.status = 'failed'
            execution_log.error_message = str(e)
            execution_log.save(update_fields=['status', 'error_message'])
            return False
        

def execute_automations_sync(trigger_type: str, payload: Dict[str, Any]) -> None:
    """Execute automations synchronously."""
    from .models import Automation
    automations = Automation.objects.filter(
        trigger_type=trigger_type,
        is_active=True
    ).select_related('created_by').prefetch_related('conditions', 'actions')
    
    for automation in automations:
        execute_automation(automation, payload)


# Workflow Engine for new Workflow models

class WorkflowEngine:
    """
    Workflow execution engine for the new Workflow models.
    Handles trigger evaluation, workflow execution, and action processing.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def evaluate_trigger(self, event: Dict[str, Any]) -> List['Workflow']:
        """
        Evaluate which workflows should be triggered by an event.
        
        Args:
            event: Dictionary with 'event_type', 'payload', and 'tenant_id'
        
        Returns:
            List of Workflow instances that should execute
        """
        from .models import Workflow, WorkflowTrigger
        
        event_type = event.get('event_type')
        payload = event.get('payload', {})
        tenant_id = event.get('tenant_id')
        
        if not event_type:
            self.logger.warning("No event_type provided to evaluate_trigger")
            return []
        
        try:
            # Find workflows matching the trigger type
            workflows = Workflow.objects.filter(
                trigger_type=event_type,
                is_active=True,
                tenant_id=tenant_id
            ).prefetch_related('triggers', 'workflow_actions')
            
            triggered_workflows = []
            
            for workflow in workflows:
                # Check if any active triggers match
                for trigger in workflow.triggers.filter(is_active=True):
                    if self._evaluate_trigger_conditions(trigger, payload):
                        triggered_workflows.append(workflow)
                        break  # Only need one matching trigger
            
            return triggered_workflows
            
        except Exception as e:
            self.logger.error(f"Error evaluating triggers: {e}")
            return []
    
    def _evaluate_trigger_conditions(self, trigger: 'WorkflowTrigger', payload: Dict[str, Any]) -> bool:
        """
        Evaluate if a trigger's conditions are met.
        
        Args:
            trigger: WorkflowTrigger instance
            payload: Event payload data
        
        Returns:
            True if all conditions are met
        """
        conditions = trigger.conditions
        
        if not conditions:
            return True  # No conditions means always match
        
        try:
            # Evaluate each condition in the trigger
            for field_path, condition_config in conditions.items():
                operator = condition_config.get('operator', 'eq')
                expected_value = condition_config.get('value')
                
                actual_value = _get_nested_value(payload, field_path)
                
                if not self._compare_values(actual_value, operator, expected_value):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Trigger condition evaluation failed: {e}")
            return False
    
    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values using specified operator."""
        try:
            if operator == 'eq':
                return actual == expected
            elif operator == 'ne':
                return actual != expected
            elif operator == 'gt':
                return float(actual) > float(expected)
            elif operator == 'lt':
                return float(actual) < float(expected)
            elif operator == 'gte':
                return float(actual) >= float(expected)
            elif operator == 'lte':
                return float(actual) <= float(expected)
            elif operator == 'in':
                return actual in expected
            elif operator == 'contains':
                return expected in str(actual)
            elif operator == 'regex':
                import re
                return bool(re.search(expected, str(actual)))
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def execute_workflow(self, workflow_id: int, context: Dict[str, Any]) -> bool:
        """
        Execute a workflow with the given context.
        
        Args:
            workflow_id: ID of the workflow to execute
            context: Execution context with payload and metadata
        
        Returns:
            True if execution succeeded, False otherwise
        """
        from .models import Workflow, WorkflowExecution
        from django.utils import timezone
        
        start_time = time.time()
        
        try:
            workflow = Workflow.objects.prefetch_related('workflow_actions').get(
                id=workflow_id,
                is_active=True
            )
        except Workflow.DoesNotExist:
            self.logger.error(f"Workflow {workflow_id} not found or inactive")
            return False
        
        with transaction.atomic():
            # Create execution log
            execution = WorkflowExecution.objects.create(
                workflow=workflow,
                trigger_payload=context.get('payload', {}),
                status='running',
                tenant_id=workflow.tenant_id
            )
            
            try:
                # Execute all active actions in order
                actions = workflow.workflow_actions.filter(is_active=True).order_by('order')
                
                for action in actions:
                    if not self.execute_action(action, context):
                        # Action failed
                        execution.status = 'failed'
                        execution.error_message = f"Action {action.action_type} failed"
                        execution.completed_at = timezone.now()
                        execution.execution_time_ms = int((time.time() - start_time) * 1000)
                        execution.save()
                        return False
                
                # All actions succeeded
                execution.status = 'completed'
                execution.completed_at = timezone.now()
                execution.execution_time_ms = int((time.time() - start_time) * 1000)
                execution.save()
                
                self.logger.info(f"Workflow {workflow_id} completed successfully")
                return True
                
            except Exception as e:
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.completed_at = timezone.now()
                execution.execution_time_ms = int((time.time() - start_time) * 1000)
                execution.save()
                
                self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
                return False
    
    def execute_action(self, action: 'WorkflowAction', context: Dict[str, Any]) -> bool:
        """
        Execute a single workflow action.
        
        Args:
            action: WorkflowAction instance to execute
            context: Execution context with payload and metadata
        
        Returns:
            True if action succeeded, False otherwise
        """
        try:
            parameters = action.parameters
            payload = context.get('payload', {})
            tenant_id = context.get('tenant_id') or action.tenant_id
            
            if action.action_type == 'send_email':
                from django.core.mail import send_mail
                send_mail(
                    subject=parameters.get('subject', 'Notification'),
                    message=parameters.get('body', ''),
                    from_email=parameters.get('from_email', 'noreply@salescompass.com'),
                    recipient_list=[parameters['to']] if isinstance(parameters['to'], str) else parameters['to']
                )
                
            elif action.action_type == 'create_task':
                from tasks.models import Task
                Task.objects.create(
                    title=parameters['title'],
                    description=parameters.get('description', ''),
                    due_date=parameters.get('due_date'),
                    assigned_to_id=parameters.get('assigned_to_id'),
                    tenant_id=tenant_id
                )
                
            elif action.action_type == 'update_field':
                from django.apps import apps
                model = apps.get_model(parameters['model'])
                instance = model.objects.get(id=parameters['instance_id'])
                setattr(instance, parameters['field_name'], parameters['new_value'])
                instance.save()
                
            elif action.action_type == 'run_function':
                from importlib import import_module
                module_path, func_name = parameters['function'].rsplit('.', 1)
                module = import_module(module_path)
                func = getattr(module, func_name)
                func(**parameters.get('args', {}))
                
            elif action.action_type == 'create_case':
                from cases.models import Case
                Case.objects.create(
                    subject=parameters['subject'],
                    description=parameters.get('description', ''),
                    account_id=parameters.get('account_id'),
                    priority=parameters.get('priority', 'medium'),
                    tenant_id=tenant_id
                )
                
            elif action.action_type == 'assign_owner':
                from django.apps import apps
                model = apps.get_model(parameters['model'])
                instance = model.objects.get(id=parameters['instance_id'])
                instance.owner_id = parameters['owner_id']
                instance.save()
                
            elif action.action_type == 'send_slack_message':
                import requests
                requests.post(
                    parameters['webhook_url'],
                    json={'text': parameters['message']},
                    timeout=10
                )
                
            elif action.action_type == 'webhook':
                import requests
                requests.post(
                    parameters['url'],
                    json=payload,
                    headers=parameters.get('headers', {}),
                    timeout=10
                )
                
            else:
                self.logger.warning(f"Unknown action type: {action.action_type}")
                return False
            
            self.logger.info(f"Action {action.action_type} executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Action {action.id} execution failed: {e}")
            return False