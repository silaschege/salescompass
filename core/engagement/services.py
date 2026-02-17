from .models import SocialInteraction
from leads.models import Lead
from accounts.models import Contact

class SocialListenerService:
    """
    Service to process incoming social media events.
    """
    
    @staticmethod
    def process_incoming_interaction(data, tenant):
        """
        Ingests data from a social webhook and tries to match it to a user.
        """
        external_id = data.get('id')
        platform = data.get('platform')
        handle = data.get('author_handle')
        
        # Avoid duplicates
        if SocialInteraction.objects.filter(platform=platform, external_id=external_id).exists():
            return None
            
        interaction = SocialInteraction.objects.create(
            tenant=tenant,
            platform=platform,
            interaction_type=data.get('type'),
            external_id=external_id,
            author_handle=handle,
            author_name=data.get('author_name', ''),
            content=data.get('content', '')
        )
        
        # Basic matching logic (can be expanded)
        # Try to match by social handle in lead or contact metadata if exists
        # For now, let's assume we search leads for the handle in description or custom fields
        # (In a real system, we'd have a SocialProfile model)
        
        matched_lead = Lead.objects.filter(tenant=tenant).filter(
            description__icontains=handle
        ).first()
        
        if matched_lead:
            interaction.lead = matched_lead
            interaction.save()
            interaction.trigger_engagement_event()
            
        return interaction

class DuplicateDetectionService:
    """
    Service to identify duplicate engagement events.
    """
    @staticmethod
    def is_duplicate(event_data, tenant):
        # Basic implementation to prevent immediate errors
        return False

class EventMergingService:
    """
    Service to merge related engagement activities.
    """
    @staticmethod
    def merge_events(primary_event, related_events):
        # Basic implementation to prevent immediate errors
        return primary_event
