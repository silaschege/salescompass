from celery import shared_task
from django.utils import timezone
from .utils import apply_decay_to_all_accounts
from .automation_rules import run_auto_nba_check

@shared_task
def update_engagement_scores():
    """
    Nightly task to update engagement scores, apply decay, and generate auto-NBAs.
    """
    print(f"[{timezone.now()}] Starting daily engagement score update...")
    apply_decay_to_all_accounts()
    
    print(f"[{timezone.now()}] Running Auto-NBA rules...")
    run_auto_nba_check()
    
    print(f"[{timezone.now()}] Running Churn Risk Detection...")
    from .models import EngagementStatus
    from .automation_rules import check_churn_risk
    
    # Iterate over all accounts with engagement status
    for status in EngagementStatus.objects.all():
        if status.account:
            check_churn_risk(status.account)
    
    print(f"[{timezone.now()}] Engagement update complete.")


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def send_engagement_webhook(self, webhook_id, event_id):
    """
    Send webhook with retry logic and detailed delivery logging.
    """
    import requests
    from .models import EngagementWebhook, EngagementEvent, WebhookDeliveryLog
    
    try:
        webhook = EngagementWebhook.objects.get(id=webhook_id)
        event = EngagementEvent.objects.get(id=event_id)
    except (EngagementWebhook.DoesNotExist, EngagementEvent.DoesNotExist):
        return "Webhook or Event not found"

    # Prepare payload based on event data
    payload = {
        'event_id': event.id,
        'event_type': event.event_type,
        'title': event.title,
        'description': event.description,
        'score': float(event.engagement_score),
        'account_id': event.account_id,
        'timestamp': event.created_at.isoformat(),
        'priority': event.priority,
    }

    # Create Delivery Log (Initial)
    log = WebhookDeliveryLog.objects.create(
        webhook=webhook,
        event=event,
        payload=payload,
        attempt_number=self.request.retries + 1,
        tenant_id=webhook.tenant_id
    )

    try:
        response = requests.post(
            webhook.url, 
            json=payload, 
            headers={'Content-Type': 'application/json', 'X-SalesCompass-Event': event.event_type},
            timeout=10
        )
        
        # Update Log with Response
        log.status_code = response.status_code
        log.response_body = response.text[:1000]  # Truncate if too long
        log.success = 200 <= response.status_code < 300
        log.save()

        # Raise for retry if failed
        if not log.success:
            log.error_message = f"HTTP {response.status_code}"
            log.save()
            raise Exception(f"Webhook failed with status {response.status_code}")

        return f"Webhook sent successfully: HTTP {response.status_code}"

    except Exception as exc:
        # Update Log with Error
        log.success = False
        log.error_message = str(exc)
        log.save()
        
        # Retry
        raise self.retry(exc=exc)
