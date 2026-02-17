import logging
from typing import Optional, List
from django.utils import timezone
from .models import SMS
from wazo import wazo_sms_service

logger = logging.getLogger(__name__)

class SMSResult:
    def __init__(self, success: bool, message_id: Optional[str] = None, error: Optional[str] = None):
        self.success = success
        self.message_id = message_id
        self.error = error

class MockSMSProvider:
    """Mock SMS provider for development and testing."""
    def send(self, from_number: str, to_number: str, body: str) -> SMSResult:
        logger.info(f"MOCK SMS: From {from_number} to {to_number}: {body}")
        return SMSResult(success=True, message_id="mock_msg_123")

class SMSService:
    """
    Unified SMS service for supporting multiple providers (Wazo, Mock, Future Twilio).
    """
    def __init__(self):
        self.mock_provider = MockSMSProvider()
        self.wazo_provider = wazo_sms_service

    def get_provider(self, provider_type: str = 'auto'):
        if provider_type == 'wazo' and self.wazo_provider.is_available():
            return self.wazo_provider
        
        if provider_type == 'auto':
            if self.wazo_provider.is_available():
                return self.wazo_provider
        
        return self.mock_provider

    def send_model_sms(self, sms_instance: SMS) -> SMSResult:
        """Send SMS based on an SMS model instance."""
        if sms_instance.status == 'sent':
            return SMSResult(success=True, error="Already sent")

        provider = self.get_provider()
        
        sms_instance.status = 'sending'
        sms_instance.save()

        try:
            # Note: Wazo adapter returns WazoSMS object, Mock returns SMSResult
            # We normalize here
            result = provider.send_sms(
                from_number=sms_instance.sender_phone or "+1000000000",
                to_number=sms_instance.recipient_phone,
                body=sms_instance.message,
                tenant_id=str(sms_instance.tenant.id) if sms_instance.tenant else None
            )
            
            if result:
                sms_instance.status = 'sent'
                sms_instance.sent_at = timezone.now()
                sms_instance.external_id = getattr(result, 'message_id', '')
                sms_instance.save()
                return SMSResult(success=True, message_id=sms_instance.external_id)
            else:
                raise Exception("Provider failed to send")
                
        except Exception as e:
            logger.error(f"Failed to send SMS {sms_instance.id}: {e}")
            sms_instance.status = 'failed'
            sms_instance.error_message = str(e)
            sms_instance.save()
            return SMSResult(success=False, error=str(e))

sms_service = SMSService()
