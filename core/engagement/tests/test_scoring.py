from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from core.models import User
from engagement.models import EngagementEvent, EngagementStatus
from engagement.utils import calculate_engagement_score

class EngagementScoringTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password')
        self.status = EngagementStatus.objects.create(account=self.user)

    def test_calculate_base_score(self):
        """Verify recent events increase score."""
        EngagementEvent.objects.create(
            account=self.user,
            event_type='proposal_viewed', # Worth 5
            title='Test Event',
            engagement_score=5.0
        )
        
        score = calculate_engagement_score(self.user)
        # Base logic: 5 (from map) + 5 (from event) = 10
        self.assertEqual(score, 10.0)

    def test_decay_application(self):
        """Verify score decreases after inactivity."""
        # 1. Create an old event (30 days ago - borderline for base calculation, 
        # but let's assume we set activity date manually to trigger decay)
        
        # Manually set last engaged to 3 weeks ago (21 days)
        # Threshold is 14 days. 21 - 14 = 7 days = 1 decay period.
        # Decay rate is 0.05.
        
        today = timezone.now()
        last_active = today - timedelta(days=21)
        
        self.status.last_engaged_at = last_active
        self.status.save()
        
        # Create an event JUST within the 30 day window so base score > 0
        event_time = today - timedelta(days=21)
        EngagementEvent.objects.create(
            account=self.user,
            event_type='demo_completed', # Worth 10
            title='Old Demo',
            created_at=event_time,
            engagement_score=10.0
        )
        # Base score should be 10 (map) + 10 (event) = 20.
        
        score = calculate_engagement_score(self.user)
        
        # Exptected: 20 * (1 - 0.05)^1 = 19.0
        self.assertEqual(score, 19.0)

    def test_multiple_decay_periods(self):
        """Verify score decreases more for longer inactivity."""
        # 30 days inactive.
        # Threshold 14. 30 - 14 = 16 days. 16 // 7 = 2 periods.
        
        today = timezone.now()
        last_active = today - timedelta(days=30)
        
        self.status.last_engaged_at = last_active
        self.status.save()
        
        # Event 29 days ago (still in window)
        event_time = today - timedelta(days=29)
        EngagementEvent.objects.create(
            account=self.user,
            event_type='demo_completed',
            title='Old Demo',
            created_at=event_time,
            engagement_score=10.0
        ) # Base 20
        
        score = calculate_engagement_score(self.user)
        
        # Expected: 20 * (0.95)^2 = 20 * 0.9025 = 18.05
        self.assertEqual(score, 18.05)
