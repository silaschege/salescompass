from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import CampaignRecipient, Unsubscribe, MarketingCampaign, LandingPage
from django.utils import timezone

def send_campaign_email(campaign_id: int, recipient_id: int) -> bool:
    """Send email to a campaign recipient."""
    recipient = CampaignRecipient.objects.get(id=recipient_id)
    
    # Check unsubscribe
    if Unsubscribe.objects.filter(email=recipient.email).exists():
        recipient.status = 'unsubscribed'
        recipient.save(update_fields=['status'])
        return False
    
    # Get email content
    campaign = recipient.campaign
    email_campaign = campaign.email_campaigns.first()
    template = email_campaign.email_template
    
    # Render with personalization
    context = {
        'recipient': recipient,
        'campaign': campaign,
        'unsubscribe_url': f"https://salescompass.com/marketing/unsubscribe/{recipient.id}/"
    }
    html_content = render_to_string('marketing/email_wrapper.html', {
        'content': template.html_content,
        'context': context
    })
    
    # Send email
    try:
        send_mail(
            subject=template.subject,
            message=template.plain_text_content,
            html_message=html_content,
            from_email=email_campaign.from_email,
            recipient_list=[recipient.email]
        )
        recipient.status = 'sent'
        recipient.sent_at = timezone.now()
        recipient.save(update_fields=['status', 'sent_at'])
        return True
    except Exception as e:
        recipient.status = 'bounced'
        recipient.save(update_fields=['status'])
        return False


def track_email_open_event(recipient_id):
    """Track email open event and update lead scoring."""
    try:
        recipient = CampaignRecipient.objects.get(id=recipient_id)
        
        # Update recipient status
        if recipient.status == 'sent':
            recipient.status = 'opened'
            recipient.opened_at = timezone.now()
            recipient.save(update_fields=['status', 'opened_at'])
            
            # Update campaign analytics
            campaign = recipient.campaign
            campaign.total_opened = CampaignRecipient.objects.filter(
                campaign=campaign, 
                status__in=['opened', 'clicked']
            ).count()
            campaign.save(update_fields=['total_opened'])
            
            # Update lead score if lead exists
            if recipient.account and hasattr(recipient.account, 'leads'):
                from leads.services import LeadScoringService
                # Find lead associated with this account and email
                lead = recipient.account.leads.filter(email=recipient.email).first()
                if lead:
                    LeadScoringService.update_lead_score(lead.id, 5, "Email opened")
                    
        return True
        
    except CampaignRecipient.DoesNotExist:
        return False


def track_link_click_event(recipient_id, url):
    """Track link click event and update lead scoring."""
    try:
        recipient = CampaignRecipient.objects.get(id=recipient_id)
        
        # Update recipient status
        if recipient.status in ['sent', 'opened']:
            recipient.status = 'clicked'
            recipient.clicked_at = timezone.now()
            recipient.save(update_fields=['status', 'clicked_at'])
            
            # Update campaign analytics
            campaign = recipient.campaign
            campaign.total_clicked = CampaignRecipient.objects.filter(
                campaign=campaign, 
                status='clicked'
            ).count()
            campaign.save(update_fields=['total_clicked'])
            
            # Update lead score if lead exists
            if recipient.account and hasattr(recipient.account, 'leads'):
                from leads.services import LeadScoringService
                lead = recipient.account.leads.filter(email=recipient.email).first()
                if lead:
                    LeadScoringService.update_lead_score(lead.id, 10, "Link clicked")
                    
        return url
        
    except CampaignRecipient.DoesNotExist:
        return url


def track_landing_page_visit_event(landing_page_id, lead_id):
    """Track landing page visit and update lead scoring."""
    try:
        landing_page = LandingPage.objects.get(id=landing_page_id)
        landing_page.views += 1
        landing_page.save(update_fields=['views'])
        
        if lead_id:
            from leads.services import LeadScoringService
            LeadScoringService.update_lead_score(int(lead_id), 3, "Landing page visit")
            
        return True
        
    except LandingPage.DoesNotExist:
        return False


def track_marketing_engagement(event_type, lead_id=None, campaign_id=None, 
                              recipient_id=None, points=0, ip_address=None, user_agent=None):
    """
    Generic marketing engagement tracking function.
    Handles various types of engagement events and updates lead scoring.
    """
    result = {
        'lead_score_updated': False,
        'new_score': 0
    }
    
    try:
        # Handle different event types
        if event_type == 'email_open':
            if recipient_id:
                track_email_open_event(recipient_id)
                
        elif event_type == 'link_click':
            if recipient_id:
                track_link_click_event(recipient_id, '')
                
        elif event_type == 'landing_page_visit':
            if lead_id:
                from leads.services import LeadScoringService
                new_score = LeadScoringService.update_lead_score(int(lead_id), points, f"Marketing engagement: {event_type}")
                result['lead_score_updated'] = True
                result['new_score'] = new_score
                
        elif event_type == 'form_submission':
            if lead_id:
                from leads.services import LeadScoringService
                new_score = LeadScoringService.update_lead_score(int(lead_id), 15, "Form submission")
                result['lead_score_updated'] = True
                result['new_score'] = new_score
                
        elif event_type == 'content_download':
            if lead_id:
                from leads.services import LeadScoringService
                new_score = LeadScoringService.update_lead_score(int(lead_id), 8, "Content download")
                result['lead_score_updated'] = True
                result['new_score'] = new_score
                
        # Log the engagement event
        from engagement.models import EngagementEvent
        EngagementEvent.objects.create(
            event_type=f'marketing_{event_type}',
            title=f"Marketing {event_type.replace('_', ' ').title()}",
            description=f"Marketing engagement event: {event_type}",
            lead_id=lead_id,
            campaign_id=campaign_id,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=getattr(lead_id, 'tenant_id', None) if lead_id else None
        )
        
        return result
        
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error tracking marketing engagement: {e}")
        return result


def calculate_campaign_roi(campaign_id: int) -> float:
    """Calculate ROI based on leads converted to opportunities."""
    from opportunities.models import Opportunity
    campaign = MarketingCampaign.objects.get(id=campaign_id)
    
    # Get leads from this campaign
    lead_ids = CampaignRecipient.objects.filter(
        campaign=campaign,
        account__converted_from_lead__isnull=False
    ).values_list('account__converted_from_lead', flat=True)
    
    # Get opportunities from those leads
    opps = Opportunity.objects.filter(
        account__converted_from_lead__in=lead_ids
    )
    
    total_revenue = opps.aggregate(total=Sum('amount'))['total'] or 0
    # Assume campaign cost is stored somewhere (e.g., $1000)
    campaign_cost = 1000.0
    roi = ((total_revenue - campaign_cost) / campaign_cost) * 100 if campaign_cost > 0 else 0
    return round(roi, 2)


def get_optimal_send_time(contact_email: str, tenant_id: str = None) -> int:
    """
    Calculate optimal send time based on historical opens.
    Returns hour with highest open rate.
    """
    # Get all opened emails for this contact
    recipients = CampaignRecipient.objects.filter(
        email=contact_email,
        status__in=['opened', 'clicked']
    ).select_related('campaign')
    
    if tenant_id:
        recipients = recipients.filter(campaign__tenant_id=tenant_id)
    
    if not recipients.exists():
        return 10  # default to 10 AM UTC
    
    # Count opens by hour
    hour_counts = {}
    for r in recipients:
        if r.opened_at:
            hour = r.opened_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    # Return hour with most opens
    if hour_counts:
        return max(hour_counts, key=hour_counts.get)
    return 10