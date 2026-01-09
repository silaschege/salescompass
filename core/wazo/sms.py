import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from django.utils import timezone
from .client import WazoAPIClient

logger = logging.getLogger(__name__)

@dataclass
class WazoSMS:
    message_id: str
    from_number: str
    to_number: str
    body: str
    status: str
    sent_at: Optional[datetime] = None

class WazoSMSService:
    """
    Wazo SMS service for SalesCompass.
    """
    
    def __init__(self, client: Optional[WazoAPIClient] = None):
        self.client = client or WazoAPIClient()
    
    def is_available(self) -> bool:
        return self.client.is_configured()
    
    def send_sms(
        self,
        from_number: str,
        to_number: str,
        body: str
    ) -> Optional[WazoSMS]:
        if not self.is_available():
            logger.warning("Wazo not configured, cannot send SMS")
            return None
        
        try:
            payload = {
                'from': from_number,
                'to': to_number,
                'body': body,
            }
            
            response = self.client.post('/api/chatd/1.0/sms', data=payload)
            
            return WazoSMS(
                message_id=response.get('id', ''),
                from_number=from_number,
                to_number=to_number,
                body=body,
                status='sent',
                sent_at=timezone.now(),
            )
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return None

wazo_sms_service = WazoSMSService()
