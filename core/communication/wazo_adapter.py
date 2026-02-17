"""
Wazo Platform Adapter for SalesCompass CRM

Provides integration with Wazo for:
- Voice calls (click-to-call, call logging)
- SMS messaging
- Voicemail management
- Call recordings
- Real-time call events

Wazo Platform Documentation: https://wazo-platform.org/documentation
"""
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import requests
from django.conf import settings
from django.utils import timezone

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
    """Represents a Wazo call."""
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


@dataclass
class WazoSMS:
    """Represents a Wazo SMS message."""
    message_id: str
    from_number: str
    to_number: str
    body: str
    status: str
    sent_at: Optional[datetime] = None


class WazoAPIClient:
    """
    Low-level Wazo API client.
    
    Handles authentication and HTTP requests to Wazo Platform.
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'WAZO_API_URL', None)
        self.api_key = getattr(settings, 'WAZO_API_KEY', None)
        self.tenant_uuid = getattr(settings, 'WAZO_TENANT_UUID', None)
        self._session = None
    
    def is_configured(self) -> bool:
        """Check if Wazo is properly configured."""
        return bool(self.base_url and self.api_key)
    
    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'X-Auth-Token': self.api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            })
            if self.tenant_uuid:
                self._session.headers['Wazo-Tenant'] = self.tenant_uuid
        return self._session
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Wazo API."""
        if not self.is_configured():
            raise WazoNotConfiguredError("Wazo API is not configured")
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Wazo API error: {e}")
            raise WazoAPIError(str(e))
    
    def get(self, endpoint: str, **kwargs) -> Dict:
        """GET request to Wazo API."""
        return self._request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, data: Dict = None, **kwargs) -> Dict:
        """POST request to Wazo API."""
        return self._request('POST', endpoint, json=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict:
        """DELETE request to Wazo API."""
        return self._request('DELETE', endpoint, **kwargs)


class WazoNotConfiguredError(Exception):
    """Raised when Wazo is not configured."""
    pass


class WazoAPIError(Exception):
    """Raised when Wazo API request fails."""
    pass


class WazoCallService:
    """
    Wazo calling service for SalesCompass.
    
    Usage:
        from communication.wazo_adapter import wazo_call_service
        
        # Initiate a call
        call = wazo_call_service.initiate_call(
            from_extension='1001',
            to_number='+15551234567',
            user_id=123,
            tenant_id='tenant_abc'
        )
        
        # Get call status
        status = wazo_call_service.get_call_status(call.call_id)
    """
    
    def __init__(self):
        self.client = WazoAPIClient()
    
    def is_available(self) -> bool:
        """Check if calling service is available."""
        return self.client.is_configured()
    
    def initiate_call(
        self,
        from_extension: str,
        to_number: str,
        user_id: int = None,
        tenant_id: str = None,
        variables: Dict[str, str] = None
    ) -> Optional[WazoCall]:
        """
        Initiate an outbound call.
        
        Args:
            from_extension: User's extension number
            to_number: Destination phone number
            user_id: SalesCompass user ID (for logging)
            tenant_id: Tenant ID (for logging)
            variables: Additional call variables
        
        Returns:
            WazoCall object or None if failed
        """
        if not self.is_available():
            logger.warning("Wazo not configured, cannot initiate call")
            return None
        
        try:
            payload = {
                'source': {
                    'extension': from_extension,
                },
                'destination': {
                    'extension': to_number,
                },
                'variables': variables or {},
            }
            
            response = self.client.post('/api/calld/1.0/calls', data=payload)
            
            call = WazoCall(
                call_id=response.get('call_id'),
                direction=CallDirection.OUTBOUND,
                caller_id=from_extension,
                callee_id=to_number,
                status=CallStatus.INITIATED,
                started_at=timezone.now(),
                metadata={
                    'user_id': user_id,
                    'tenant_id': tenant_id,
                }
            )
            
            self._emit_call_event('call.initiated', call, tenant_id)
            
            return call
            
        except (WazoNotConfiguredError, WazoAPIError) as e:
            logger.error(f"Failed to initiate call: {e}")
            return None
    
    def get_call_status(self, call_id: str) -> Optional[WazoCall]:
        """Get current status of a call."""
        if not self.is_available():
            return None
        
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
            
        except (WazoNotConfiguredError, WazoAPIError) as e:
            logger.error(f"Failed to get call status: {e}")
            return None
    
    def hangup_call(self, call_id: str) -> bool:
        """Hangup an active call."""
        if not self.is_available():
            return False
        
        try:
            self.client.delete(f'/api/calld/1.0/calls/{call_id}')
            return True
        except (WazoNotConfiguredError, WazoAPIError) as e:
            logger.error(f"Failed to hangup call: {e}")
            return False
    
    def get_call_recordings(self, call_id: str) -> List[str]:
        """Get recording URLs for a call."""
        if not self.is_available():
            return []
        
        try:
            response = self.client.get(f'/api/call-logd/1.0/cdr/{call_id}/recordings')
            return [r.get('filename') for r in response.get('items', [])]
        except (WazoNotConfiguredError, WazoAPIError) as e:
            logger.error(f"Failed to get recordings: {e}")
            return []
    
    def log_call_to_crm(
        self,
        call: WazoCall,
        account_id: int = None,
        contact_id: int = None,
        lead_id: int = None,
        notes: str = ''
    ) -> Optional[int]:
        """
        Log a Wazo call to the CRM communication module.
        
        Returns the ID of the created Call record.
        """
        try:
            from communication.models import CallLog
            from tenants.models import Tenant
            
            outcome_map = {
                CallStatus.ANSWERED: 'answered',
                CallStatus.COMPLETED: 'completed',
                CallStatus.VOICEMAIL: 'voicemail',
                CallStatus.NO_ANSWER: 'no_answer',
                CallStatus.BUSY: 'busy',
                CallStatus.FAILED: 'failed',
            }
            
            tenant_id = call.metadata.get('tenant_id') if call.metadata else None
            tenant = None
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                except (Tenant.DoesNotExist, ValueError):
                    pass

            crm_call = CallLog.objects.create(
                tenant=tenant,
                user_id=call.metadata.get('user_id') if call.metadata else None,
                account_id=account_id,
                contact_id=contact_id,
                lead_id=lead_id,
                duration_seconds=call.duration if call.duration else 0,
                outcome=outcome_map.get(call.status, 'completed'),
                recording_url=call.recording_url or '',
                phone_number=call.callee_id if call.direction == CallDirection.OUTBOUND else call.caller_id,
                direction='outbound' if call.direction == CallDirection.OUTBOUND else 'inbound',
                call_type='outgoing' if call.direction == CallDirection.OUTBOUND else 'incoming',
                notes=notes,
                call_started_at=call.started_at or timezone.now(),
                call_ended_at=call.ended_at
            )
            
            return crm_call.id
            
        except Exception as e:
            logger.error(f"Failed to log call to CRM: {e}")
            return None
    
    def _emit_call_event(self, event_type: str, call: WazoCall, tenant_id: str = None) -> None:
        """Emit call event to the event bus."""
        try:
            from core.event_bus import emit
            
            emit(event_type, {
                'call_id': call.call_id,
                'direction': call.direction.value,
                'caller_id': call.caller_id,
                'callee_id': call.callee_id,
                'status': call.status.value,
                'duration': call.duration,
                'tenant_id': tenant_id,
            })
        except Exception as e:
            logger.debug(f"Failed to emit call event: {e}")


class WazoSMSService:
    """
    Wazo SMS service for SalesCompass.
    
    Usage:
        from communication.wazo_adapter import wazo_sms_service
        
        result = wazo_sms_service.send_sms(
            from_number='+15551234567',
            to_number='+15559876543',
            body='Hello from SalesCompass!'
        )
    """
    
    def __init__(self):
        self.client = WazoAPIClient()
    
    def is_available(self) -> bool:
        """Check if SMS service is available."""
        return self.client.is_configured()
    
    def send_sms(
        self,
        from_number: str,
        to_number: str,
        body: str,
        tenant_id: str = None
    ) -> Optional[WazoSMS]:
        """
        Send an SMS message.
        
        Args:
            from_number: Sender phone number
            to_number: Recipient phone number
            body: Message content
            tenant_id: Tenant ID for logging
        
        Returns:
            WazoSMS object or None if failed
        """
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
            
            sms = WazoSMS(
                message_id=response.get('id', ''),
                from_number=from_number,
                to_number=to_number,
                body=body,
                status='sent',
                sent_at=timezone.now(),
            )
            
            self._emit_sms_event('sms.sent', sms, tenant_id)
            
            return sms
            
        except (WazoNotConfiguredError, WazoAPIError) as e:
            logger.error(f"Failed to send SMS: {e}")
            return None
    
    def _emit_sms_event(self, event_type: str, sms: WazoSMS, tenant_id: str = None) -> None:
        """Emit SMS event to the event bus."""
        try:
            from core.event_bus import emit
            
            emit(event_type, {
                'message_id': sms.message_id,
                'from_number': sms.from_number,
                'to_number': sms.to_number,
                'tenant_id': tenant_id,
            })
        except Exception as e:
            logger.debug(f"Failed to emit SMS event: {e}")


wazo_api_client = WazoAPIClient()
wazo_call_service = WazoCallService()
wazo_sms_service = WazoSMSService()
