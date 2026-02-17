"""
Wazo API Views for SalesCompass CRM.
Provides endpoints for click-to-call, SMS, and webhook handling.
"""
import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .client import WazoAPIClient
from .voice import WazoVoiceService, wazo_voice_service
from .sms import WazoSMSService, wazo_sms_service
from .webhooks import wazo_webhook_handler
from .models import WazoCallLog, WazoSMSLog, WazoExtension

logger = logging.getLogger(__name__)


class WazoStatusView(LoginRequiredMixin, View):
    """
    Check Wazo connection status and user extension.
    GET /wazo/status/
    """
    
    def get(self, request):
        client = WazoAPIClient()
        user_extension = None
        
        try:
            ext = WazoExtension.objects.get(user=request.user, is_active=True)
            user_extension = ext.extension
        except WazoExtension.DoesNotExist:
            pass
        
        return JsonResponse({
            'connected': client.is_configured(),
            'user_extension': user_extension,
            'services': {
                'voice': wazo_voice_service.is_available(),
                'sms': wazo_sms_service.is_available(),
            }
        })


class InitiateCallView(LoginRequiredMixin, View):
    """
    Initiate an outbound call.
    POST /wazo/call/
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        to_number = data.get('to_number')
        if not to_number:
            return JsonResponse({'error': 'to_number is required'}, status=400)
        
        # Get user's extension
        try:
            ext = WazoExtension.objects.get(user=request.user, is_active=True)
            from_extension = ext.extension
        except WazoExtension.DoesNotExist:
            return JsonResponse({'error': 'No extension configured for user'}, status=400)
        
        # Initiate call
        call = wazo_voice_service.initiate_call(from_extension, to_number)
        
        if call:
            # Log the call
            call_log = WazoCallLog.objects.create(
                tenant=request.user.tenant if hasattr(request.user, 'tenant') else None,
                call_id=call.call_id,
                direction='outbound',
                from_number=from_extension,
                to_number=to_number,
                status='initiated',
                started_at=timezone.now(),
                user=request.user,
            )
            
            # Try to link to CRM entities from request
            if data.get('contact_id'):
                from accounts.models import Contact
                try:
                    call_log.contact = Contact.objects.get(id=data['contact_id'])
                    call_log.save()
                except Contact.DoesNotExist:
                    pass
            
            if data.get('lead_id'):
                from leads.models import Lead
                try:
                    call_log.lead = Lead.objects.get(id=data['lead_id'])
                    call_log.save()
                except Lead.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'call_id': call.call_id,
                'status': call.status.value,
            })
        else:
            return JsonResponse({'error': 'Failed to initiate call'}, status=500)


class HangupCallView(LoginRequiredMixin, View):
    """
    Hangup an active call.
    POST /wazo/call/<call_id>/hangup/
    """
    
    def post(self, request, call_id):
        success = wazo_voice_service.hangup_call(call_id)
        
        if success:
            # Update call log
            try:
                call_log = WazoCallLog.objects.get(call_id=call_id)
                call_log.status = 'completed'
                call_log.ended_at = timezone.now()
                call_log.save()
            except WazoCallLog.DoesNotExist:
                pass
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Failed to hangup call'}, status=500)


class SendSMSView(LoginRequiredMixin, View):
    """
    Send an SMS message.
    POST /wazo/sms/
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        to_number = data.get('to_number')
        body = data.get('body')
        
        if not to_number or not body:
            return JsonResponse({'error': 'to_number and body are required'}, status=400)
        
        # Get from number from user extension or settings
        try:
            ext = WazoExtension.objects.get(user=request.user, is_active=True)
            from_number = ext.caller_id or ext.extension
        except WazoExtension.DoesNotExist:
            from_number = getattr(settings, 'WAZO_DEFAULT_SMS_NUMBER', '')
        
        if not from_number:
            return JsonResponse({'error': 'No SMS sender configured'}, status=400)
        
        # Send SMS
        sms = wazo_sms_service.send_sms(from_number, to_number, body)
        
        if sms:
            # Log the SMS
            sms_log = WazoSMSLog.objects.create(
                tenant=request.user.tenant if hasattr(request.user, 'tenant') else None,
                message_id=sms.message_id,
                direction='outbound',
                from_number=from_number,
                to_number=to_number,
                body=body,
                status='sent',
                sent_at=timezone.now(),
                user=request.user,
            )
            
            # Link to CRM entities
            if data.get('contact_id'):
                from accounts.models import Contact
                try:
                    sms_log.contact = Contact.objects.get(id=data['contact_id'])
                    sms_log.save()
                except Contact.DoesNotExist:
                    pass
            
            if data.get('lead_id'):
                from leads.models import Lead
                try:
                    sms_log.lead = Lead.objects.get(id=data['lead_id'])
                    sms_log.save()
                except Lead.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'message_id': sms.message_id,
                'status': sms.status,
            })
        else:
            return JsonResponse({'error': 'Failed to send SMS'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class WazoWebhookView(View):
    """
    Receive webhooks from Wazo Platform.
    POST /wazo/webhooks/
    """
    
    def post(self, request):
        # Verify signature if configured
        signature = request.headers.get('X-Wazo-Signature', '')
        if not wazo_webhook_handler.verify_signature(request.body, signature):
            logger.warning("Invalid webhook signature")
            return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        event_type = data.get('name') or data.get('event_type', 'unknown')
        
        # Process the event
        result = wazo_webhook_handler.process_event(event_type, data)
        
        return JsonResponse(result)


class CallHistoryView(LoginRequiredMixin, View):
    """
    Get call history for current user.
    GET /wazo/calls/
    """
    
    def get(self, request):
        calls = WazoCallLog.objects.filter(user=request.user).order_by('-started_at')[:50]
        
        return JsonResponse({
            'calls': [
                {
                    'call_id': c.call_id,
                    'direction': c.direction,
                    'from_number': c.from_number,
                    'to_number': c.to_number,
                    'status': c.status,
                    'duration': c.duration,
                    'started_at': c.started_at.isoformat() if c.started_at else None,
                    'contact_id': c.contact_id,
                    'lead_id': c.lead_id,
                }
                for c in calls
            ]
        })


class SMSHistoryView(LoginRequiredMixin, View):
    """
    Get SMS history for current user.
    GET /wazo/sms/history/
    """
    
    def get(self, request):
        messages = WazoSMSLog.objects.filter(user=request.user).order_by('-sent_at')[:50]
        
        return JsonResponse({
            'messages': [
                {
                    'message_id': m.message_id,
                    'direction': m.direction,
                    'from_number': m.from_number,
                    'to_number': m.to_number,
                    'body': m.body,
                    'status': m.status,
                    'sent_at': m.sent_at.isoformat() if m.sent_at else None,
                    'contact_id': m.contact_id,
                    'lead_id': m.lead_id,
                }
                for m in messages
            ]
        })
