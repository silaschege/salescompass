from celery import shared_task
import requests
import hmac
import hashlib
import json
from django.utils import timezone
from .models import Webhook
import logging

logger = logging.getLogger(__name__)


@shared_task
def trigger_webhook(event_type, payload, tenant_id):
    """
    Fan-out task to find active webhooks and queue delivery tasks.
    
    Args:
        event_type (str): Event name (e.g., 'lead.created')
        payload (dict): Data to send
        tenant_id (str): Tenant ID
    
    """
    from .models import APIToken
    import datetime
    
    # Get the current API token (if available)
    if 'api_key' in payload:
        try:
            api_token = APIToken.objects.get(token=payload['api_key'])
            
            # Update request counts
            api_token.daily_request_count += 1
            api_token.weekly_request_count += 1
            api_token.monthly_request_count += 1
            
            # Update time window counters
            now = timezone.now()
            one_hour_ago = now - datetime.timedelta(hours=1)
            
            # Reset hourly counter if needed
            if api_token.last_updated.hour != now.hour:
                api_token.last_hour_requests = 0
                
            api_token.last_hour_requests += 1
            api_token.last_updated = now
            
            api_token.save()
        except APIToken.DoesNotExist:
            pass
    
    # Find active webhooks for this tenant
    # Note: We filter by event in Python to avoid DB-specific JSON lookup issues (SQLite)
    all_webhooks = Webhook.objects.filter(
        tenant__tenant_id=tenant_id,
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
        
        # Track start time for latency measurement
        start_time = timezone.now()
        
        # Send request
        response = requests.post(
            webhook.url,
            data=json_data,
            headers=headers,
            timeout=10
        )
        
        # Calculate latency
        latency = (timezone.now() - start_time).total_seconds() * 1000  # in milliseconds
        
        # Update webhook delivery metrics
        webhook.daily_delivery_count += 1
        webhook.last_hour_deliveries += 1
        
        # Update latency metrics
        webhook.avg_delivery_time_ms = (webhook.avg_delivery_time_ms * webhook.success_count + latency) / (webhook.success_count + 1)
        
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
            
        return {
            'status': status,
            'response_code': response.status_code,
            'webhook_id': webhook_id
        }
            
    except Exception as exc:
        logger.error(f"Webhook delivery failed: {str(exc)}")
        webhook.failure_count += 1
        webhook.save(update_fields=['failure_count'])
        
        # Retry if not exceeded max retries
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))