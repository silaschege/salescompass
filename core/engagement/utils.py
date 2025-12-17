from django.utils import timezone
from datetime import timedelta
from .models import EngagementEvent, EngagementStatus

# Decay configuration
# Reduce score by DECAY_RATE percent for every DECAY_PERIOD_DAYS of inactivity
DECAY_RATE = 0.05  # 5% decay
DECAY_PERIOD_DAYS = 7
INACTIVITY_THRESHOLD_DAYS = 14

def calculate_engagement_score(account):
    """
    Recalculate the engagement score for a given account.
    Considers recent events and applies time-based decay.
    """
    # 1. Base Score from recent events (last 30 days)
    cutoff_date = timezone.now() - timedelta(days=30)
    events = EngagementEvent.objects.filter(
        account=account,
        created_at__gte=cutoff_date
    )
    
    # Simple scoring logic based on event types (could be moved to a config model)
    # This is an example; real scores would come from event_type weights
    SCORE_MAP = {
        'email_opened': 1,
        'link_clicked': 2,
        'proposal_viewed': 5,
        'demo_completed': 10,
        'content_downloaded': 3,
    }
    
    base_score = 0
    for event in events:
        base_score += SCORE_MAP.get(event.event_type, 1) + event.engagement_score
        
    # Cap base score at 100 for normalization
    final_score = min(base_score, 100.0)
    
    # 2. Apply Decay if inactive
    status, created = EngagementStatus.objects.get_or_create(account=account)
    
    last_activity = status.last_engaged_at
    if not last_activity:
        # If no activity recorded, try to find latest event
        latest_event = EngagementEvent.objects.filter(account=account).order_by('-created_at').first()
        if latest_event:
            last_activity = latest_event.created_at
            status.last_engaged_at = last_activity
            status.save()
            
    if last_activity:
        days_inactive = (timezone.now() - last_activity).days
        
        if days_inactive > INACTIVITY_THRESHOLD_DAYS:
            # Calculate how many decay periods have passed
            decay_periods = (days_inactive - INACTIVITY_THRESHOLD_DAYS) // DECAY_PERIOD_DAYS
            
            # Apply decay: Score * (1 - Rate)^Periods
            # We apply this to the calculated base score effectively dampening it
            if decay_periods > 0:
                decay_factor = (1 - DECAY_RATE) ** decay_periods
                final_score = final_score * decay_factor
                
    return round(final_score, 2)

def apply_decay_to_all_accounts():
    """
    Batch process to update engagement scores with decay.
    Should be run via Celery task.
    """
    # Iterate through all engagement statuses
    # In a real system, we'd batch this query
    for status in EngagementStatus.objects.all():
        new_score = calculate_engagement_score(status.account)
        
        status.engagement_score = new_score
        status.last_decay_calculation = timezone.now()
        status.save()

def get_best_engagement_time(account):
    """
    Analyze past successful engagement events to determine the optimal time to contact.
    Returns a string like "Tuesday at 10 AM" or None.
    """
    from django.db.models.functions import ExtractWeekDay, ExtractHour
    from django.db.models import Count
    from .models import EngagementEvent
    
    # Filter for "successful" interactions initiated by the user or client
    # e.g., emails opened, calls scheduled/completed, meetings
    relevant_types = [
        'email_opened', 'link_clicked', 'lead_contacted', 
        'demo_completed', 'webinar_attended'
    ]
    
    events = EngagementEvent.objects.filter(
        # Let's assume for now I can filter by `contact__account=account`.
        contact__account=account,
        event_type__in=relevant_types
    ).annotate(
        weekday=ExtractWeekDay('created_at'),
        hour=ExtractHour('created_at')
    ).values('weekday', 'hour').annotate(count=Count('id')).order_by('-count')
    
    if not events.exists():
        return None
        
    top_time = events.first()
    
    # Weekday: 1=Sunday, 2=Monday, ... 7=Saturday (Django default)
    days = {1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday', 5: 'Thursday', 6: 'Friday', 7: 'Saturday'}
    day_name = days.get(top_time['weekday'], 'Unknown')
    
    # Hour: 0-23
    hour = top_time['hour']
    am_pm = 'AM' if hour < 12 else 'PM'
    hour_12 = hour if hour <= 12 else hour - 12
    hour_12 = 12 if hour_12 == 0 else hour_12
    
    return f"{day_name}s at {hour_12} {am_pm}"
