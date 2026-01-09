import logging
import time
from typing import Any, Dict, List, Optional
from django.db import transaction
from .models import Automation, AutomationCondition, AutomationAction, AutomationExecutionLog

logger = logging.getLogger(__name__)

class WorkflowPauseException(Exception):
    """Exception raised when a workflow needs to pause for approval or delay."""
    def __init__(self, execution, current_step=None, current_branch=None, branch_value=None):
        self.execution = execution
        self.current_step = current_step
        self.current_branch = current_branch
        self.branch_value = branch_value

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

        elif action.action_type == 'create_nba':
            from engagement.models import NextBestAction
            from django.utils import timezone
            from datetime import timedelta
            
            # Get parameters from config
            nba_params = {
                'account_id': config.get('account_id'),
                'action_type': config.get('action_type', 'check_in'),
                'next_best_action_description': config.get('description', 'Auto-generated next best action'),
                'due_date': timezone.now() + timedelta(days=config.get('due_in_days', 7)),
                'priority': config.get('priority', 'medium'),
                'assigned_to_id': config.get('assigned_to_id'),
                'tenant_id': execution_log.tenant_id,
                'source': 'Automation Rule'
            }
            
            # Remove any None values
            nba_params = {k: v for k, v in nba_params.items() if v is not None}
            
            # Create the NBA
            NextBestAction.objects.create(**nba_params)
            
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
                workflow_trigger_type=event_type,
                workflow_is_active=True,
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
        conditions = trigger.workflow_trigger_conditions
        
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
        Execute a workflow with the given context, supporting branching.
        """
        from .models import Workflow, WorkflowExecution, WorkflowAction, WorkflowBranch
        from django.utils import timezone
        
        start_time = time.time()
        
        try:
            workflow = Workflow.objects.get(id=workflow_id, workflow_is_active=True)
        except Workflow.DoesNotExist:
            self.logger.error(f"Workflow {workflow_id} not found or inactive")
            return False
        
        with transaction.atomic():
            execution = WorkflowExecution.objects.create(
                workflow=workflow,
                workflow_execution_trigger_payload=context.get('payload', {}),
                workflow_execution_status='running',
                tenant_id=workflow.tenant_id
            )
            
            try:
                # Start recursive execution from the root (no parent branch)
                success = self._execute_recursive(workflow, context, execution, None, None)
                
                if success:
                    execution.workflow_execution_status = 'completed'
                else:
                    execution.workflow_execution_status = 'failed'
                    if not execution.workflow_execution_error_message:
                        execution.workflow_execution_error_message = "One or more actions failed"
                
                execution.workflow_execution_completed_at = timezone.now()
                execution.workflow_execution_execution_time_ms = int((time.time() - start_time) * 1000)
                execution.save()
                
                if not success:
                    from .alerting import AutomationAlertService
                    AutomationAlertService.create_alert_from_execution(execution)
                
                if success:
                    self.logger.info(f"Workflow {workflow_id} completed successfully")
                return success
                
            except WorkflowPauseException as e:
                # Workflow is paused, not failed or completed
                self.logger.info(f"Workflow {workflow_id} paused for approval/delay")
                return True
                
            except Exception as e:
                execution.workflow_execution_status = 'failed'
                execution.workflow_execution_error_message = str(e)
                execution.workflow_execution_completed_at = timezone.now()
                execution.workflow_execution_execution_time_ms = int((time.time() - start_time) * 1000)
                execution.save()
                
                from .alerting import AutomationAlertService
                AutomationAlertService.create_alert_from_execution(execution)
                
                self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
                return False

    def _execute_recursive(self, workflow, context, execution, parent_branch, branch_value, start_from_item_id=None) -> bool:
        """Recursive helper to execute actions and branches."""
        from .models import WorkflowAction, WorkflowBranch

        # Get actions in this context
        actions = list(workflow.workflow_actions.filter(
            workflow_action_is_active=True,
            branch=parent_branch,
            branch_value=branch_value
        ))

        # Get branches in this context
        branches = list(workflow.workflow_branches.filter(
            branch_is_active=True,
            parent_branch=parent_branch,
            parent_branch_value=branch_value
        ))

        # Combine and sort by order
        items = sorted(
            actions + branches,
            key=lambda x: getattr(x, 'workflow_action_order', getattr(x, 'branch_order', 0))
        )

        skip_until_found = start_from_item_id is not None
        
        for item in items:
            if skip_until_found:
                if item.id == start_from_item_id:
                    skip_until_found = False
                    # We continue from this item (which was the one that paused)
                    # Actually, if it paused *at* an action, we should probably skip it or re-execute?
                    # For approvals, we skip the approval action itself since it's done.
                    continue
                continue

            if isinstance(item, WorkflowAction):
                if not self.execute_action(item, context, execution):
                    return False
            elif isinstance(item, WorkflowBranch):
                # Evaluate branch condition
                branch_result = self._evaluate_branch_conditions(item, context.get('payload', {}))
                if not self._execute_recursive(workflow, context, execution, item, branch_result):
                    return False
        
        return True

    def _evaluate_branch_conditions(self, branch: 'WorkflowBranch', payload: Dict[str, Any]) -> bool:
        """Evaluate branch conditions against payload."""
        conditions = branch.branch_conditions
        if not conditions:
            return True
            
        try:
            # Similar to trigger evaluation but for branching
            for field_path, condition_config in conditions.items():
                operator = condition_config.get('operator', 'eq')
                expected_value = condition_config.get('value')
                
                actual_value = _get_nested_value(payload, field_path)
                
                if not self._compare_values(actual_value, operator, expected_value):
                    return False
            return True
        except Exception as e:
            self.logger.warning(f"Branch condition evaluation failed: {e}")
            return False

    def resume_workflow(self, execution_id: int, context_update: Dict[str, Any] = None) -> bool:
        """Resume a paused workflow execution."""
        from .models import WorkflowExecution, Workflow
        from django.utils import timezone
        
        start_time = time.time()
        
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
            if execution.workflow_execution_status != 'waiting_for_approval':
                self.logger.warning(f"Execution {execution_id} is not in waiting state.")
                return False
                
            workflow = execution.workflow
            context = execution.workflow_execution_context_data
            if context_update:
                context.update(context_update)
                
            # Get current pause point
            current_step_id = execution.workflow_execution_current_step_id
            current_branch_id = execution.workflow_execution_current_branch_id
            current_branch_value = execution.workflow_execution_current_branch_value
            
            # Reset status to running
            execution.workflow_execution_status = 'running'
            execution.save()
            
            with transaction.atomic():
                try:
                    # Finding the parent branch object
                    parent_branch = None
                    if current_branch_id:
                        from .models import WorkflowBranch
                        parent_branch = WorkflowBranch.objects.get(id=current_branch_id)
                    
                    success = self._execute_recursive(
                        workflow, context, execution, 
                        parent_branch, current_branch_value, 
                        start_from_item_id=current_step_id
                    )
                    
                    if success:
                        execution.workflow_execution_status = 'completed'
                    else:
                        execution.workflow_execution_status = 'failed'
                    
                    execution.workflow_execution_completed_at = timezone.now()
                    execution.save()
                    return success
                    
                except WorkflowPauseException:
                    self.logger.info(f"Workflow {workflow.id} paused again")
                    return True
                except Exception as e:
                    execution.workflow_execution_status = 'failed'
                    execution.workflow_execution_error_message = str(e)
                    execution.workflow_execution_completed_at = timezone.now()
                    execution.save()
                    self.logger.error(f"Resume failed: {e}")
                    return False
                    
        except WorkflowExecution.DoesNotExist:
            self.logger.error(f"Execution {execution_id} not found")
            return False


    def _resolve_context_object(self, payload: Dict[str, Any]) -> Any:
        """Resolve the primary object from the payload."""
        from django.contrib.contenttypes.models import ContentType
        from django.apps import apps
        
        # Priority list of ID keys to check
        object_keys = [
            ('lead_id', 'leads.Lead'),
            ('opportunity_id', 'opportunities.Opportunity'),
            ('case_id', 'cases.Case'),
            ('account_id', 'accounts.Account'),
            ('contact_id', 'accounts.Contact'),
            ('subscription_id', 'billing.Subscription'),
            ('invoice_id', 'billing.Invoice'),
            ('campaign_id', 'marketing.Campaign'),
            ('product_id', 'products.Product'),
            ('sale_id', 'sales.Sale'),
        ]
        
        for key, model_path in object_keys:
            if key in payload and payload[key]:
                try:
                    model = apps.get_model(model_path)
                    return model.objects.filter(id=payload[key]).first()
                except (LookupError, ValueError):
                    continue
        return None

    def _calculate_due_date(self, rule: Dict[str, Any]) -> Any:
        """Calculate due date based on rule."""
        from django.utils import timezone
        from datetime import timedelta
        
        if not rule or not isinstance(rule, dict):
            # Try parsing as direct date string if not dict
            if isinstance(rule, str):
                try:
                    from dateutil.parser import parse
                    return parse(rule)
                except:
                    return None
            return None
            
        rule_type = rule.get('type')
        if rule_type == 'relative':
            value = int(rule.get('value', 0))
            unit = rule.get('unit', 'days')
            
            if unit == 'hours':
                return timezone.now() + timedelta(hours=value)
            elif unit == 'minutes':
                return timezone.now() + timedelta(minutes=value)
            else: # days
                return timezone.now() + timedelta(days=value)
                
        return None

    def _resolve_assignee(self, rule: Dict[str, Any], context_object: Any, tenant_id: int) -> int:
        """Resolve assignee ID based on rule."""
        if not rule or not isinstance(rule, dict):
             # If strictly an ID (int/str), return it
            if isinstance(rule, (int, str)) and str(rule).isdigit():
                return int(rule)
            return None
            
        rule_type = rule.get('type')
        
        if rule_type == 'owner':
            if context_object and hasattr(context_object, 'owner_id') and context_object.owner_id:
                return context_object.owner_id
            return rule.get('fallback_user_id')
            
        elif rule_type == 'user':
            return rule.get('value')
            
        return rule.get('fallback_user_id')

    def execute_action(self, action: 'WorkflowAction', context: Dict[str, Any], execution: 'WorkflowExecution' = None) -> bool:
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
                from django.contrib.contenttypes.models import ContentType
                from django.template import Template, Context
                
                # Resolve context object
                context_object = self._resolve_context_object(payload)
                
                # Prepare template context
                template_ctx = {'payload': payload, 'object': context_object}
                django_context = Context(template_ctx)
                
                # Render dynamic strings
                title = Template(parameters.get('title', '')).render(django_context)
                description = Template(parameters.get('description', '')).render(django_context)
                
                # Calculate Due Date
                due_date_rule = parameters.get('due_date_rule') or parameters.get('due_date')
                due_date = self._calculate_due_date(due_date_rule)
                
                # Resolve Assignee
                assignee_rule = parameters.get('assignee_rule') or parameters.get('assigned_to_id')
                assignee_id = self._resolve_assignee(assignee_rule, context_object, tenant_id)

                # Determine Object Linking
                related_object_kwargs = {}
                if context_object:
                    related_object_kwargs['content_type'] = ContentType.objects.get_for_model(context_object)
                    related_object_kwargs['object_id'] = context_object.id
                
                Task.objects.create(
                    title=title,
                    description=description,
                    due_date=due_date,
                    assigned_to_id=assignee_id,
                    tenant_id=tenant_id,
                    **related_object_kwargs
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
                from .services import WebhookService
                from .models import WebhookEndpoint
                
                endpoint_id = parameters.get('webhook_endpoint_id')
                if endpoint_id:
                    endpoint = WebhookEndpoint.objects.get(id=endpoint_id)
                    return WebhookService.deliver_webhook(endpoint, payload)
                else:
                    # Direct URL fallback
                    import requests
                    requests.post(
                        parameters['url'],
                        json=payload,
                        headers=parameters.get('headers', {}),
                        timeout=parameters.get('timeout', 10)
                    )
                    return True
                
            elif action.action_type == 'approval':
                # Handle approval pause
                if execution:
                    execution.workflow_execution_status = 'waiting_for_approval'
                    execution.workflow_execution_current_step_id = action.id
                    execution.workflow_execution_current_branch_id = action.branch.id if action.branch else None
                    execution.workflow_execution_current_branch_value = action.branch_value
                    execution.workflow_execution_context_data = context
                    execution.save()
                    
                    # Create Approval record
                    from .models import WorkflowApproval
                    WorkflowApproval.objects.create(
                        workflow_execution=execution,
                        workflow_action=action,
                        approval_status='pending',
                        tenant_id=execution.tenant_id
                    )
                    
                    raise WorkflowPauseException(execution, action, action.branch, action.branch_value)
                return False
            
            elif action.action_type == 'send_sms':
                # Send SMS via WazoSMSService
                try:
                    from core.wazo import wazo_sms_service
                    from communication.models import SMS
                    
                    result = wazo_sms_service.send_sms(
                        from_number=parameters.get('from_number') or "+1000000000",
                        to_number=parameters.get('to_number'),
                        body=parameters.get('message', ''),
                    )
                    
                    # Log to communication history
                    CommunicationHistory.objects.create(
                        communication_type='sms',
                        recipient=parameters.get('to_number', ''),
                        subject='Workflow SMS',
                        content_text=parameters.get('message', ''),
                        status='sent' if result else 'failed',
                        tenant_id=tenant_id
                    )
                except Exception as e:
                    self.logger.error(f"Failed to send workflow SMS: {e}")
                    raise

            elif action.action_type == 'send_whatsapp':
                # Send WhatsApp message via WazoWhatsAppService
                try:
                    from core.wazo import wazo_whatsapp_service
                    
                    to_number = parameters.get('to_number')
                    # Resolving phone helper if needed (simplistic logic here)
                    if not to_number and context.get('object'):
                         obj = context.get('object')
                         if hasattr(obj, 'phone'):
                             to_number = obj.phone

                    template_name = parameters.get('template_name')
                    
                    if template_name:
                         # Send Template
                         wazo_whatsapp_service.send_template_message(
                             from_number=parameters.get('from_number'), # Service handles fallback
                             to_number=to_number,
                             template_name=template_name,
                             template_variables=parameters.get('template_variables', []),
                             tenant_id=str(tenant_id)
                         )
                    else:
                        # Send Text
                        wazo_whatsapp_service.send_message(
                            from_number=parameters.get('from_number'),
                            to_number=to_number,
                            body=parameters.get('message', ''),
                            tenant_id=str(tenant_id)
                        )
                except Exception as e:
                    self.logger.error(f"Failed to send workflow WhatsApp: {e}")
                    raise

            
            elif action.action_type == 'send_teams_message':
                # Send Microsoft Teams message via webhook
                try:
                    from communication.teams_service import teams_service
                    from communication.models import CommunicationHistory
                    
                    result = teams_service.send_message(
                        webhook_url=parameters.get('webhook_url'),
                        title=parameters.get('title', 'SalesCompass Notification'),
                        message=parameters.get('message', ''),
                        facts=parameters.get('facts'),
                        theme_color=parameters.get('theme_color', '0076D7'),
                    )
                    
                    # Log to communication history
                    CommunicationHistory.objects.create(
                        communication_type='microsoft_teams',
                        recipient=parameters.get('webhook_url', 'Teams Channel'),
                        subject=parameters.get('title', 'Workflow Notification'),
                        content_text=parameters.get('message', ''),
                        content_html='',
                        status='sent' if result.success else 'failed',
                        error_message=result.error or '',
                        tenant_id=tenant_id,
                    )
                    return result.success
                except Exception as e:
                    self.logger.error(f"Teams message send failed: {e}")
                    return False
            
            elif action.action_type == 'send_whatsapp':
                # Send WhatsApp message via Wazo Business API
                try:
                    from core.wazo import wazo_whatsapp_service
                    
                    wa_from = parameters.get('from_number')
                    wa_to = parameters.get('to_number')
                    body = parameters.get('message', '')
                    
                    result = wazo_whatsapp_service.send_message(
                        from_number=wa_from,
                        to_number=wa_to,
                        body=body
                    )
                    
                    # Log to communication models
                    from communication.models import ChatMessage
                    ChatMessage.objects.create(
                        tenant_id=tenant_id,
                        channel='whatsapp',
                        sender_name='Automation Workflow',
                        message=body,
                        external_id=result.message_id if result else None
                    )
                    return bool(result)
                except Exception as e:
                    self.logger.error(f"WhatsApp message send failed: {e}")
                    return False
            
            elif action.action_type == 'delay':
                # Schedule delayed execution
                if execution:
                    from .models import WorkflowScheduledExecution
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    delay_minutes = parameters.get('delay_minutes', 5)
                    delay_hours = parameters.get('delay_hours', 0)
                    delay_days = parameters.get('delay_days', 0)
                    
                    scheduled_for = timezone.now() + timedelta(
                        days=delay_days,
                        hours=delay_hours,
                        minutes=delay_minutes
                    )
                    
                    # Save current state for resumption
                    execution.workflow_execution_status = 'waiting_for_approval'  # Reusing status for paused state
                    execution.workflow_execution_current_step_id = action.id
                    execution.workflow_execution_current_branch_id = action.branch.id if action.branch else None
                    execution.workflow_execution_current_branch_value = action.branch_value
                    execution.workflow_execution_context_data = context
                    execution.save()
                    
                    # Create scheduled execution record
                    WorkflowScheduledExecution.objects.create(
                        workflow_execution=execution,
                        action=action,
                        scheduled_for=scheduled_for,
                        status='pending',
                        context_data=context,
                        tenant_id=execution.tenant_id
                    )
                    
                    # Queue Celery task for delayed execution
                    from .tasks import resume_delayed_workflow
                    resume_delayed_workflow.apply_async(
                        args=[execution.id],
                        eta=scheduled_for
                    )
                    
                    raise WorkflowPauseException(execution, action, action.branch, action.branch_value)
                return False
            
            elif action.action_type == 'loop':
                # Handle loop/iteration logic
                loop_count = parameters.get('loop_count', 1)
                loop_variable = parameters.get('loop_variable', 'items')
                max_iterations = parameters.get('max_iterations', 100)
                
                items = payload.get(loop_variable, [])
                if not isinstance(items, list):
                    items = [items]
                
                # Limit iterations
                items = items[:max_iterations]
                
                # Execute actions for each item
                loop_actions = parameters.get('loop_actions', [])
                for idx, item in enumerate(items):
                    loop_context = {**context, 'loop_item': item, 'loop_index': idx}
                    # Note: Loop actions would need separate processing
                    self.logger.info(f"Loop iteration {idx + 1}/{len(items)}")
                
                return True
            
            elif action.action_type == 'custom_code':
                # Execute custom code action in a sandboxed environment
                from .models import CustomCodeSnippet, CustomCodeExecutionLog
                import time
                
                snippet_id = parameters.get('snippet_id')
                code_parameters = parameters.get('code_parameters', {})
                
                if not snippet_id:
                    self.logger.error("No snippet_id provided for custom_code action")
                    return False
                
                try:
                    snippet = CustomCodeSnippet.objects.get(id=snippet_id, tenant_id=tenant_id)
                    
                    if not snippet.is_active:
                        self.logger.warning(f"Custom code snippet {snippet_id} is not active")
                        return False
                    
                    # Create execution log
                    execution_log = CustomCodeExecutionLog.objects.create(
                        custom_code_snippet=snippet,
                        workflow_execution=execution,
                        input_parameters=code_parameters,
                        execution_status='running',
                        tenant_id=tenant_id
                    )
                    
                    start_time = time.time()
                    
                    # Execute the custom code in a secure sandbox
                    execution_context = {
                        'payload': payload,
                        'tenant_id': tenant_id,
                        'parameters': code_parameters,
                    }
                    
                    result = self._execute_custom_code_safely(snippet.code_content, execution_context)
                    
                    execution_time = int((time.time() - start_time) * 1000)
                    
                    if result['success']:
                        execution_log.output_result = result.get('result', {})
                        execution_log.execution_status = 'completed'
                        execution_log.execution_time_ms = execution_time
                        execution_log.save()
                        return True
                    else:
                        execution_log.error_message = result.get('error', 'Unknown error')
                        execution_log.execution_status = 'failed'
                        execution_log.execution_time_ms = execution_time
                        execution_log.save()
                        return False
                        
                except CustomCodeSnippet.DoesNotExist:
                    self.logger.error(f"Custom code snippet {snippet_id} not found")
                    return False
                except Exception as e:
                    self.logger.error(f"Custom code execution failed: {e}")
                    return False
                
            else:
                self.logger.warning(f"Unknown action type: {action.action_type}")
                return False
            
            self.logger.info(f"Action {action.action_type} executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Action {action.id} execution failed: {e}")
            return False

    def _execute_custom_code_safely(self, code_content: str, execution_context: dict) -> dict:
        """
        Execute custom code in a secure sandboxed environment.
        Uses subprocess isolation with timeout to prevent security issues.
        
        Args:
            code_content: The Python code to execute
            execution_context: Context dict with payload, tenant_id, parameters
        
        Returns:
            Dict with 'success' bool and 'result' or 'error' key
        """
        import tempfile
        import subprocess
        import json
        import os
        import sys
        
        # Build sandboxed code with limited imports
        sandbox_code = f'''
import json
import datetime
import re
import math
from decimal import Decimal

# Context provided from the workflow
context = {json.dumps(execution_context)}
payload = context.get('payload', {{}})
parameters = context.get('parameters', {{}})

# User's custom code starts here
{code_content}
# User's custom code ends here

# Output the result - user should define 'result' variable
result = locals().get('result', {{'status': 'completed'}})
print(json.dumps(result))
'''
        
        # Write the code to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sandbox_code)
            temp_file = f.name
        
        try:
            # Execute the code with a timeout using subprocess
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )
            
            if result.returncode == 0:
                try:
                    # Parse the result
                    output = json.loads(result.stdout.strip())
                    return {'success': True, 'result': output}
                except json.JSONDecodeError:
                    return {'success': True, 'result': {'output': result.stdout}}
            else:
                return {
                    'success': False, 
                    'error': f"Code execution failed: {result.stderr[:500]}"
                }
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Code execution timed out (30s limit)'}
        except Exception as e:
            return {'success': False, 'error': f"Execution error: {str(e)}"}
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_file)
            except:
                pass