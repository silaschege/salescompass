from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from core.models import User
from engagement.models import EngagementStatus, NextBestAction
from engagement.automation_rules import run_auto_nba_check

class AutoNBATest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test-nba@example.com', password='password')
        self.status = EngagementStatus.objects.create(account=self.user)

    def test_low_score_creates_nba(self):
        """Verify low engagement score triggers a check-in NBA."""
        self.status.engagement_score = 15.0 # Below 30 threshold
        self.status.save()
        
        run_auto_nba_check()
        
        nba_count = NextBestAction.objects.filter(
            account=self.user,
            action_type='check_in',
            source='Auto-Rule: Low Engagement'
        ).count()
        self.assertEqual(nba_count, 1)

    def test_inactivity_creates_nba(self):
        """Verify inactivity (>30 days) triggers a re-engagement email NBA."""
        self.status.last_engaged_at = timezone.now() - timedelta(days=35)
        self.status.save()
        
        run_auto_nba_check()
        
        nba_count = NextBestAction.objects.filter(
            account=self.user,
            action_type='send_email',
            source='Auto-Rule: Inactivity'
        ).count()
        self.assertEqual(nba_count, 1)

    def test_no_duplicate_nba(self):
        """Verify rules don't create duplicate NBAs if one is already open."""
        self.status.engagement_score = 10.0
        self.status.save()
        
        # Run once
        run_auto_nba_check()
        self.assertEqual(NextBestAction.objects.count(), 1)
        
        # Run again
        run_auto_nba_check()
        self.assertEqual(NextBestAction.objects.count(), 1)
