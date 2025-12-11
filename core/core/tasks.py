"""
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
=======
>>>>>>> Stashed changes
Background tasks for business metrics calculations
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from core.services.business_metrics_service import BusinessMetricsService
from core.models import Tenant
from datetime import datetime, timedelta
from django.core.cache import cache
from core.core.cache import BusinessMetricsCache


logger = get_task_logger(__name__)


@shared_task
def calculate_clv_metrics_task(tenant_id=None):
    """
    Background task to calculate CLV metrics
    """
    logger.info(f"Starting CLV metrics calculation for tenant {tenant_id}")
    
    try:
        # Calculate metrics
        metrics = BusinessMetricsService.calculate_clv_metrics(tenant_id=tenant_id)
        
        # Cache the results
        BusinessMetricsCache.invalidate_metrics_cache('clv', tenant_id=tenant_id)
        cached_metrics = BusinessMetricsCache.get_clv_metrics(tenant_id=tenant_id)
        
        logger.info(f"Successfully calculated CLV metrics for tenant {tenant_id}")
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'metrics_calculated': len(metrics),
            'calculated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating CLV metrics for tenant {tenant_id}: {str(e)}")
        return {
            'status': 'error',
            'tenant_id': tenant_id,
            'error': str(e),
            'calculated_at': datetime.now().isoformat()
        }


@shared_task
def calculate_cac_metrics_task(tenant_id=None):
    """
    Background task to calculate CAC metrics
    """
    logger.info(f"Starting CAC metrics calculation for tenant {tenant_id}")
    
    try:
        # Calculate metrics
        metrics = BusinessMetricsService.calculate_cac_metrics(tenant_id=tenant_id)
        
        # Cache the results
        BusinessMetricsCache.invalidate_metrics_cache('cac', tenant_id=tenant_id)
        cached_metrics = BusinessMetricsCache.get_cac_metrics(tenant_id=tenant_id)
        
        logger.info(f"Successfully calculated CAC metrics for tenant {tenant_id}")
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'metrics_calculated': len(metrics),
            'calculated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating CAC metrics for tenant {tenant_id}: {str(e)}")
        return {
            'status': 'error',
            'tenant_id': tenant_id,
            'error': str(e),
            'calculated_at': datetime.now().isoformat()
        }


@shared_task
def calculate_sales_velocity_metrics_task(tenant_id=None):
    """
    Background task to calculate sales velocity metrics
    """
    logger.info(f"Starting sales velocity metrics calculation for tenant {tenant_id}")
    
    try:
        # Calculate metrics
        metrics = BusinessMetricsService.calculate_sales_velocity_metrics(tenant_id=tenant_id)
        
        # Cache the results
        BusinessMetricsCache.invalidate_metrics_cache('sales_velocity', tenant_id=tenant_id)
        cached_metrics = BusinessMetricsCache.get_sales_velocity_metrics(tenant_id=tenant_id)
        
        logger.info(f"Successfully calculated sales velocity metrics for tenant {tenant_id}")
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'metrics_calculated': len(metrics),
            'calculated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating sales velocity metrics for tenant {tenant_id}: {str(e)}")
        return {
            'status': 'error',
            'tenant_id': tenant_id,
            'error': str(e),
            'calculated_at': datetime.now().isoformat()
        }


@shared_task
def calculate_roi_metrics_task(tenant_id=None):
    """
    Background task to calculate ROI metrics
    """
    logger.info(f"Starting ROI metrics calculation for tenant {tenant_id}")
    
    try:
        # Calculate metrics
        metrics = BusinessMetricsService.calculate_roi_metrics(tenant_id=tenant_id)
        
        # Cache the results
        BusinessMetricsCache.invalidate_metrics_cache('roi', tenant_id=tenant_id)
        cached_metrics = BusinessMetricsCache.get_roi_metrics(tenant_id=tenant_id)
        
        logger.info(f"Successfully calculated ROI metrics for tenant {tenant_id}")
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'metrics_calculated': len(metrics),
            'calculated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating ROI metrics for tenant {tenant_id}: {str(e)}")
        return {
            'status': 'error',
            'tenant_id': tenant_id,
            'error': str(e),
            'calculated_at': datetime.now().isoformat()
        }


@shared_task
def calculate_conversion_funnel_metrics_task(tenant_id=None):
    """
    Background task to calculate conversion funnel metrics
    """
    logger.info(f"Starting conversion funnel metrics calculation for tenant {tenant_id}")
    
    try:
        # Calculate metrics
        metrics = BusinessMetricsService.calculate_conversion_funnel_metrics(tenant_id=tenant_id)
        
        # Cache the results
        BusinessMetricsCache.invalidate_metrics_cache('conversion_funnel', tenant_id=tenant_id)
        cached_metrics = BusinessMetricsCache.get_conversion_funnel_metrics(tenant_id=tenant_id)
        
        logger.info(f"Successfully calculated conversion funnel metrics for tenant {tenant_id}")
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'metrics_calculated': len(metrics),
            'calculated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating conversion funnel metrics for tenant {tenant_id}: {str(e)}")
        return {
            'status': 'error',
            'tenant_id': tenant_id,
            'error': str(e),
            'calculated_at': datetime.now().isoformat()
        }


@shared_task
def calculate_all_metrics_task(tenant_id=None):
    """
    Background task to calculate all business metrics for a tenant
    """
    logger.info(f"Starting calculation of all metrics for tenant {tenant_id}")
    
    results = {}
    
    # Calculate all metrics
    results['clv'] = calculate_clv_metrics_task(tenant_id)
    results['cac'] = calculate_cac_metrics_task(tenant_id)
    results['sales_velocity'] = calculate_sales_velocity_metrics_task(tenant_id)
    results['roi'] = calculate_roi_metrics_task(tenant_id)
    results['conversion_funnel'] = calculate_conversion_funnel_metrics_task(tenant_id)
    
    logger.info(f"Completed calculation of all metrics for tenant {tenant_id}")
    return {
        'status': 'success',
        'tenant_id': tenant_id,
        'results': results,
        'calculated_at': datetime.now().isoformat()
    }


@shared_task
def calculate_metrics_trend_task(days=30, tenant_id=None):
    """
    Background task to calculate metrics trends
    """
    logger.info(f"Starting metrics trend calculation for {days} days for tenant {tenant_id}")
    
    try:
        # Calculate trend metrics
        metrics = BusinessMetricsService.calculate_metrics_trend(days=days, tenant_id=tenant_id)
        
        # Cache the results
        BusinessMetricsCache.invalidate_metrics_cache('trend', tenant_id=tenant_id)
        cached_metrics = BusinessMetricsCache.get_metrics_trend(days=days, tenant_id=tenant_id)
        
        logger.info(f"Successfully calculated metrics trend for {days} days for tenant {tenant_id}")
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'days': days,
            'metrics_calculated': len(metrics['daily_metrics']),
            'calculated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating metrics trend for tenant {tenant_id}: {str(e)}")
        return {
            'status': 'error',
            'tenant_id': tenant_id,
            'days': days,
            'error': str(e),
            'calculated_at': datetime.now().isoformat()
        }


@shared_task
def update_all_tenants_metrics_task():
    """
    Background task to update metrics for all tenants
    """
    logger.info("Starting metrics update for all tenants")
    
    try:
        tenants = Tenant.objects.all()
        results = []
        
        for tenant in tenants:
            result = calculate_all_metrics_task.delay(tenant.id)
            results.append({
                'tenant_id': tenant.id,
                'task_id': result.task_id
            })
        
        logger.info(f"Started metrics update for {len(results)} tenants")
        return {
            'status': 'success',
            'tenants_processed': len(results),
            'task_results': results,
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating metrics for all tenants: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'processed_at': datetime.now().isoformat()
        }


@shared_task
def scheduled_metrics_refresh_task():
    """
    Scheduled task to refresh metrics periodically
    """
    logger.info("Starting scheduled metrics refresh")
    
    try:
        # Calculate metrics for all tenants
        result = update_all_tenants_metrics_task.delay()
        
        logger.info("Scheduled metrics refresh initiated")
        return {
            'status': 'success',
            'task_id': result.task_id,
            'refresh_started_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in scheduled metrics refresh: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'refresh_attempted_at': datetime.now().isoformat()
        }
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
