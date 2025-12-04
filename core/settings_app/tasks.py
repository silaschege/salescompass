"""
Assignment Rule Automation Tasks
Celery tasks for evaluating and executing assignment rules
"""
from celery import shared_task
from django.db.models import Q, Count
import logging

logger = logging.getLogger(__name__)


@shared_task
def evaluate_assignment_rules(record_type, record_id):
    """
    Evaluate and execute assignment rules for a given record
    
    Args:
        record_type (str): Type of record ('lead', 'case', 'opportunity')
        record_id (int): ID of the record to assign
        
    Returns:
        dict: Result of assignment including assigned_to_id and rule_used
    """
    from .models import AssignmentRule
    from django.apps import apps
    
    logger.info(f"Evaluating assignment rules for {record_type} #{record_id}")
    
    # Get the model class
    model_map = {
        'lead': 'leads.Lead',
        'case': 'cases.Case',
        'opportunity': 'opportunities.Opportunity',
    }
    
    if record_type not in model_map:
        logger.error(f"Invalid record type: {record_type}")
        return {'success': False, 'error': 'Invalid record type'}
    
    try:
        model_class = apps.get_model(model_map[record_type])
        record = model_class.objects.get(id=record_id)
    except model_class.DoesNotExist:
        logger.error(f"{record_type} #{record_id} not found")
        return {'success': False, 'error': 'Record not found'}
    
    # Get active assignment rules for this module, ordered by priority
    rules = AssignmentRule.objects.filter(
        module=record_type,
        is_active=True,
        tenant_id=record.tenant_id
    ).order_by('-priority', 'name').prefetch_related('assignees')
    
    logger.info(f"Found {rules.count()} active rules for {record_type}")
    
    # Try each rule in priority order
    for rule in rules:
        assignee = None
        
        # Check if criteria matches (for criteria-based rules)
        if rule.rule_type == 'criteria' and not _matches_criteria(record, rule.criteria):
            logger.debug(f"Rule '{rule.name}' criteria not matched")
            continue
        
        # Get assignee based on rule type
        if rule.rule_type == 'round_robin':
            assignee = _get_round_robin_assignee(rule)
        elif rule.rule_type == 'territory':
            assignee = _get_territory_assignee(record, rule)
        elif rule.rule_type == 'load_balanced':
            assignee = _get_load_balanced_assignee(record_type, rule)
        elif rule.rule_type == 'criteria':
            assignee = _get_criteria_assignee(rule)
        
        # If we found an assignee, assign the record
        if assignee:
            # Assign the record
            if hasattr(record, 'owner'):
                record.owner = assignee
            elif hasattr(record, 'assigned_to'):
                record.assigned_to = assignee
            record.save(update_fields=['owner'] if hasattr(record, 'owner') else ['assigned_to'])
            
            logger.info(f"Assigned {record_type} #{record_id} to {assignee.email} using rule '{rule.name}'")
            
            return {
                'success': True,
                'assigned_to_id': assignee.id,
                'assigned_to_email': assignee.email,
                'rule_id': rule.id,
                'rule_name': rule.name,
                'rule_type': rule.rule_type
            }
    
    logger.warning(f"No matching assignment rule found for {record_type} #{record_id}")
    return {'success': False, 'error': 'No matching rule found'}


def _matches_criteria(record, criteria):
    """
    Check if a record matches the given criteria
    
    Args:
        record: Django model instance
        criteria (dict): Criteria dictionary e.g. {'country': 'US', 'industry': 'Tech'}
        
    Returns:
        bool: True if all criteria match
    """
    if not criteria:
        return True  # No criteria means always match
    
    for field, value in criteria.items():
        # Handle related fields with double underscore
        if hasattr(record, field):
            record_value = getattr(record, field)
            # Handle case-insensitive string comparison
            if isinstance(record_value, str) and isinstance(value, str):
                if record_value.lower() != value.lower():
                    return False
            elif record_value != value:
                return False
        else:
            # Try to get through related fields
            try:
                parts = field.split('__')
                current = record
                for part in parts:
                    current = getattr(current, part)
                if current != value:
                    return False
            except (AttributeError, TypeError):
                return False
    
    return True


