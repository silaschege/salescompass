"""
Tests for WhatsApp Integration Module.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from .whatsapp import WazoWhatsAppService, WhatsAppMessageResult


User = get_user_model()


class WazoWhatsAppServiceTests(TestCase):
    """Tests for WazoWhatsAppService."""
    
    def setUp(self):
        self.mock_client = MagicMock()
        self.service = WazoWhatsAppService(client=self.mock_client)
    
    def test_service_not_available_when_not_configured(self):
        """Test service reports not available when client not configured."""
        self.mock_client.is_configured.return_value = False
        
        self.assertFalse(self.service.is_available())
    
    def test_service_available_when_configured(self):
        """Test service reports available when client configured."""
        self.mock_client.is_configured.return_value = True
        
        self.assertTrue(self.service.is_available())
    
    def test_send_message_not_available(self):
        """Test send_message returns None when service not available."""
        self.mock_client.is_configured.return_value = False
        
        result = self.service.send_message(
            from_number='+1234567890',
            to_number='+0987654321',
            body='Hello World'
        )
        
        self.assertIsNone(result)
    
    def test_send_message_success(self):
        """Test successful message sending."""
        self.mock_client.is_configured.return_value = True
        self.mock_client.post.return_value = {'id': 'wamid.test123'}
        
        result = self.service.send_message(
            from_number='+1234567890',
            to_number='+0987654321',
            body='Hello World'
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, WhatsAppMessageResult)
        self.assertEqual(result.message_id, 'wamid.test123')
        self.assertEqual(result.status, 'sent')
        self.assertEqual(result.body, 'Hello World')
    
    def test_send_message_with_exception(self):
        """Test message sending handles exceptions."""
        self.mock_client.is_configured.return_value = True
        self.mock_client.post.side_effect = Exception("API Error")
        
        result = self.service.send_message(
            from_number='+1234567890',
            to_number='+0987654321',
            body='Hello World'
        )
        
        self.assertIsNone(result)
    
    def test_send_template_message_success(self):
        """Test successful template message sending."""
        self.mock_client.is_configured.return_value = True
        self.mock_client.post.return_value = {'id': 'wamid.tpl123'}
        
        result = self.service.send_template_message(
            from_number='+1234567890',
            to_number='+0987654321',
            template_name='hello_world',
            template_variables=['John']
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.message_id, 'wamid.tpl123')
        self.assertEqual(result.message_type, 'template')
        self.assertIn('hello_world', result.body)
    
    def test_get_tenant_numbers_fallback(self):
        """Test fallback to mock numbers when config not found."""
        numbers = self.service.get_tenant_numbers('nonexistent-tenant')
        
        self.assertIsInstance(numbers, list)
        self.assertTrue(len(numbers) > 0)


class WhatsAppWebhookTests(TestCase):
    """Tests for WhatsApp webhook handling."""
    
    def setUp(self):
        from .webhooks import WazoWebhookHandler
        self.handler = WazoWebhookHandler()
    
    def test_process_whatsapp_message_received(self):
        """Test processing inbound WhatsApp message event."""
        event_data = {
            'message_id': 'wamid.inbound123',
            'from': '+1234567890',
            'to': '+0987654321',
            'body': 'Hello from customer',
            'type': 'text',
            'tenant_id': 'test-tenant'
        }
        
        with patch('wazo.whatsapp.wazo_whatsapp_service.receive_message') as mock_receive:
            mock_message = MagicMock()
            mock_message.message_id = 'wamid.inbound123'
            mock_receive.return_value = mock_message
            
            result = self.handler.process_event('whatsapp_message_received', event_data)
            
            self.assertEqual(result['status'], 'processed')
            self.assertTrue(result['created'])
    
    def test_process_whatsapp_status_update(self):
        """Test processing WhatsApp status update event."""
        event_data = {
            'message_id': 'wamid.test456',
            'status': 'delivered'
        }
        
        with patch('wazo.whatsapp.wazo_whatsapp_service.update_message_status') as mock_update:
            mock_update.return_value = True
            
            result = self.handler.process_event('whatsapp_message_delivered', event_data)
            
            self.assertEqual(result['status'], 'processed')
            self.assertEqual(result['new_status'], 'delivered')
    
    def test_whatsapp_events_in_handler_list(self):
        """Test that WhatsApp events are registered in handler."""
        self.assertIn('whatsapp_message_received', self.handler.WHATSAPP_EVENTS)
        self.assertIn('whatsapp_message_status', self.handler.WHATSAPP_EVENTS)
        self.assertIn('whatsapp_message_delivered', self.handler.WHATSAPP_EVENTS)
        self.assertIn('whatsapp_message_read', self.handler.WHATSAPP_EVENTS)


class WhatsAppMessageResultTests(TestCase):
    """Tests for WhatsAppMessageResult dataclass."""
    
    def test_create_message_result(self):
        """Test creating a WhatsAppMessageResult."""
        result = WhatsAppMessageResult(
            message_id='test123',
            from_number='+1234567890',
            to_number='+0987654321',
            body='Test message',
            status='sent'
        )
        
        self.assertEqual(result.message_id, 'test123')
        self.assertEqual(result.status, 'sent')
        self.assertEqual(result.message_type, 'text')
        self.assertIsNone(result.sent_at)
    
    def test_message_result_with_all_fields(self):
        """Test creating a WhatsAppMessageResult with all fields."""
        now = timezone.now()
        result = WhatsAppMessageResult(
            message_id='test456',
            from_number='+1234567890',
            to_number='+0987654321',
            body='Template message',
            status='sent',
            message_type='template',
            sent_at=now,
            metadata={'template_name': 'hello_world'}
        )
        
        self.assertEqual(result.message_type, 'template')
        self.assertEqual(result.sent_at, now)
        self.assertIn('template_name', result.metadata)
