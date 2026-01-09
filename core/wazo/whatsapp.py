import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from django.utils import timezone
from .client import WazoAPIClient

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppMessageResult:
    """Result object returned after sending a WhatsApp message."""
    message_id: str
    from_number: str
    to_number: str
    body: str
    status: str
    message_type: str = 'text'
    sent_at: Optional[datetime] = None
    metadata: Optional[Dict] = None


class WazoWhatsAppService:
    """
    Wazo WhatsApp Business API service for SalesCompass.
    Provides comprehensive WhatsApp messaging capabilities including:
    - Text messages
    - Template messages
    - Inbound message handling
    - Status tracking
    """
    
    def __init__(self, client: Optional[WazoAPIClient] = None):
        self.client = client or WazoAPIClient()
    
    def is_available(self, tenant_id: str = None) -> bool:
        """Check if WhatsApp service is available."""
        if not self.client.is_configured():
            return False
        # In production, also check tenant-specific WhatsApp configuration
        if tenant_id:
            try:
                from communication.whatsapp_models import WhatsAppConfiguration
                return WhatsAppConfiguration.objects.filter(
                    tenant_id=tenant_id, is_active=True
                ).exists()
            except Exception:
                pass
        return True
    
    def get_tenant_numbers(self, tenant_id: str) -> List[str]:
        """Get available WhatsApp numbers for a tenant."""
        try:
            from communication.whatsapp_models import WhatsAppConfiguration
            configs = WhatsAppConfiguration.objects.filter(
                tenant_id=tenant_id, is_active=True
            )
            return [c.phone_number for c in configs]
        except Exception as e:
            logger.warning(f"Could not fetch tenant WhatsApp numbers: {e}")
            # Return mock numbers for development
            return ['+12025550123', '+12025550198']
    
    def send_message(
        self,
        from_number: str,
        to_number: str,
        body: str,
        tenant_config: Optional[Dict] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[WhatsAppMessageResult]:
        """
        Send a text WhatsApp message.
        
        Args:
            from_number: Sender's WhatsApp Business number
            to_number: Recipient's phone number
            body: Message text content
            tenant_config: Optional tenant-specific API configuration
            tenant_id: Optional tenant ID for logging
            
        Returns:
            WhatsAppMessageResult on success, None on failure
        """
        if not self.is_available():
            logger.warning("WhatsApp service not available")
            return None
        
        try:
            payload = {
                'from': from_number,
                'to': to_number,
                'body': body,
                'channel': 'whatsapp',
                'type': 'text',
                'tenant_config': tenant_config or {}
            }
            
            response = self.client.post('/api/chatd/1.0/messages', data=payload)
            
            result = WhatsAppMessageResult(
                message_id=response.get('id', f'wa_{timezone.now().timestamp()}'),
                from_number=from_number,
                to_number=to_number,
                body=body,
                status='sent',
                message_type='text',
                sent_at=timezone.now(),
                metadata=response.get('metadata')
            )
            
            # Store in database if tenant_id provided
            if tenant_id:
                self._store_message(result, 'outbound', tenant_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return None
    
    def send_template_message(
        self,
        from_number: str,
        to_number: str,
        template_name: str,
        template_variables: List[str],
        language: str = 'en',
        tenant_config: Optional[Dict] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[WhatsAppMessageResult]:
        """
        Send a WhatsApp template message.
        
        Template messages are required for initiating conversations outside
        the 24-hour customer service window.
        
        Args:
            from_number: Sender's WhatsApp Business number
            to_number: Recipient's phone number
            template_name: Approved template name
            template_variables: List of variable values for the template
            language: Language code (default: 'en')
            tenant_config: Optional tenant-specific API configuration
            tenant_id: Optional tenant ID for logging
            
        Returns:
            WhatsAppMessageResult on success, None on failure
        """
        if not self.is_available():
            logger.warning("WhatsApp service not available")
            return None
        
        try:
            # Build template components
            components = []
            if template_variables:
                components.append({
                    'type': 'body',
                    'parameters': [
                        {'type': 'text', 'text': var} for var in template_variables
                    ]
                })
            
            payload = {
                'from': from_number,
                'to': to_number,
                'channel': 'whatsapp',
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {'code': language},
                    'components': components
                },
                'tenant_config': tenant_config or {}
            }
            
            response = self.client.post('/api/chatd/1.0/messages', data=payload)
            
            result = WhatsAppMessageResult(
                message_id=response.get('id', f'wa_tpl_{timezone.now().timestamp()}'),
                from_number=from_number,
                to_number=to_number,
                body=f"[Template: {template_name}]",
                status='sent',
                message_type='template',
                sent_at=timezone.now(),
                metadata={
                    'template_name': template_name,
                    'template_variables': template_variables,
                    'language': language,
                    **response.get('metadata', {})
                }
            )
            
            if tenant_id:
                self._store_message(result, 'outbound', tenant_id, template_name=template_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send template message: {e}")
            return None
    
    def receive_message(
        self,
        message_id: str,
        from_number: str,
        to_number: str,
        body: str,
        message_type: str = 'text',
        media_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        raw_data: Optional[Dict] = None
    ) -> Optional['WhatsAppMessage']:
        """
        Process an inbound WhatsApp message from webhook.
        
        Args:
            message_id: WhatsApp message ID
            from_number: Sender's phone number
            to_number: Recipient (our business number)
            body: Message text content
            message_type: Type of message (text, image, etc.)
            media_url: URL to media for non-text messages
            tenant_id: Tenant ID for multi-tenant isolation
            raw_data: Raw webhook payload
            
        Returns:
            WhatsAppMessage model instance
        """
        try:
            from communication.whatsapp_models import WhatsAppMessage
            
            # Create message record
            message = WhatsAppMessage.objects.create(
                message_id=message_id,
                direction='inbound',
                message_type=message_type,
                from_number=from_number,
                to_number=to_number,
                body=body,
                media_url=media_url or '',
                status='received',
                tenant_id=tenant_id,
                wazo_data=raw_data or {}
            )
            
            # Try to match to CRM entities
            self._match_to_crm(message, from_number)
            
            # Log engagement event
            self._log_engagement_event(message, 'inbound', tenant_id)
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to process inbound WhatsApp message: {e}")
            return None
    
    def update_message_status(
        self,
        message_id: str,
        status: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Update message status from webhook callback.
        
        Args:
            message_id: WhatsApp message ID
            status: New status (sent, delivered, read, failed)
            timestamp: When the status changed
            
        Returns:
            True if update successful
        """
        try:
            from communication.whatsapp_models import WhatsAppMessage
            
            message = WhatsAppMessage.objects.filter(message_id=message_id).first()
            if not message:
                logger.warning(f"Message not found for status update: {message_id}")
                return False
            
            ts = timestamp or timezone.now()
            
            if status == 'sent':
                message.status = 'sent'
                message.sent_at = ts
            elif status == 'delivered':
                message.status = 'delivered'
                message.delivered_at = ts
            elif status == 'read':
                message.status = 'read'
                message.read_at = ts
                # Log engagement event for message read
                self._log_engagement_event(message, 'read', message.tenant_id)
            elif status == 'failed':
                message.status = 'failed'
            
            message.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update message status: {e}")
            return False
    
    def _store_message(
        self,
        result: WhatsAppMessageResult,
        direction: str,
        tenant_id: str,
        template_name: str = ''
    ) -> None:
        """Store message in database."""
        try:
            from communication.whatsapp_models import WhatsAppMessage
            
            WhatsAppMessage.objects.create(
                message_id=result.message_id,
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
    
    def _match_to_crm(self, message, phone_number: str) -> None:
        """Try to match inbound message to CRM contact/lead."""
        try:
            from accounts.models import Contact
            from leads.models import Lead
            
            # Normalize phone number (last 10 digits)
            normalized = phone_number[-10:] if len(phone_number) >= 10 else phone_number
            
            # Try contact first
            contact = Contact.objects.filter(phone__icontains=normalized).first()
            if contact:
                message.contact = contact
                message.account = contact.account
                message.save()
                return
            
            # Try lead
            lead = Lead.objects.filter(phone__icontains=normalized).first()
            if lead:
                message.lead = lead
                message.save()
                
        except Exception as e:
            logger.debug(f"Could not match WhatsApp message to CRM: {e}")
    
    def _log_engagement_event(self, message, event_type: str, tenant_id: str) -> None:
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
                        'message_preview': message.body[:50] if message.body else ''
                    },
                    engagement_score=3
                )
            elif event_type == 'read':
                log_engagement_event(
                    tenant_id=tenant_id,
                    event_type='whatsapp_read',
                    description=f"WhatsApp message read by {message.to_number}",
                    title="WhatsApp Message Read",
                    metadata={
                        'message_id': message.message_id
                    },
                    engagement_score=1
                )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")


# Singleton instance
wazo_whatsapp_service = WazoWhatsAppService()

