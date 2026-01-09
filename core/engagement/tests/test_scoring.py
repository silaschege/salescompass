from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from core.models import User
from tenants.models import Tenant
from engagement.models import EngagementEvent, EngagementStatus, EngagementScoringConfig, ScoringRule
from engagement.utils import calculate_engagement_score

class EngagementScoringTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.user.tenant = self.tenant
        self.user.save()
        self.tenant_id = str(self.tenant.id)
        self.status = EngagementStatus.objects.create(account=self.user)
        # Create default config for tenant
        self.config = EngagementScoringConfig.objects.create(
            tenant_id=self.tenant_id,
            decay_rate=0.1, # 10% decay
            decay_period_days=5,
            inactivity_threshold_days=10
        )

    def test_calculate_base_score_with_custom_weights(self):
        """Verify dynamic weights from ScoringRule are applied."""
        ScoringRule.objects.create(
            tenant_id=self.tenant_id,
            event_type='proposal_viewed',
            weight=10.0
        )
        
        EngagementEvent.objects.create(
            account=self.user,
            tenant_id=self.tenant_id,
            event_type='proposal_viewed',
            title='Test Event',
            engagement_score=0.0
        )
        
        score = calculate_engagement_score(self.user, tenant_id=self.tenant_id)
        # Base logic: 10 (weight) + 0 (event score * 0.1) = 10
        self.assertEqual(score, 10.0)

    def test_dynamic_decay_application(self):
        """Verify dynamic decay settings are applied."""
        today = timezone.now()
        # threshold 10, period 5. 20 days inactive -> (20-10)/5 = 2 periods.
        last_active = today - timedelta(days=20)
        
        self.status.last_engaged_at = last_active
        self.status.save()
        
        EngagementEvent.objects.create(
            account=self.user,
            tenant_id=self.tenant_id,
            event_type='demo_completed', # Default weight 10
            title='Old Demo',
            created_at=today - timedelta(days=19),
            engagement_score=0
        )
        
        score = calculate_engagement_score(self.user, tenant_id=self.tenant_id)
        
        # Expected: 10 * (1 - 0.1)^2 = 10 * 0.81 = 8.1
        self.assertEqual(score, 8.1)
