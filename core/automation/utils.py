import json
from typing import Dict, Any
from django.db import transaction
from django.utils import timezone
from .models import Automation, AutomationExecutionLog
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


