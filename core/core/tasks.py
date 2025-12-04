"""
Celery Tasks for Core Event Processing

Provides async task execution for:
- Event bus processing
- Background jobs
- Scheduled tasks
"""
import logging
from typing import Dict, Any
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_event_task(self, event: Dict[str, Any]) -> None:
    """
    Process an event asynchronously via Celery.
    
    This task is called by the event bus when async_execution is enabled.
    """
    try:
        from core.event_bus import event_bus
        event_bus._emit_sync(event)
        logger.info(f"Processed event: {event.get('event_type')}")
    except Exception as e:
        logger.error(f"Failed to process event: {e}")
        self.retry(exc=e)


@shared_task
def send_email_async(
    to: list,
    subject: str,
    html_content: str = None,
    template: str = None,
    context: dict = None,
    **kwargs
) -> bool:
    """
    Send email asynchronously.
    
    Usage:
        send_email_async.delay(
            to=['user@example.com'],
            subject='Welcome!',
            template='welcome_email',
            context={'name': 'John'}
        )
    """
    try:
        from communication.email_service import email_service
        
        result = email_service.send_email(
            to=to,
            subject=subject,
            html_content=html_content,
            template=template,
            context=context,
            **kwargs
        )
        return result.success
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


@shared_task
def sync_tenant_metrics(tenant_id: str = None) -> None:
    """
    Sync and aggregate tenant metrics periodically.
    
    Should be scheduled to run every 5-15 minutes.
    """
    try:
        from infrastructure.metrics import metrics_collector
        
        if tenant_id:
            metrics_collector.flush_metrics(tenant_id)
        else:
            metrics_collector.flush_metrics()
            
        logger.info("Tenant metrics synced")
    except Exception as e:
        logger.error(f"Failed to sync metrics: {e}")


@shared_task
def cleanup_old_audit_logs(days: int = 90) -> int:
    """
    Clean up audit logs older than specified days.
    
    Should be scheduled to run daily.
    """
    try:
        from audit_logs.models import AuditLog
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=days)
        count, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
        
        logger.info(f"Deleted {count} old audit logs")
        return count
    except Exception as e:
        logger.error(f"Failed to cleanup audit logs: {e}")
        return 0


@shared_task
def check_feature_flag_consistency() -> None:
    """
    Check and log feature flag consistency.
    
    Should be scheduled to run hourly.
    """
    try:
        from feature_flags.models import FeatureFlag
        from core.feature_flag_middleware import FeatureFlagCache
        
        FeatureFlagCache.clear()
        
        flags = FeatureFlag.objects.filter(is_active=True)
        logger.info(f"Active feature flags: {flags.count()}")
        
        for flag in flags:
            logger.debug(f"Flag {flag.key}: {flag.rollout_percentage}% rollout")
            
    except Exception as e:
        logger.error(f"Failed to check feature flags: {e}")
