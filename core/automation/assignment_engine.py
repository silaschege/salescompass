import logging
from typing import Any, Dict, List, Optional, Union
from django.apps import apps
from django.db import transaction
from django.db.models import Count, Q
from settings_app.models import AssignmentRule, Territory, TeamMember

logger = logging.getLogger(__name__)

def evaluate_assignment_rules(record_type: str, record_id: int) -> bool:
    """
    Evaluate assignment rules for a given record.
    
    Args:
        record_type: 'leads', 'cases', or 'opportunities'
        record_id: ID of the record to assign
        
    Returns:
        bool: True if assigned, False otherwise
    """
    try:
        # Get the model class
        model_class = _get_model_class(record_type)
        if not model_class:
            logger.error(f"Unknown record type: {record_type}")
            return False
            
        # Get the record
        try:
            record = model_class.objects.get(id=record_id)
        except model_class.DoesNotExist:
            logger.error(f"{record_type} with id {record_id} not found")
            return False
            
        # If already assigned, check if we should re-assign (logic can be added here)
        # For now, assuming we only assign if owner is None or specific system user
        if getattr(record, 'owner_id', None):
             # Optional: Log that it's already assigned
             return False

        # Fetch active rules for this module, ordered by priority
        rules = AssignmentRule.objects.filter(
            module=record_type,
            is_active=True
        ).order_by('-priority', 'name')
        
        for rule in rules:
            if _check_criteria_match(rule, record):
                assignee = _get_assignee(rule, record)
                if assignee:
                    # Assign the record
                    record.owner = assignee
                    record.save(update_fields=['owner'])
                    logger.info(f"Assigned {record_type} {record_id} to {assignee} via rule {rule.name}")
                    return True
                    
        logger.info(f"No matching assignment rule found for {record_type} {record_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error evaluating assignment rules: {e}")
        return False

def _get_model_class(record_type: str):
    """Map string record type to Django model."""
    if record_type == 'leads':
        return apps.get_model('leads', 'Lead')
    elif record_type == 'cases':
        return apps.get_model('cases', 'Case')
    elif record_type == 'opportunities':
        return apps.get_model('opportunities', 'Opportunity')
    return None

def _check_criteria_match(rule: AssignmentRule, record: Any) -> bool:
    """
    Check if the record matches the rule's criteria.
    Criteria is a JSON dict: {'field__operator': 'value', ...}
    Simple implementation supports direct equality and some lookups.
    """
    if not rule.criteria:
        return True # No criteria means it matches everything (catch-all)
        
    for key, expected_value in rule.criteria.items():
        # Handle operators like field__contains, field__gt, etc.
        field_parts = key.split('__')
        field_name = field_parts[0]
        operator = field_parts[1] if len(field_parts) > 1 else 'eq'
        
        # Get actual value from record
        if not hasattr(record, field_name):
            logger.warning(f"Field {field_name} not found on record {record}")
            return False
            
        actual_value = getattr(record, field_name)
        
        if not _compare_values(actual_value, operator, expected_value):
            return False
            
    return True

def _compare_values(actual: Any, operator: str, expected: Any) -> bool:
    """Compare values based on operator."""
    try:
        if operator == 'eq':
            return str(actual) == str(expected)
        elif operator == 'ne':
            return str(actual) != str(expected)
        elif operator == 'contains':
            return str(expected).lower() in str(actual).lower()
        elif operator == 'gt':
            return float(actual) > float(expected)
        elif operator == 'lt':
            return float(actual) < float(expected)
        elif operator == 'in':
            return str(actual) in expected
        return False
    except Exception:
        return False

def _get_assignee(rule: AssignmentRule, record: Any):
    """Determine the assignee based on rule type."""
    if rule.rule_type == 'round_robin':
        return rule.get_next_assignee()
        
    elif rule.rule_type == 'territory':
        return _get_territory_assignee(rule, record)
        
    elif rule.rule_type == 'load_balanced':
        return _get_load_balanced_assignee(rule, record)
        
    elif rule.rule_type == 'criteria':
        # For simple criteria match, usually just pick the first available user in the group
        # or could be a specific user if defined. 
        # Assuming the rule's assignees list is the pool.
        return rule.assignees.filter(is_active=True).first()
        
    return None

def _get_territory_assignee(rule: AssignmentRule, record: Any):
    """
    Assign based on territory matching.
    Assumes record has a 'country' or 'state' field.
    """
    # Try to find location on record
    country = getattr(record, 'country', None)
    if not country:
        return None
        
    # Find users in the rule's pool who cover this territory
    # This requires checking TeamMember -> Territory -> country_codes
    
    potential_assignees = rule.assignees.filter(is_active=True)
    
    for user in potential_assignees:
        try:
            team_member = user.team_member
            if team_member.territory and country in team_member.territory.country_codes:
                return user
        except TeamMember.DoesNotExist:
            continue
            
    return None

def _get_load_balanced_assignee(rule: AssignmentRule, record: Any):
    """
    Assign to user with fewest active records of this type.
    """
    potential_assignees = rule.assignees.filter(is_active=True)
    if not potential_assignees.exists():
        return None
        
    model_class = type(record)
    
    # Annotate users with count of active records
    # Assuming 'active' means not closed/won/lost/archived depending on model
    # For simplicity, just counting all owned records for now, or could refine based on status
    
    # We need to do this query carefully to avoid performance issues
    # But for a limited set of assignees, it's okay to iterate or subquery
    
    best_assignee = None
    min_count = float('inf')
    
    for user in potential_assignees:
        count = model_class.objects.filter(owner=user).count() # Could filter by status here
        if count < min_count:
            min_count = count
            best_assignee = user
            
    return best_assignee
