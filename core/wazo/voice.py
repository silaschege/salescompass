import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from django.utils import timezone
from .client import WazoAPIClient

logger = logging.getLogger(__name__)

class CallDirection(Enum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'

class CallStatus(Enum):
    INITIATED = 'initiated'
    RINGING = 'ringing'
    ANSWERED = 'answered'
    COMPLETED = 'completed'
    FAILED = 'failed'
    BUSY = 'busy'
    NO_ANSWER = 'no_answer'
    VOICEMAIL = 'voicemail'

@dataclass
class WazoCall:
    call_id: str
    direction: CallDirection
    caller_id: str
    callee_id: str
    status: CallStatus
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Optional[Dict] = None

class WazoVoiceService:
    """
    Wazo calling service for SalesCompass.
    """
    
    def __init__(self, client: Optional[WazoAPIClient] = None):
        self.client = client or WazoAPIClient()
    
    def is_available(self) -> bool:
        return self.client.is_configured()
    
    def initiate_call(
        self,
        from_extension: str,
        to_number: str,
        variables: Dict[str, str] = None
    ) -> Optional[WazoCall]:
        if not self.is_available():
            logger.warning("Wazo not configured, cannot initiate call")
            return None
        
        try:
            payload = {
                'source': {'extension': from_extension},
                'destination': {'extension': to_number},
                'variables': variables or {},
            }
            
            response = self.client.post('/api/calld/1.0/calls', data=payload)
            
            return WazoCall(
                call_id=response.get('call_id'),
                direction=CallDirection.OUTBOUND,
                caller_id=from_extension,
                callee_id=to_number,
                status=CallStatus.INITIATED,
                started_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to initiate call: {e}")
            return None
    
    def get_call_status(self, call_id: str) -> Optional[WazoCall]:
        if not self.is_available(): return None
        
        try:
            response = self.client.get(f'/api/calld/1.0/calls/{call_id}')
            
            status_map = {
                'up': CallStatus.ANSWERED,
                'ringing': CallStatus.RINGING,
                'down': CallStatus.COMPLETED,
            }
            
            return WazoCall(
                call_id=response.get('call_id'),
                direction=CallDirection(response.get('direction', 'outbound')),
                caller_id=response.get('caller_id_number', ''),
                callee_id=response.get('peer_caller_id_number', ''),
                status=status_map.get(response.get('status'), CallStatus.INITIATED),
                duration=response.get('talking_to_duration'),
            )
        except Exception as e:
            logger.error(f"Failed to get call status: {e}")
            return None
    
    def hangup_call(self, call_id: str) -> bool:
        if not self.is_available(): return False
        try:
            self.client.delete(f'/api/calld/1.0/calls/{call_id}')
            return True
        except Exception as e:
            logger.error(f"Failed to hangup call: {e}")
            return False
    
    def get_call_recordings(self, call_id: str) -> List[str]:
        if not self.is_available(): return []
        try:
            response = self.client.get(f'/api/call-logd/1.0/cdr/{call_id}/recordings')
            return [r.get('filename') for r in response.get('items', [])]
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
            return []

wazo_voice_service = WazoVoiceService()
