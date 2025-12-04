from celery import shared_task
from celery.utils.log import get_task_logger
from typing import Any, Dict
from .engine import execute_automations_sync

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_automation_task(self, trigger_type: str, payload: Dict[str, Any]):
    """
    Celery task to execute automations asynchronously.
    """
    try:
        execute_automations_sync(trigger_type, payload)
    except Exception as exc:
        logger.error(f"Automation task failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=3)
def evaluate_assignment_rules(self, record_type: str, record_id: int):
    """
    Celery task to evaluate assignment rules for a record.
    """
    try:
        from .assignment_engine import evaluate_assignment_rules as engine_evaluate
        engine_evaluate(record_type, record_id)
    except Exception as exc:
        logger.error(f"Assignment task failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))