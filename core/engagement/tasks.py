from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import EngagementEvent
from .services import DuplicateDetectionService, EventMergingService

@shared_task
def cleanup_old_engagement_events(days_older_than=365):
    """
    Deletes engagement events older than a certain number of days,
    unless they are marked as important.
    """
    cutoff_date = timezone.now() - timedelta(days=days_older_than)
    deleted_count, _ = EngagementEvent.objects.filter(
        created_at__lt=cutoff_date,
        is_important=False
    ).delete()
    return f"Deleted {deleted_count} old engagement events."

@shared_task
def auto_deduplicate_events():
    """
    Identifies and merges duplicate events across the entire system.
    This is intended to be run as a periodic background job.
    """
    # Simply find events from the last 24 hours and check for duplicates
    recent_events = EngagementEvent.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    )
    
    merged_total = 0
    processed_ids = set()
    
    for event in recent_events:
        if event.pk in processed_ids:
            continue
            
        duplicates = DuplicateDetectionService.find_duplicates(event)
        if duplicates.exists():
            EventMergingService.merge_events(event, duplicates)
            merged_total += duplicates.count()
            for d in duplicates:
                processed_ids.add(d.pk)
        
        processed_ids.add(event.pk)
        
    return f"Auto-deduplication complete. Merged {merged_total} events."
