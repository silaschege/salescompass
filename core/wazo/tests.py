"""
Tests for Wazo Integration Module.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from .client import WazoAPIClient
from .voice import WazoVoiceService
from .sms import WazoSMSService
from .webhooks import WazoWebhookHandler
from .models import WazoCallLog, WazoSMSLog, WazoExtension


User = get_user_model()


class WazoClientTests(TestCase):
    """Tests for WazoAPIClient."""
    
    def test_client_not_configured(self):
        """Test client reports not configured when no settings."""
        with patch('wazo.client.settings') as mock_settings:
            mock_settings.WAZO_API_URL = None
            mock_settings.WAZO_API_KEY = None
            client = WazoAPIClient()
            self.assertFalse(client.is_configured())
    
    @patch('wazo.client.settings')
    def test_client_configured(self, mock_settings):
        """Test client reports configured when settings present."""
        mock_settings.WAZO_API_URL = 'http://localhost:9497'
        mock_settings.WAZO_API_KEY = 'test-token'
        mock_settings.WAZO_TENANT_UUID = None
        mock_settings.WAZO_CALLD_URL = None
        mock_settings.WAZO_CHATD_URL = None
        mock_settings.WAZO_CONFD_URL = None
        mock_settings.WAZO_AGENTD_URL = None
        mock_settings.WAZO_CALL_LOG_URL = None
        mock_settings.WAZO_WEBHOOKD_URL = None
        
        client = WazoAPIClient()
        self.assertTrue(client.is_configured())


class WazoVoiceServiceTests(TestCase):
    """Tests for WazoVoiceService."""
    
    @patch('wazo.voice.WazoAPIClient')
    def test_initiate_call_not_configured(self, MockClient):
        """Test call fails gracefully when not configured."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = False
        MockClient.return_value = mock_client
        
        service = WazoVoiceService(client=mock_client)
        result = service.initiate_call('1001', '+15551234567')
        
        self.assertIsNone(result)
    
    @patch('wazo.voice.WazoAPIClient')
    def test_initiate_call_success(self, MockClient):
        """Test successful call initiation."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.post.return_value = {'call_id': 'test-call-123'}
        MockClient.return_value = mock_client
        
        service = WazoVoiceService(client=mock_client)
        result = service.initiate_call('1001', '+15551234567')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.call_id, 'test-call-123')


class WazoSMSServiceTests(TestCase):
    """Tests for WazoSMSService."""
    
    @patch('wazo.sms.WazoAPIClient')
    def test_send_sms_not_configured(self, MockClient):
        """Test SMS fails gracefully when not configured."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = False
        MockClient.return_value = mock_client
        
        service = WazoSMSService(client=mock_client)
        result = service.send_sms('+15551234567', '+15559876543', 'Hello')
        
        self.assertIsNone(result)


class WazoWebhookTests(TestCase):
    """Tests for webhook handling."""
    
    def setUp(self):
        self.handler = WazoWebhookHandler()
    
    def test_process_call_created_event(self):
        """Test processing call_created webhook event."""
        event_data = {
            'call_id': 'test-call-456',
            'caller_id_number': '+15551234567',
            'peer_caller_id_number': '+15559876543',
            'is_caller': False,
        }
        
        result = self.handler.process_event('call_created', event_data)
        
        self.assertEqual(result['status'], 'processed')
        self.assertTrue(result['created'])
        
        # Verify call log was created
        call_log = WazoCallLog.objects.get(call_id='test-call-456')
        self.assertEqual(call_log.status, 'initiated')
    
    def test_process_unknown_event(self):
        """Test unknown events are ignored."""
        result = self.handler.process_event('unknown_event', {})
        
        self.assertEqual(result['status'], 'ignored')


class WazoModelTests(TestCase):
    """Tests for Wazo models."""
    
    def test_call_log_creation(self):
        """Test creating a CallLog entry."""
        call_log = WazoCallLog.objects.create(
            call_id='model-test-call',
            direction='outbound',
            from_number='1001',
            to_number='+15551234567',
            status='completed',
            duration=120,
            started_at=timezone.now(),
        )
        
        self.assertEqual(str(call_log), 'outbound: 1001 → +15551234567 (completed)')
    
    def test_sms_log_creation(self):
        """Test creating an SMSLog entry."""
        sms_log = WazoSMSLog.objects.create(
            message_id='model-test-sms',
            direction='outbound',
            from_number='+15551234567',
            to_number='+15559876543',
            body='Test message',
            status='sent',
            sent_at=timezone.now(),
        )
        
        self.assertEqual(str(sms_log), 'outbound: +15551234567 → +15559876543')


class WazoViewTests(TestCase):
    """Tests for Wazo views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_status_view_requires_auth(self):
        """Test status endpoint requires authentication."""
        response = self.client.get(reverse('wazo:status'))
        # Should redirect to login
        self.assertIn(response.status_code, [302, 403])
    
    def test_status_view_authenticated(self):
        """Test status endpoint when authenticated."""
        self.client.login(username='testuser', password='testpass123')
        
        with patch('wazo.views.WazoAPIClient') as MockClient:
            mock_client = MagicMock()
            mock_client.is_configured.return_value = False
            MockClient.return_value = mock_client
            
            response = self.client.get(reverse('wazo:status'))
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIn('connected', data)
    
    def test_webhook_accepts_post(self):
        """Test webhook endpoint accepts POST requests."""
        with patch('wazo.views.wazo_webhook_handler') as mock_handler:
            mock_handler.verify_signature.return_value = True
            mock_handler.process_event.return_value = {'status': 'ok'}
            
            response = self.client.post(
                reverse('wazo:webhooks'),
                data=json.dumps({'name': 'test_event'}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
