
import hmac
import hashlib
import requests
import json
import logging
from django.utils import timezone
from django.core.cache import cache
from .models import WebhookEndpoint, WebhookDeliveryLog

logger = logging.getLogger(__name__)

class WebhookService:
    @staticmethod
    def is_rate_limited(endpoint: WebhookEndpoint) -> bool:
        """Check if the endpoint is currently rate limited."""
        if not endpoint.rate_limit:
            return False
            
        cache_key = f"webhook_rate_limit:{endpoint.id}"
        count = cache.get(cache_key, 0)
        
        if count >= endpoint.rate_limit:
            return True
            
        # Increment count and set expiry if it's the first request
        if count == 0:
            cache.set(cache_key, 1, endpoint.rate_limit_period_seconds)
        else:
            cache.incr(cache_key)
            
        return False

    @staticmethod
    def sign_payload(payload: dict, secret: str, algorithm: str = 'sha256') -> str:
        """Generate a signature for the payload using the secret."""
        if not secret:
            return ""
            
        payload_bytes = json.dumps(payload).encode('utf-8')
        if algorithm == 'sha256':
            hash_func = hashlib.sha256
        elif algorithm == 'sha1':
            hash_func = hashlib.sha1
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
            
        signature = hmac.new(secret.encode('utf-8'), payload_bytes, hash_func).hexdigest()
        return signature

    @classmethod
    def deliver_webhook(cls, endpoint: WebhookEndpoint, payload: dict, event_type: str = 'workflow.execution') -> bool:
        """Deliver a webhook to the specified endpoint."""
        if not endpoint.webhook_endpoint_is_active:
            logger.warning(f"Webhook endpoint {endpoint.id} is inactive. Skipping delivery.")
            return False

        if cls.is_rate_limited(endpoint):
            logger.warning(f"Webhook endpoint {endpoint.id} is rate limited. Skipping delivery.")
            # We could log this as a skipped delivery
            return False

        # Generate signature if secret is present
        headers = endpoint.headers.copy() if endpoint.headers else {}
        if endpoint.secret:
            signature = cls.sign_payload(payload, endpoint.secret, endpoint.signature_algorithm)
            headers[endpoint.signature_header] = signature

        # Create log entry
        log = WebhookDeliveryLog.objects.create(
            webhook_endpoint=endpoint,
            event_type=event_type,
            payload=json.dumps(payload),
            headers=headers,
            webhook_delivery_url=endpoint.webhook_endpoint_url,
            http_method=endpoint.http_method,
            status='sent',
            tenant=endpoint.tenant
        )

        start_time = timezone.now()
        try:
            response = requests.request(
                method=endpoint.http_method,
                url=endpoint.webhook_endpoint_url,
                json=payload,
                headers=headers,
                timeout=endpoint.timeout_seconds
            )
            
            execution_time = (timezone.now() - start_time).total_seconds() * 1000
            log.status = 'delivered' if 200 <= response.status_code < 300 else 'failed'
            log.response_status_code = response.status_code
            log.response_body = response.text[:5000] # Cap body size
            log.execution_time_ms = execution_time
            log.completed_at = timezone.now()
            log.save()

            # Update endpoint stats
            endpoint.last_called = timezone.now()
            endpoint.last_response_code = response.status_code
            if log.status == 'failed':
                endpoint.failure_count += 1
                if endpoint.failure_count >= endpoint.disabled_after_failures:
                    endpoint.webhook_endpoint_is_active = False
                    logger.warning(f"Endpoint {endpoint.id} disabled after {endpoint.failure_count} failures.")
            else:
                endpoint.failure_count = 0
            endpoint.save()

            return log.status == 'delivered'

        except Exception as e:
            execution_time = (timezone.now() - start_time).total_seconds() * 1000
            log.status = 'failed'
            log.error_message = str(e)
            log.execution_time_ms = execution_time
            log.completed_at = timezone.now()
            log.save()
            
            endpoint.last_called = timezone.now()
            endpoint.last_error = str(e)
            endpoint.failure_count += 1
            endpoint.save()
            
            logger.error(f"Webhook delivery failed for {endpoint.id}: {e}")
            return False
