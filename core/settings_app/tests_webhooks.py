from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock
from developer.models import Webhook
from leads.models import Lead, LeadSource
from opportunities.models import Opportunity, OpportunityStage
from accounts.models import Account
from .tasks import trigger_webhook

User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class WebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='webhookuser',
            email='webhook@example.com',
            password='password123',
            tenant_id='tenant1'
        )
        
        self.webhook = Webhook.objects.create(
            name='Test Webhook',
            url='https://example.com/webhook',
            events=['lead.created', 'opportunity.won', 'opportunity.created'],
            secret='test_secret',
            tenant_id='tenant1',
            is_active=True
        )
        
        self.source = LeadSource.objects.create(name='web', label='Web', tenant_id='tenant1')
        self.account = Account.objects.create(name='Test Account', tenant_id='tenant1')
        self.stage_won = OpportunityStage.objects.create(
            name='closed_won', 
            is_won=True, 
            tenant_id='tenant1'
        )

    @patch('settings_app.tasks.deliver_webhook.delay')
    def test_lead_signal_triggers_webhook(self, mock_delay):
        """Test that creating a lead triggers the webhook task."""
        # Mock the return value of delay to avoid errors if accessed
        mock_delay.return_value = MagicMock(id='task_123')
        
        Lead.objects.create(
            first_name='Test',
            last_name='Lead',
            email='test@example.com',
            source_ref=self.source,
            tenant_id='tenant1',
            owner=self.user
        )
        
        # The signal calls trigger_webhook.delay, which executes trigger_webhook (if eager)
        # trigger_webhook then calls deliver_webhook.delay
        # Since we are patching deliver_webhook.delay, we expect it to be called
        
        # NOTE: If CELERY_TASK_ALWAYS_EAGER is True, trigger_webhook runs immediately
        # and calls deliver_webhook.delay.
        mock_delay.assert_called_once()
        args = mock_delay.call_args[0]
        self.assertEqual(args[0], self.webhook.id)
        self.assertEqual(args[1], 'lead.created')
        self.assertEqual(args[2]['email'], 'test@example.com')

    @patch('settings_app.tasks.deliver_webhook.delay')
    def test_opportunity_won_signal(self, mock_delay):
        """Test that winning an opportunity triggers the webhook."""
        mock_delay.return_value = MagicMock(id='task_123')
        
        opp = Opportunity.objects.create(
            name='Test Opp',
            amount=1000,
            stage=self.stage_won,
            account=self.account,
            tenant_id='tenant1',
            owner=self.user,
            close_date='2023-01-01'
        )
        
        # Should trigger opportunity.created first
        mock_delay.assert_called()
        args = mock_delay.call_args[0]
        self.assertEqual(args[1], 'opportunity.created')
        
        # Reset mock
        mock_delay.reset_mock()
        
        # Update to won
        # First move to non-won
        stage_open = OpportunityStage.objects.create(name='open', tenant_id='tenant1')
        opp.stage = stage_open
        opp.save()
        
        # Reset mock again (update might trigger opportunity.updated)
        mock_delay.reset_mock()
        
        # Update to won
        opp.stage = self.stage_won
        opp.save()
        
        mock_delay.assert_called()
        args = mock_delay.call_args[0]
        self.assertEqual(args[1], 'opportunity.won')

    @patch('requests.post')
    def test_deliver_webhook_success(self, mock_post):
        """Test successful execution of deliver_webhook task."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        from .tasks import deliver_webhook
        import hmac
        import hashlib
        import json
        
        # Call the task directly (synchronously)
        payload = {'id': 1, 'name': 'Test'}
        result = deliver_webhook(self.webhook.id, 'lead.created', payload)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['webhook_id'], self.webhook.id)
        
        # Verify stats updated
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.success_count, 1)
        self.assertIsNotNone(self.webhook.last_triggered)
        
        # Verify request headers (HMAC)
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        headers = call_kwargs['headers']
        self.assertIn('X-SalesCompass-Signature', headers)
        self.assertIn('X-SalesCompass-Event', headers)
        self.assertEqual(headers['X-SalesCompass-Event'], 'lead.created')
        
        # Verify signature value
        # We need to reconstruct the exact JSON payload used in the task
        # The task adds a timestamp, so we can't easily replicate the exact string unless we mock timezone
        # OR we can inspect the data passed to requests.post
        
        sent_data = call_kwargs['data']
        expected_signature = hmac.new(
            self.webhook.secret.encode(),
            sent_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        self.assertEqual(headers['X-SalesCompass-Signature'], expected_signature)

    @patch('requests.post')
    def test_deliver_webhook_failure_retry(self, mock_post):
        """Test handling of failed webhook delivery with retry."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        from .tasks import deliver_webhook
        
        payload = {'id': 1}
        
        # We need to mock self.retry to avoid actual retry logic during test
        # or we can catch the retry exception if we want to verify it raises Retry
        with patch('settings_app.tasks.deliver_webhook.retry') as mock_retry:
            mock_retry.side_effect = Exception('Retry called')
            
            try:
                deliver_webhook(self.webhook.id, 'lead.created', payload)
            except Exception as e:
                self.assertEqual(str(e), 'Retry called')
            
            mock_retry.assert_called()

    def test_no_webhook_found(self):
        """Test that no tasks are queued if no matching webhook exists."""
        from .tasks import trigger_webhook
        
        # 'case.created' is not in our webhook's events list
        task_ids = trigger_webhook('case.created', {}, 'tenant1')
        self.assertEqual(task_ids, [])