def _get_round_robin_assignee(rule):
    """
    Get next assignee using round-robin algorithm
    
    Args:
        rule: AssignmentRule instance
        
    Returns:
        User instance or None
    """
    assignees = list(rule.assignees.filter(is_active=True))
    if not assignees:
        logger.warning(f"Rule '{rule.name}' has no active assignees")
        return None
    
    # Get next assignee based on last_assigned_index
    next_index = (rule.last_assigned_index + 1) % len(assignees)
    assignee = assignees[next_index]
    
    # Update last_assigned_index
    rule.last_assigned_index = next_index
    rule.save(update_fields=['last_assigned_index'])
    
    logger.debug(f"Round-robin assigned to {assignee.email} (index {next_index})")
    return assignee


def _get_territory_assignee(record, rule):
    """
    Get assignee based on territory
    
    Args:
        record: Record instance
        rule: AssignmentRule instance
        
    Returns:
        User instance or None
    """
    # Try to get territory from record
    territory = None
    if hasattr(record, 'territory'):
        territory = record.territory
    elif hasattr(record, 'account') and hasattr(record.account, 'territory'):
        territory = record.account.territory
    elif hasattr(record, 'country'):
        # Try to find territory by country code
        from .models import Territory
        territory = Territory.objects.filter(
            tenant_id=record.tenant_id,
            country_codes__contains=record.country
        ).first()
    
    if not territory:
        logger.debug(f"No territory found for record {record.id}")
        return None
    
    # Find an assignee in this territory
    assignees = rule.assignees.filter(
        is_active=True,
        team_members__territory=territory
    )
    
    if not assignees.exists():
        logger.debug(f"No assignees found for territory {territory.name}")
        return None
    
    # Use round-robin among territory assignees
    assignee = assignees.first()
    logger.debug(f"Territory-based assigned to {assignee.email} in {territory.name}")
    return assignee


def _get_load_balanced_assignee(record_type, rule):
    """
    Get assignee with least current workload
    
    Args:
        record_type: Type of record
        rule: AssignmentRule instance
        
    Returns:
        User instance or None
    """
    from django.apps import apps
    
    model_map = {
        'lead': 'leads.Lead',
        'case': 'cases.Case',
        'opportunity': 'opportunities.Opportunity',
    }
    
    model_class = apps.get_model(model_map[record_type])
    
    # Count current open records per assignee
    assignees = rule.assignees.filter(is_active=True)
    
    if not assignees.exists():
        return None
    
    # Annotate with count of assigned records
    # Try both 'owner' and 'assigned_to' fields
    owner_field = 'owner' if hasattr(model_class, 'owner') else 'assigned_to'
    
    assignee_loads = []
    for assignee in assignees:
        filter_kwargs = {owner_field: assignee}
        # Only count open/active records
        if hasattr(model_class, 'status'):
            filter_kwargs['status__in'] = ['new', 'open', 'in_progress', 'working']
        
        count = model_class.objects.filter(**filter_kwargs).count()
        assignee_loads.append((assignee, count))
    
    # Sort by load (ascending) and get the one with least load
    assignee_loads.sort(key=lambda x: x[1])
    assignee = assignee_loads[0][0]
    
    logger.debug(f"Load-balanced assigned to {assignee.email} (current load: {assignee_loads[0][1]})")
    return assignee


def _get_criteria_assignee(rule):
    """
    Get assignee for criteria-based rule (round-robin among eligible assignees)
    
    Args:
        rule: AssignmentRule instance
        
    Returns:
        User instance or None
    """
    # For criteria-based rules, use round-robin among the eligible assignees
    return _get_round_robin_assignee(rule)


