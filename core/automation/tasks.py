from celery import shared_task
from celery.utils.log import get_task_logger
from typing import Any, Dict, Optional
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

@shared_task(bind=True)
def send_webhook_task(self, endpoint_id: int, payload: Dict[str, Any], event_type: str = 'workflow.execution'):
    """
    Celery task to deliver a webhook with retries.
    """
    from .models import WebhookEndpoint
    from .services import WebhookService
    
    try:
        endpoint = WebhookEndpoint.objects.get(id=endpoint_id)
        success = WebhookService.deliver_webhook(endpoint, payload, event_type)
        
        if not success:
            # Check if we should retry
            if self.request.retries < endpoint.retry_attempts:
                logger.info(f"Retrying webhook delivery for endpoint {endpoint_id} (Attempt {self.request.retries + 1})")
                raise self.retry(countdown=endpoint.retry_delay_seconds)
            else:
                logger.error(f"Webhook delivery failed for {endpoint_id} after {endpoint.retry_attempts} retries.")
                
    except WebhookEndpoint.DoesNotExist:
        logger.error(f"Webhook endpoint {endpoint_id} not found.")
    except Exception as exc:
        logger.error(f"Webhook task error: {exc}")
        # Reraise if it's already a retry
        if hasattr(self, 'Retry') and isinstance(exc, self.Retry):
            raise exc
        raise self.retry(exc=exc, countdown=60)

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


@shared_task(bind=True, max_retries=3)
def resume_delayed_workflow(self, execution_id: int):
    """
    Celery task to resume a delayed workflow execution.
    This is triggered after a delay action completes its wait time.
    """
    from .engine import WorkflowEngine
    from .models import WorkflowExecution, WorkflowScheduledExecution
    from django.utils import timezone
    
    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        
        # Update scheduled execution status
        scheduled = WorkflowScheduledExecution.objects.filter(
            workflow_execution=execution,
            status='pending'
        ).first()
        
        if scheduled:
            scheduled.status = 'executed'
            scheduled.executed_at = timezone.now()
            scheduled.save()
        
        # Resume the workflow
        engine = WorkflowEngine()
        success = engine.resume_workflow(execution_id)
        
        if not success:
            logger.warning(f"Resume of workflow execution {execution_id} returned False")
            if scheduled:
                scheduled.status = 'failed'
                scheduled.save()
                
    except WorkflowExecution.DoesNotExist:
        logger.error(f"Workflow execution {execution_id} not found for resume")
    except Exception as exc:
        logger.error(f"Resume delayed workflow failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))