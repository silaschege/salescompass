from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from core.models import User
from engagement.models import EngagementEvent
from engagement.services import DuplicateDetectionService, EventMergingService
from engagement.tasks import cleanup_old_engagement_events, auto_deduplicate_events
from accounts.models import Account, Contact

class EngagementDataGovernanceTest(TestCase):
    def setUp(self):
        self.tenant_id = 'test-tenant'
        self.user = User.objects.create_user(email='test@example.com', password='password', tenant_id=self.tenant_id)
        self.account = Account.objects.create(name='Test Account', tenant_id=self.tenant_id)
        self.contact = Contact.objects.create(first_name='John', last_name='Doe', account=self.account, tenant_id=self.tenant_id)

    def test_engagement_event_validation(self):
        """Test that event validation enforces entity linkage and score bounds."""
        from django.core.exceptions import ValidationError
        
        # Missing entity linkage
        event = EngagementEvent(
            account=self.user,
            event_type='email_opened',
            engagement_score=50,
            tenant_id=self.tenant_id
        )
        with self.assertRaises(ValidationError):
            event.full_clean()
            
        # Invalid score
        event.contact = self.contact
        event.engagement_score = 150
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_duplicate_detection_and_merging(self):
        """Test finding and merging duplicate events."""
        event1 = EngagementEvent.objects.create(
            account=self.user,
            contact=self.contact,
            event_type='email_opened',
            engagement_score=50,
            tenant_id=self.tenant_id
        )
        
        event2 = EngagementEvent.objects.create(
            account=self.user,
            contact=self.contact,
            event_type='email_opened',
            engagement_score=30,
            tenant_id=self.tenant_id
        )
        
        duplicates = DuplicateDetectionService.find_duplicates(event1)
        self.assertEqual(duplicates.count(), 1)
        self.assertEqual(duplicates.first(), event2)
        
        merged_event = EventMergingService.merge_events(event1, [event2])
        self.assertEqual(merged_event.engagement_score, 50)
        self.assertFalse(EngagementEvent.objects.filter(pk=event2.pk).exists())

    def test_cleanup_task(self):
        """Test that the cleanup task removes old unimportant events."""
        old_event = EngagementEvent.objects.create(
            account=self.user,
            contact=self.contact,
            event_type='link_clicked',
            engagement_score=10,
            tenant_id=self.tenant_id
        )
        # Manually backdate via queryset.update since auto_now_add is on created_at (if it were, but it's not)
        # Actually created_at is not auto_now_add in models.py (line 717 shows it's added manually in some places)
        # Wait, I should check created_at definition.
        EngagementEvent.objects.filter(pk=old_event.pk).update(created_at=timezone.now() - timedelta(days=400))
        
        important_old_event = EngagementEvent.objects.create(
            account=self.user,
            contact=self.contact,
            event_type='link_clicked',
            engagement_score=90,
            is_important=True,
            tenant_id=self.tenant_id
        )
        EngagementEvent.objects.filter(pk=important_old_event.pk).update(created_at=timezone.now() - timedelta(days=400))
        
        cleanup_old_engagement_events(days_older_than=365)
        
        self.assertFalse(EngagementEvent.objects.filter(pk=old_event.pk).exists())
        self.assertTrue(EngagementEvent.objects.filter(pk=important_old_event.pk).exists())
