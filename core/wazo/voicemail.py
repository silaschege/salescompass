"""
Voicemail Drop Service for SalesCompass CRM.
Allows pre-recorded voicemail messages to be dropped into recipient voicemail.
Uses Twilio's Answering Machine Detection (AMD) feature.
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from django.conf import settings
from .client import WazoAPIClient

logger = logging.getLogger(__name__)


@dataclass
class VoicemailDrop:
    """Represents a voicemail drop action."""
    drop_id: str
    to_number: str
    recording_url: str
    status: str
    duration: Optional[int] = None


class WazoVoicemailService:
    """
    Voicemail drop service for SalesCompass.
    
    Allows users to drop pre-recorded messages directly into voicemail
    without ringing the recipient's phone.
    
    Uses Twilio's AMD (Answering Machine Detection) to:
    1. Call the number
    2. Detect if it's a voicemail/machine
    3. Play the pre-recorded message
    4. Hang up
    """
    
    def __init__(self, client: Optional[WazoAPIClient] = None):
        self.client = client or WazoAPIClient()
    
    def is_available(self) -> bool:
        """Check if voicemail drop is available (Twilio configured)."""
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        return bool(account_sid and auth_token)
    
    def get_templates(self, tenant_id: str = None) -> List[Dict]:
        """Get available voicemail templates for a tenant."""
        from .models import VoicemailTemplate
        
        qs = VoicemailTemplate.objects.filter(is_active=True)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        
        return [
            {
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'duration': t.duration,
                'audio_url': t.audio_file.url if t.audio_file else t.audio_url,
            }
            for t in qs
        ]
    
    def drop_voicemail(
        self,
        to_number: str,
        template_id: int = None,
        audio_url: str = None,
        caller_id: str = None,
        user_id: int = None,
        tenant_id: str = None
    ) -> Optional[VoicemailDrop]:
        """
        Drop a voicemail to the specified number.
        
        Uses Twilio's AMD to detect voicemail and play the message.
        
        Args:
            to_number: Destination phone number
            template_id: ID of VoicemailTemplate to use (optional)
            audio_url: Direct URL to audio file (optional, used if no template_id)
            caller_id: Outbound caller ID (defaults to TWILIO_CALLER_ID)
            user_id: ID of the user initiating the drop
            tenant_id: Tenant ID for logging
            
        Returns:
            VoicemailDrop object with call SID and status
        """
        if not self.is_available():
            logger.warning("Twilio not configured for voicemail drop")
            return None
        
        # Get audio URL from template or use provided URL
        if template_id:
            from .models import VoicemailTemplate
            try:
                template = VoicemailTemplate.objects.get(id=template_id)
                audio_url = template.audio_file.url if template.audio_file else template.audio_url
            except VoicemailTemplate.DoesNotExist:
                logger.error(f"Voicemail template {template_id} not found")
                return None
        
        if not audio_url:
            logger.error("No audio URL provided for voicemail drop")
            return None
        
        try:
            from twilio.rest import Client as TwilioClient
            
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            
            client = TwilioClient(account_sid, auth_token)
            
            caller_id = caller_id or getattr(settings, 'TWILIO_CALLER_ID', '')
            base_url = getattr(settings, 'BASE_URL', 'https://crm.salescompass.io')
            
            # Create call with AMD enabled
            call = client.calls.create(
                to=to_number,
                from_=caller_id,
                url=f"{base_url}/wazo/voicemail-twiml/?audio={audio_url}",
                machine_detection='DetectMessageEnd',
                machine_detection_timeout=30,
                async_amd=True,
                async_amd_status_callback=f"{base_url}/wazo/voicemail-callback/"
            )
            
            # Log the drop
            self._log_voicemail_drop(
                call_sid=call.sid,
                to_number=to_number,
                audio_url=audio_url,
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            return VoicemailDrop(
                drop_id=call.sid,
                to_number=to_number,
                recording_url=audio_url,
                status='initiated'
            )
            
        except ImportError:
            logger.error("Twilio package not installed. Run: pip install twilio")
            return None
        except Exception as e:
            logger.error(f"Failed to drop voicemail: {e}")
            return None
    
    def _log_voicemail_drop(
        self,
        call_sid: str,
        to_number: str,
        audio_url: str,
        user_id: int = None,
        tenant_id: str = None
    ):
        """Log voicemail drop to the database."""
        try:
            from .models import WazoCallLog
            from django.utils import timezone
            
            WazoCallLog.objects.create(
                call_id=call_sid,
                direction='outbound',
                from_number=getattr(settings, 'TWILIO_CALLER_ID', ''),
                to_number=to_number,
                status='initiated',
                started_at=timezone.now(),
                notes=f"Voicemail drop: {audio_url}",
                tenant_id=tenant_id,
                user_id=user_id,
                wazo_data={
                    'type': 'voicemail_drop',
                    'audio_url': audio_url
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log voicemail drop: {e}")


# Singleton instance
wazo_voicemail_service = WazoVoicemailService()
