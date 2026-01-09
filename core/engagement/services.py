from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import EngagementEvent

class DuplicateDetectionService:
    @staticmethod
    def find_duplicates(event, window_minutes=10):
        """
        Finds potential duplicates for a given event within a time window.
        A duplicate is defined as an event with the same type, tenant, and primary entity (contact/lead/account).
        """
        start_time = event.created_at - timedelta(minutes=window_minutes) if event.pk else timezone.now() - timedelta(minutes=window_minutes)
        
        query = EngagementEvent.objects.filter(
            event_type=event.event_type,
            tenant_id=event.tenant_id,
            created_at__gte=start_time
        ).exclude(pk=event.pk)
        
        if event.contact_id:
            query = query.filter(contact_id=event.contact_id)
        elif event.lead_id:
            query = query.filter(lead_id=event.lead_id)
        elif event.account_company_id:
            query = query.filter(account_company_id=event.account_company_id)
        else:
            return EngagementEvent.objects.none()
            
        return query

class EventMergingService:
    @staticmethod
    def merge_events(primary_event, secondary_events):
        """
        Merges secondary events into the primary event.
        Aggregates scores and metadata.
        """
        if not secondary_events:
            return primary_event
            
        for event in secondary_events:
            # Aggregate score (simple max for now, can be changed based on business rules)
            primary_event.engagement_score = max(primary_event.engagement_score, event.engagement_score)
            
            # Merge metadata
            if event.metadata:
                primary_event.metadata.update(event.metadata)
            
            # Append internal notes
            if event.internal_notes:
                primary_event.internal_notes += f"\nMerged from event {event.pk}: {event.internal_notes}"
            
            # Mark primary as important if any secondary was
            if event.is_important:
                primary_event.is_important = True
                
            event.delete()
            
        primary_event.save()
        return primary_event
