"""
Twilio Webhook Handler for SalesCompass CRM.
Handles WhatsApp and SMS webhooks from Twilio.
"""
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)


class TwilioWebhookHandler:
    """Handle incoming webhooks from Twilio."""
    
    def __init__(self):
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    
    def verify_signature(self, request) -> bool:
        """Verify Twilio request signature."""
        if not self.auth_token:
            logger.warning("Twilio auth token not configured")
            return False
        
        try:
            from twilio.request_validator import RequestValidator
            
            validator = RequestValidator(self.auth_token)
            url = request.build_absolute_uri()
            params = request.POST.dict()
            signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
            
            return validator.validate(url, params, signature)
            
        except ImportError:
            logger.error("Twilio package not installed")
            return False
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def process_whatsapp_message(self, request):
        """Process incoming WhatsApp message webhook."""
        try:
            from .twilio_whatsapp import twilio_whatsapp_service
            
            message_sid = request.POST.get('MessageSid', '')
            from_number = request.POST.get('From', '')
            to_number = request.POST.get('To', '')
            body = request.POST.get('Body', '')
            num_media = int(request.POST.get('NumMedia', 0))
            
            media_url = None
            message_type = 'text'
            if num_media > 0:
                media_url = request.POST.get('MediaUrl0', '')
                message_type = request.POST.get('MediaContentType0', 'media').split('/')[0]
            
            tenant_id = self._get_tenant_for_number(to_number)
            
            message = twilio_whatsapp_service.receive_message(
                message_sid=message_sid,
                from_number=from_number,
                to_number=to_number,
                body=body,
                message_type=message_type,
                media_url=media_url,
                tenant_id=tenant_id,
                raw_data=dict(request.POST)
            )
            
            if message:
                logger.info(f"Processed WhatsApp message: {message_sid}")
                return {'status': 'processed', 'message_id': message.id}
            else:
                return {'status': 'failed'}
                
        except Exception as e:
            logger.error(f"Failed to process WhatsApp message: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def process_status_callback(self, request):
        """Process message status callback from Twilio."""
        try:
            from .twilio_whatsapp import twilio_whatsapp_service
            
            message_sid = request.POST.get('MessageSid', '')
            status = request.POST.get('MessageStatus', '')
            
            success = twilio_whatsapp_service.update_message_status(
                message_sid=message_sid,
                status=status
            )
            
            return {'status': 'processed' if success else 'failed'}
            
        except Exception as e:
            logger.error(f"Failed to process status callback: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_tenant_for_number(self, phone_number: str) -> str:
        """Map a WhatsApp number to a tenant ID."""
        try:
            from tenants.models import Tenant
            tenant = Tenant.objects.first()
            return str(tenant.id) if tenant else None
        except Exception:
            return None


# Singleton instance
twilio_webhook_handler = TwilioWebhookHandler()


@method_decorator(csrf_exempt, name='dispatch')
class TwilioWhatsAppWebhookView(View):
    """Handle Twilio WhatsApp webhooks."""
    
    def post(self, request):
        handler = twilio_webhook_handler
        
        # Verify signature in production
        if not settings.DEBUG:
            if not handler.verify_signature(request):
                return HttpResponse(status=403)
        
        # Determine webhook type
        if 'MessageSid' in request.POST:
            if 'MessageStatus' in request.POST:
                result = handler.process_status_callback(request)
            else:
                result = handler.process_whatsapp_message(request)
        else:
            result = {'status': 'ignored'}
        
        # Return empty TwiML response
        return HttpResponse(
            '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            content_type='text/xml'
        )
