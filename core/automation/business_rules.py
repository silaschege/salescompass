import logging
import time
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from .models import AutomationRule

logger = logging.getLogger(__name__)

class BusinessRuleEngine:
    """
    Engine for evaluating and executing Business Rules (AutomationRule).
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def evaluate_rule(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """
        Evaluate if a rule's conditions are met.
        
        Args:
            rule: AutomationRule instance
            context: Dictionary containing 'payload' and other context data
            
        Returns:
            True if all conditions match, False otherwise
        """
        if not rule.automation_rule_is_active:
            return False

        conditions = rule.conditions
        if not conditions:
            return True # No conditions means always match

        payload = context.get('payload', {})

        try:
            # Handle list of conditions (AND logic by default)
            # Structure expected: [{'field': 'path', 'operator': 'eq', 'value': 'val'}, ...]
            if isinstance(conditions, list):
                for condition in conditions:
                    if not self._evaluate_single_condition(condition, payload):
                        return False
                return True
            
            # Handle dict structure if that's what is stored
            elif isinstance(conditions, dict):
                 for field_path, condition_config in conditions.items():
                    # Adapt dict structure to single condition check
                    # detailed config might be {'operator': 'eq', 'value': 'val'}
                    condition_data = condition_config.copy()
                    condition_data['field'] = field_path
                    if not self._evaluate_single_condition(condition_data, payload):
                        return False
                 return True

            return False

        except Exception as e:
            self.logger.error(f"Error evaluating rule {rule.id}: {e}")
            return False

    def _evaluate_single_condition(self, condition: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        """Evaluate a single condition dictionary."""
        field_path = condition.get('field')
        operator = condition.get('operator', 'eq')
        expected_value = condition.get('value')

        actual_value = self._get_nested_value(payload, field_path)

        return self._compare_values(actual_value, operator, expected_value)

    def execute_rule(self, rule: AutomationRule, context: Dict[str, Any]) -> bool:
        """
        Execute actions for a rule.
        """
        actions = rule.actions
        if not actions:
            return True

        success = True
        try:
            # Update execution stats
            rule.execution_count += 1
            rule.last_executed = timezone.now()
            start_time = time.time()

            for action_config in actions:
                # Expecting list of action dicts: [{'type': 'send_email', 'config': {...}}, ...]
                if not self._execute_single_action(action_config, context, rule):
                    success = False
                    # potentially break or continue based on error handling config
            
            execution_time = (time.time() - start_time) * 1000
            rule.average_execution_time_ms = (rule.average_execution_time_ms * (rule.execution_count - 1) + execution_time) / rule.execution_count
            
            if not success:
                rule.failure_count += 1
            
            rule.save(update_fields=['execution_count', 'last_executed', 'average_execution_time_ms', 'failure_count'])
            return success

        except Exception as e:
            self.logger.error(f"Error executing rule {rule.id}: {e}")
            rule.failure_count += 1
            rule.save(update_fields=['failure_count'])
            return False

    def _execute_single_action(self, action_config: Dict[str, Any], context: Dict[str, Any], rule: AutomationRule) -> bool:
        """Execute a single action."""
        action_type = action_config.get('type')
        config = action_config.get('config', {})
        payload = context.get('payload', {})
        tenant_id = context.get('tenant_id') or (rule.tenant_id if rule.tenant else None)

        try:
            if action_type == 'update_field':
                from django.apps import apps
                model_name = config.get('model')
                instance_id = config.get('instance_id') or payload.get('id')
                field_name = config.get('field_name')
                new_value = config.get('new_value')

                if model_name and instance_id and field_name:
                    model = apps.get_model(model_name)
                    instance = model.objects.get(pk=instance_id)
                    setattr(instance, field_name, new_value)
                    instance.save()
                    return True
            
            elif action_type == 'create_task':
                from tasks.models import Task
                from django.utils import timezone
                from datetime import timedelta
                
                due_date = config.get('due_date')
                if not due_date:
                    due_date = timezone.now() + timedelta(days=1)
                    
                Task.objects.create(
                    title=config.get('title', 'Automated Task'),
                    task_description=config.get('description', ''),
                    due_date=due_date,
                    tenant_id=tenant_id
                )
                return True

            # Add more action types as needed

            self.logger.warning(f"Unknown or Incomplete Action: {action_type}")
            return False

        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            return False

    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values helper."""
        try:
            if operator == 'eq':
                return str(actual) == str(expected)
            elif operator == 'ne':
                return str(actual) != str(expected)
            elif operator == 'gt':
                return float(actual) > float(expected)
            elif operator == 'lt':
                return float(actual) < float(expected)
            # ... (reuse logic or import from engine if possible, but simpler to incude basic types)
            elif operator == 'contains':
                return str(expected) in str(actual)
            
            return False
        except Exception:
            return False

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dict."""
        if not path:
            return None
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
    
    
    def _execute_single_action(self, action_config: Dict[str, Any], context: Dict[str, Any], rule: AutomationRule) -> bool:
        """Execute a single action dictionary."""
        action_type = action_config.get('type')
        config = action_config.get('config', {})
        
        try:
            if action_type == 'send_email':
                # Implementation for sending email
                pass
            elif action_type == 'create_task':
                # Implementation for creating task
                pass
            elif action_type == 'create_nba':
                from engagement.models import NextBestAction
                from django.utils import timezone
                from datetime import timedelta
                
                # Resolve dynamic values from context
                resolved_config = self._resolve_dynamic_values(config, context)
                
                # Set default values
                nba_params = {
                    'account_id': resolved_config.get('account_id'),
                    'action_type': resolved_config.get('action_type', 'check_in'),
                    'next_best_action_description': resolved_config.get('description', 'Auto-generated next best action'),
                    'due_date': timezone.now() + timedelta(days=resolved_config.get('due_in_days', 7)),
                    'priority': resolved_config.get('priority', 'medium'),
                    'assigned_to_id': resolved_config.get('assigned_to_id'),
                    'tenant_id': context.get('payload', {}).get('tenant_id'),
                    'source': f'Automation Rule: {rule.automation_rule_name}'
                }
                
                # Remove any None values
                nba_params = {k: v for k, v in nba_params.items() if v is not None}
                
                # Create the NBA
                NextBestAction.objects.create(**nba_params)
            # Add other action types...
            
            return True
        except Exception as e:
            self.logger.error(f"Error executing action {action_type}: {e}")
            return False

    def _resolve_dynamic_values(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve dynamic values in config from context.
        Example: "{{payload.account_id}}" -> actual account ID from payload
        """
        resolved = {}
        payload = context.get('payload', {})
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                # Extract path like "payload.account_id"
                path = value[2:-2].strip()
                resolved[key] = self._get_nested_value(payload, path)
            else:
                resolved[key] = value
                
        return resolved
# ... existing code ...
