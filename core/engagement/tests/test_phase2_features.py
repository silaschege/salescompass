from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from engagement.models import (
    EngagementPlaybook, PlaybookStep, EngagementEvent, 
    EngagementWebhook, WebhookDeliveryLog, EngagementStatus, NextBestAction
)
from engagement.tasks import send_engagement_webhook
from engagement.automation_rules import check_churn_risk
from tenants.models import Tenant
from accounts.models import Account
from unittest.mock import patch
from datetime import timedelta

User = get_user_model()

class PlaybookTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.user = User.objects.create_user(username="testuser", password="password", tenant=self.tenant)
        
    def test_playbook_creation(self):
        playbook = EngagementPlaybook.objects.create(
            name="Onboarding",
            tenant_id=self.tenant.id,
            created_by=self.user
        )
        step1 = PlaybookStep.objects.create(
            playbook=playbook,
            day_offset=0,
            action_type='send_email',
            description="Welcome Email"
        )
        step2 = PlaybookStep.objects.create(
            playbook=playbook,
            day_offset=3,
            action_type='schedule_call',
            description="First check-in"
        )
        
        self.assertEqual(playbook.steps.count(), 2)
        self.assertEqual(playbook.steps.first().action_type, 'send_email')

class WebhookTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.webhook = EngagementWebhook.objects.create(
            name="Test Hook",
            url="http://example.com/hook",
            tenant_id=self.tenant.id
        )
        self.account = Account.objects.create(name="Test Account", tenant=self.tenant)
        self.event = EngagementEvent.objects.create(
            account=self.account,
            event_type='email_sent',
            title="Test Event",
            engagement_score=5.0
        )

    @patch('requests.post')
    def test_webhook_delivery_logging(self, mock_post):
        # Mock success
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"
        
        send_engagement_webhook(self.webhook.id, self.event.id)
        
        log = WebhookDeliveryLog.objects.first()
        self.assertIsNotNone(log)
        self.assertTrue(log.success)
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.event, self.event)

    @patch('requests.post')
    def test_webhook_retry_logic(self, mock_post):
        # Mock failure
        mock_post.return_value.status_code = 500
        mock_post.side_effect = Exception("Network Error")
        
        # We need to catch the retry exception from celery
        try:
            send_engagement_webhook(self.webhook.id, self.event.id)
        except Exception:
            pass # Expected retry exception
            
        log = WebhookDeliveryLog.objects.first()
        self.assertIsNotNone(log)
        self.assertFalse(log.success)
        self.assertIn("Network Error", log.error_message)

class ChurnRiskTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.account = Account.objects.create(name="Churn Risk Account", tenant=self.tenant)
        
    def test_churn_risk_inactivity(self):
        # Create status with old last_engaged
        EngagementStatus.objects.create(
            account=self.account,
            engagement_score=50,
            last_engaged_at=timezone.now() - timedelta(days=50) # > 45 days
        )
        
        check_churn_risk(self.account)
        
        nba = NextBestAction.objects.filter(account=self.account, priority='critical').first()
        self.assertIsNotNone(nba)
        self.assertIn("Churn Risk Alert", nba.description)
        self.assertEqual(nba.source, 'Churn Risk Detector')

    def test_churn_risk_low_score(self):
        # Create status with low score
        EngagementStatus.objects.create(
            account=self.account,
            engagement_score=10, # < 15
            last_engaged_at=timezone.now() - timedelta(days=5)
        )
        
        check_churn_risk(self.account)
        
        nba = NextBestAction.objects.filter(account=self.account, priority='high').first()
        self.assertIsNotNone(nba)
        self.assertIn("Engagement score critical", nba.description)
