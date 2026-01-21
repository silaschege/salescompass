"""
Twilio WhatsApp Business API Service for SalesCompass CRM.
Replaces Wazo-based WhatsApp with Twilio's API.
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppMessageResult:
    """Result object returned after sending a WhatsApp message."""
    message_sid: str
    from_number: str
    to_number: str
    body: str
    status: str
    message_type: str = 'text'
    sent_at: Optional[datetime] = None
    metadata: Optional[Dict] = None


class TwilioWhatsAppService:
    """
    Twilio WhatsApp Business API service for SalesCompass.
    
    Supports:
    - Text messages
    - Template messages (for outside 24-hour window)
    - Media messages (images, documents)
    - Status tracking via webhooks
    """
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.whatsapp_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', None)
        self.is_sandbox = getattr(settings, 'TWILIO_WHATSAPP_SANDBOX', True)
        self._client = None
    
    @property
    def client(self):
        """Lazy-load Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.error("Twilio package not installed. Run: pip install twilio")
                return None
            except Exception as e:
                logger.error(f"Failed to create Twilio client: {e}")
                return None
        return self._client
    
    def is_available(self, tenant_id: str = None) -> bool:
        """Check if WhatsApp service is available."""
        return bool(
            self.account_sid and 
            self.auth_token and 
            self.whatsapp_number and
            self.client
        )
    
    def get_tenant_numbers(self, tenant_id: str) -> List[str]:
        """Get available WhatsApp numbers for a tenant."""
        if self.whatsapp_number:
            return [self.whatsapp_number]
        return []
    
    def _format_whatsapp_number(self, number: str) -> str:
        """Format number for WhatsApp (whatsapp:+1234567890)."""
        number = number.replace('whatsapp:', '')
        if not number.startswith('+'):
            number = '+' + number
        return f'whatsapp:{number}'
    
    def send_message(
        self,
        from_number: str,
        to_number: str,
        body: str,
        tenant_config: Optional[Dict] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[WhatsAppMessageResult]:
        """
        Send a text WhatsApp message via Twilio.
        """
        if not self.is_available():
            logger.warning("Twilio WhatsApp service not available")
            return None
        
        try:
            from_wa = self._format_whatsapp_number(from_number or self.whatsapp_number)
            to_wa = self._format_whatsapp_number(to_number)
            
            message = self.client.messages.create(
                from_=from_wa,
                to=to_wa,
                body=body
            )
            
            result = WhatsAppMessageResult(
                message_sid=message.sid,
                from_number=from_number or self.whatsapp_number,
                to_number=to_number,
                body=body,
                status=message.status,
                message_type='text',
                sent_at=timezone.now(),
                metadata={'twilio_sid': message.sid}
            )
            
            if tenant_id:
                self._store_message(result, 'outbound', tenant_id)
            
            logger.info(f"WhatsApp message sent: {message.sid}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return None
    
    def send_template_message(
        self,
        from_number: str,
        to_number: str,
        template_sid: str,
        template_variables: Dict[str, str],
        language: str = 'en',
        tenant_config: Optional[Dict] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[WhatsAppMessageResult]:
        """
        Send a WhatsApp template message via Twilio Content API.
        Required for initiating conversations outside 24-hour window.
        """
        if not self.is_available():
            logger.warning("Twilio WhatsApp service not available")
            return None
        
        try:
            from_wa = self._format_whatsapp_number(from_number or self.whatsapp_number)
            to_wa = self._format_whatsapp_number(to_number)
            
            message = self.client.messages.create(
                from_=from_wa,
                to=to_wa,
                content_sid=template_sid,
                content_variables=template_variables
            )
            
            result = WhatsAppMessageResult(
                message_sid=message.sid,
                from_number=from_number or self.whatsapp_number,
                to_number=to_number,
                body=f"[Template: {template_sid}]",
                status=message.status,
                message_type='template',
                sent_at=timezone.now(),
                metadata={
                    'twilio_sid': message.sid,
                    'template_sid': template_sid,
                    'template_variables': template_variables
                }
            )
            
            if tenant_id:
                self._store_message(result, 'outbound', tenant_id, template_name=template_sid)
            
            logger.info(f"WhatsApp template message sent: {message.sid}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send template message: {e}")
            return None
    
    def send_media_message(
        self,
        from_number: str,
        to_number: str,
        media_url: str,
        caption: str = '',
        tenant_id: Optional[str] = None
    ) -> Optional[WhatsAppMessageResult]:
        """Send a media message (image, document, etc.)."""
        if not self.is_available():
            return None
        
        try:
            from_wa = self._format_whatsapp_number(from_number or self.whatsapp_number)
            to_wa = self._format_whatsapp_number(to_number)
            
            message = self.client.messages.create(
                from_=from_wa,
                to=to_wa,
                body=caption,
                media_url=[media_url]
            )
            
            result = WhatsAppMessageResult(
                message_sid=message.sid,
                from_number=from_number or self.whatsapp_number,
                to_number=to_number,
                body=caption,
                status=message.status,
                message_type='media',
                sent_at=timezone.now(),
                metadata={'twilio_sid': message.sid, 'media_url': media_url}
            )
            
            if tenant_id:
                self._store_message(result, 'outbound', tenant_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send media message: {e}")
            return None
    
    def receive_message(
        self,
        message_sid: str,
        from_number: str,
        to_number: str,
        body: str,
        message_type: str = 'text',
        media_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        raw_data: Optional[Dict] = None
    ):
        """Process an inbound WhatsApp message from Twilio webhook."""
        try:
            from communication.whatsapp_models import WhatsAppMessage
            
            from_num = from_number.replace('whatsapp:', '')
            to_num = to_number.replace('whatsapp:', '')
            
            message = WhatsAppMessage.objects.create(
                message_id=message_sid,
                direction='inbound',
                message_type=message_type,
                from_number=from_num,
                to_number=to_num,
                body=body,
                media_url=media_url or '',
                status='received',
                tenant_id=tenant_id,
                wazo_data=raw_data or {}
            )
            
            self._match_to_crm(message, from_num)
            self._log_engagement_event(message, 'inbound', tenant_id)
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to process inbound WhatsApp message: {e}")
            return None
    
    def update_message_status(
        self,
        message_sid: str,
        status: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Update message status from Twilio webhook callback."""
        try:
            from communication.whatsapp_models import WhatsAppMessage
            
            message = WhatsAppMessage.objects.filter(message_id=message_sid).first()
            if not message:
                logger.warning(f"Message not found: {message_sid}")
                return False
            
            ts = timestamp or timezone.now()
            
            if status in ['sent', 'queued']:
                message.status = 'sent'
                message.sent_at = ts
            elif status == 'delivered':
                message.status = 'delivered'
                message.delivered_at = ts
            elif status == 'read':
                message.status = 'read'
                message.read_at = ts
                self._log_engagement_event(message, 'read', message.tenant_id)
            elif status in ['failed', 'undelivered']:
                message.status = 'failed'
            
            message.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update message status: {e}")
            return False
    
    def _store_message(self, result, direction, tenant_id, template_name=''):
        """Store message in database."""
        try:
            from communication.whatsapp_models import WhatsAppMessage
            
            WhatsAppMessage.objects.create(
                message_id=result.message_sid,
                direction=direction,
                message_type=result.message_type,
                from_number=result.from_number,
                to_number=result.to_number,
                body=result.body,
                status=result.status,
                sent_at=result.sent_at,
                template_name=template_name,
                tenant_id=tenant_id,
                wazo_data=result.metadata or {}
            )
        except Exception as e:
            logger.warning(f"Failed to store WhatsApp message: {e}")
    
    def _match_to_crm(self, message, phone_number):
        """Try to match inbound message to CRM contact/lead."""
        try:
            from accounts.models import Contact
            from leads.models import Lead
            
            normalized = phone_number[-10:] if len(phone_number) >= 10 else phone_number
            
            contact = Contact.objects.filter(phone__icontains=normalized).first()
            if contact:
                message.contact = contact
                message.account = contact.account
                message.save()
                return
            
            lead = Lead.objects.filter(phone__icontains=normalized).first()
            if lead:
                message.lead = lead
                message.save()
                
        except Exception as e:
            logger.debug(f"Could not match WhatsApp message to CRM: {e}")
    
    def _log_engagement_event(self, message, event_type, tenant_id):
        """Log engagement event for the WhatsApp message."""
        try:
            from engagement.utils import log_engagement_event
            
            if event_type == 'inbound':
                log_engagement_event(
                    tenant_id=tenant_id,
                    event_type='whatsapp_received',
                    description=f"WhatsApp message received from {message.from_number}",
                    title="WhatsApp Message Received",
                    metadata={
                        'message_id': message.message_id,
                        'from_number': message.from_number,
                    },
                    engagement_score=3
                )
            elif event_type == 'read':
                log_engagement_event(
                    tenant_id=tenant_id,
                    event_type='whatsapp_read',
                    description=f"WhatsApp message read by {message.to_number}",
                    title="WhatsApp Message Read",
                    metadata={'message_id': message.message_id},
                    engagement_score=1
                )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")


# Singleton instance
twilio_whatsapp_service = TwilioWhatsAppService()