# Additional helper task for batch assignment
@shared_task
def evaluate_bulk_assignment(record_type, record_ids):
    """
    Evaluate assignment rules for multiple records
    
    Args:
        record_type (str): Type of record
        record_ids (list): List of record IDs
        
    Returns:
        dict: Summary of assignments
    """
    results = []
    for record_id in record_ids:
        result = evaluate_assignment_rules(record_type, record_id)
        results.append(result)
    
    successful = sum(1 for r in results if r.get('success'))
    
    return {
        'total': len(record_ids),
        'successful': successful,
        'failed': len(record_ids) - successful,
        'results': results
    }


@shared_task
def trigger_webhook(event_type, payload, tenant_id):
    """
    Fan-out task to find active webhooks and queue delivery tasks.
    
    Args:
        event_type (str): Event name (e.g., 'lead.created')
        payload (dict): Data to send
        tenant_id (str): Tenant ID
    """
    from .models import Webhook
    
    # Find active webhooks for this tenant
    # Note: We filter by event in Python to avoid DB-specific JSON lookup issues (SQLite)
    all_webhooks = Webhook.objects.filter(
        tenant_id=tenant_id,
        is_active=True
    )
    
    webhooks = [w for w in all_webhooks if event_type in w.events]
    
    if not webhooks:
        logger.info(f"No webhooks found for {event_type} in tenant {tenant_id}")
        return []
    
    task_ids = []
    for webhook in webhooks:
        # Queue individual delivery task
        task = deliver_webhook.delay(webhook.id, event_type, payload)
        task_ids.append(task.id)
            
    return task_ids


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_webhook(self, webhook_id, event_type, payload):
    """
    Deliver a single webhook payload to a specific URL.
    
    Args:
        webhook_id (int): ID of the Webhook model
        event_type (str): Event name
        payload (dict): Data to send
    """
    from .models import Webhook
    import requests
    import hmac
    import hashlib
    import json
    from django.utils import timezone
    
    try:
        webhook = Webhook.objects.get(id=webhook_id)
    except Webhook.DoesNotExist:
        logger.error(f"Webhook {webhook_id} not found")
        return {'status': 'error', 'error': 'Webhook not found'}
        
    try:
        # Prepare payload
        data = {
            'event': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': payload
        }
        json_data = json.dumps(data)
        
        # Generate signature
        signature = hmac.new(
            webhook.secret.encode(),
            json_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-SalesCompass-Signature': signature,
            'X-SalesCompass-Event': event_type,
            'User-Agent': 'SalesCompass-Webhook/1.0'
        }
        
        # Send request
        response = requests.post(
            webhook.url,
            data=json_data,
            headers=headers,
            timeout=10
        )
        
        # Update stats
        webhook.last_triggered = timezone.now()
        
        if 200 <= response.status_code < 300:
            webhook.success_count += 1
            status = 'success'
            webhook.save(update_fields=['last_triggered', 'success_count'])
        else:
            webhook.failure_count += 1
            status = 'failed'
            webhook.save(update_fields=['last_triggered', 'failure_count'])
            logger.warning(f"Webhook {webhook.id} failed with status {response.status_code}")
            
            # Retry on server errors
            if response.status_code >= 500:
                raise requests.exceptions.RequestException(f"Server error: {response.status_code}")
        
        return {
            'webhook_id': webhook.id,
            'status': status,
            'http_code': response.status_code
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error delivering webhook {webhook.id}: {str(e)}")
        
        # Only increment failure count if we are giving up or it's a hard failure
        # But for retries, we might want to track transient failures too?
        # For now, let's just log and retry
        
        try:
            # Retry the task
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            webhook.failure_count += 1
            webhook.save(update_fields=['failure_count'])
            return {
                'webhook_id': webhook.id,
                'status': 'failed',
                'error': f"Max retries exceeded: {str(e)}"
            }
