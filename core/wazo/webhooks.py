"""
Wazo Webhook Handlers for SalesCompass CRM.
Receives events from Wazo Platform and updates CRM accordingly.
"""
import logging
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class WazoWebhookHandler:
    """
    Handles incoming webhook events from Wazo Platform.
    """
    
    # Event type mappings
    CALL_EVENTS = [
        'call_created', 'call_answered', 'call_ended',
        'call_updated', 'call_held', 'call_resumed'
    ]
    
    SMS_EVENTS = [
        'chatd_user_room_message_created',
        'chatd_user_room_message_updated'
    ]
    
    VOICEMAIL_EVENTS = [
        'user_voicemail_message_created'
    ]
    
    WHATSAPP_EVENTS = [
        'whatsapp_message_received',
        'whatsapp_message_status',
        'whatsapp_message_delivered',
        'whatsapp_message_read'
    ]
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or getattr(settings, 'WAZO_WEBHOOK_SECRET', None)
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify HMAC signature from Wazo webhook.
        """
        if not self.secret_key:
            logger.warning("No webhook secret configured, skipping verification")
            return True
        
        expected = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def process_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route event to appropriate handler.
        """
        logger.info(f"Processing Wazo event: {event_type}")
        
        if event_type in self.CALL_EVENTS:
            return self._handle_call_event(event_type, data)
        elif event_type in self.SMS_EVENTS:
            return self._handle_sms_event(event_type, data)
        elif event_type in self.VOICEMAIL_EVENTS:
            return self._handle_voicemail_event(event_type, data)
        elif event_type in self.WHATSAPP_EVENTS:
            return self._handle_whatsapp_event(event_type, data)
        else:
            logger.debug(f"Unhandled event type: {event_type}")
            return {'status': 'ignored', 'event_type': event_type}
    
    def _handle_call_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call-related events.
        """
        from .models import WazoCallLog
        
        call_id = data.get('call_id')
        if not call_id:
            return {'status': 'error', 'message': 'No call_id in event'}
        
        # Map Wazo event to our status
        status_map = {
            'call_created': 'initiated',
            'call_answered': 'answered',
            'call_ended': 'completed',
            'call_held': 'answered',
            'call_resumed': 'answered',
        }
        
        try:
            call_log, created = WazoCallLog.objects.get_or_create(
                call_id=call_id,
                defaults={
                    'direction': 'inbound' if data.get('is_caller') else 'outbound',
                    'from_number': data.get('caller_id_number', ''),
                    'to_number': data.get('peer_caller_id_number', ''),
                    'status': status_map.get(event_type, 'initiated'),
                    'started_at': timezone.now(),
                    'wazo_data': data,
                }
            )
            
            if not created:
                # Update existing call
                call_log.status = status_map.get(event_type, call_log.status)
                if event_type == 'call_ended':
                    call_log.ended_at = timezone.now()
                    call_log.duration = data.get('talking_to_duration', 0)
                call_log.wazo_data = data
                call_log.save()
            
            # Try to match to CRM contact
            self._match_call_to_crm(call_log)
            
            return {'status': 'processed', 'call_id': call_id, 'created': created}
            
        except Exception as e:
            logger.error(f"Error processing call event: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_sms_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SMS/message events.
        """
        from .models import WazoSMSLog
        
        message_id = data.get('uuid') or data.get('message_id')
        if not message_id:
            return {'status': 'error', 'message': 'No message_id in event'}
        
        try:
            sms_log, created = WazoSMSLog.objects.get_or_create(
                message_id=message_id,
                defaults={
                    'direction': 'inbound',
                    'from_number': data.get('user_uuid', ''),
                    'to_number': data.get('room_uuid', ''),
                    'body': data.get('content', ''),
                    'status': 'received',
                    'sent_at': timezone.now(),
                    'wazo_data': data,
                }
            )
            
            return {'status': 'processed', 'message_id': message_id, 'created': created}
            
        except Exception as e:
            logger.error(f"Error processing SMS event: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_voicemail_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle voicemail events.
        """
        # Create a call log entry for voicemail
        from .models import WazoCallLog
        
        try:
            call_log = WazoCallLog.objects.create(
                call_id=f"vm_{data.get('id', timezone.now().timestamp())}",
                direction='inbound',
                from_number=data.get('caller_id_num', 'Unknown'),
                to_number=data.get('user_uuid', ''),
                status='voicemail',
                started_at=timezone.now(),
                wazo_data=data,
            )
            
            return {'status': 'processed', 'voicemail_id': call_log.call_id}
            
        except Exception as e:
            logger.error(f"Error processing voicemail event: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _match_call_to_crm(self, call_log) -> None:
        """
        Try to match a call to CRM entities based on phone number.
        """
        from accounts.models import Contact
        from leads.models import Lead
        
        # Search for matching contact or lead
        phone_to_search = call_log.from_number if call_log.direction == 'inbound' else call_log.to_number
        
        try:
            # Try to find a contact
            contact = Contact.objects.filter(
                phone__icontains=phone_to_search[-10:]  # Last 10 digits
            ).first()
            
            if contact:
                call_log.contact = contact
                call_log.account = contact.account
                call_log.save()
                return
            
            # Try to find a lead
            lead = Lead.objects.filter(
                phone__icontains=phone_to_search[-10:]
            ).first()
            
            if lead:
                call_log.lead = lead
                call_log.save()
                
        except Exception as e:
            logger.debug(f"Could not match call to CRM: {e}")
    
    def _handle_whatsapp_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle WhatsApp-related webhook events.
        
        Processes inbound messages and status updates from WhatsApp Business API.
        """
        from .whatsapp import wazo_whatsapp_service
        
        try:
            if event_type == 'whatsapp_message_received':
                # Process inbound message
                message = wazo_whatsapp_service.receive_message(
                    message_id=data.get('message_id', data.get('id', '')),
                    from_number=data.get('from', data.get('sender', '')),
                    to_number=data.get('to', data.get('recipient', '')),
                    body=data.get('text', {}).get('body', data.get('body', '')),
                    message_type=data.get('type', 'text'),
                    media_url=data.get('media_url'),
                    tenant_id=data.get('tenant_id'),
                    raw_data=data
                )
                
                if message:
                    return {
                        'status': 'processed',
                        'message_id': message.message_id,
                        'created': True
                    }
                return {'status': 'error', 'message': 'Failed to process message'}
            
            elif event_type in ['whatsapp_message_status', 'whatsapp_message_delivered', 'whatsapp_message_read']:
                # Process status update
                message_id = data.get('message_id', data.get('id', ''))
                
                # Determine status from event type or data
                if event_type == 'whatsapp_message_delivered':
                    status = 'delivered'
                elif event_type == 'whatsapp_message_read':
                    status = 'read'
                else:
                    status = data.get('status', 'sent')
                
                updated = wazo_whatsapp_service.update_message_status(
                    message_id=message_id,
                    status=status
                )
                
                return {
                    'status': 'processed' if updated else 'not_found',
                    'message_id': message_id,
                    'new_status': status
                }
            
            return {'status': 'ignored', 'event_type': event_type}
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp event: {e}")
            return {'status': 'error', 'message': str(e)}


# Singleton instance
wazo_webhook_handler = WazoWebhookHandler()
