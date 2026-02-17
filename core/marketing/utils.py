import random
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum
from .models import (
    CampaignRecipient, Campaign, LandingPage, 
    ABTest, ABTestVariant, ABTestResponse, EmailCampaign
)

logger = logging.getLogger(__name__)

def send_campaign_email(recipient_id: int) -> bool:
    """Send email to a campaign recipient using updated model fields."""
    try:
        recipient = CampaignRecipient.objects.select_related(
            'email_campaign', 
            'email_campaign__campaign'
        ).get(id=recipient_id)
        
        # Check unsubscribe (Assuming Unsubscribe model exists in your leads or core app)
        # Using a try-except or a generic check to avoid import errors
        try:
            from core.leads.models import Unsubscribe
            if Unsubscribe.objects.filter(email=recipient.email, tenant_id=recipient.tenant_id).exists():
                recipient.status = 'unsubscribed'
                recipient.save(update_fields=['status'])
                return False
        except ImportError:
            pass
     
        email_campaign = recipient.email_campaign
        campaign = email_campaign.campaign
        
        # The EmailCampaign model in your snippets doesn't have a direct FK to EmailTemplate,
        # but the EmailCampaign object itself has 'subject' and 'content' fields.
        # Alternatively, if you are using a template:
        subject = email_campaign.subject
        body_content = email_campaign.content
        
        # Render with personalization
        context = {
            'recipient': recipient,
            'campaign_name': campaign.campaign_name,
            'first_name': recipient.first_name,
            'last_name': recipient.last_name,
            'merge_data': recipient.merge_data,
            'unsubscribe_url': f"https://salescompass.com/marketing/unsubscribe/{recipient.id}/"
        }
        
        html_content = render_to_string('marketing/email_wrapper.html', {
            'content': body_content,
            'context': context
        })
        
        # Send email
        # Note: from_email could be dynamically pulled from EmailIntegration/Provider later
        send_mail(
            subject=subject,
            message='', # Plain text
            html_message=html_content,
            from_email='noreply@salescompass.com',
            recipient_list=[recipient.email]
        )
        
        recipient.status = 'sent'
        recipient.sent_at = timezone.now()
        recipient.save(update_fields=['status', 'sent_at'])
        return True
        
    except Exception as e:
        logger.error(f"Failed to send campaign email to {recipient_id}: {e}")
        recipient.status = 'bounced'
        recipient.save(update_fields=['status'])
        return False


def assign_ab_test_variant(ab_test_id: int, recipient_email: str) -> ABTestVariant:
    """
    Assign a variant to a recipient. Ensures tenant_id is preserved.
    """
    try:
        ab_test = ABTest.objects.get(id=ab_test_id, is_active=True)
        
        # Check if recipient already has a variant assigned
        existing_response = ABTestResponse.objects.filter(
            ab_test_variant__ab_test=ab_test,
            email=recipient_email
        ).first()
        
        if existing_response:
            return existing_response.ab_test_variant
            
        variants = list(ab_test.variants.all())
        if not variants:
            return None
            
        total_weight = sum(variant.assignment_rate for variant in variants)
        rand_val = random.uniform(0, total_weight)
        
        cumulative_weight = 0
        selected_variant = variants[0] # Default fallback
        
        for variant in variants:
            cumulative_weight += variant.assignment_rate
            if rand_val <= cumulative_weight:
                selected_variant = variant
                break
        
        # Create a response record with tenant inheritance
        ABTestResponse.objects.create(
            ab_test_variant=selected_variant,
            email=recipient_email,
            tenant_id=ab_test.tenant_id
        )
        return selected_variant
        
    except ABTest.DoesNotExist:
        return None


def send_ab_test_email(ab_test_id: int, recipient_email: str, **kwargs) -> bool:
    """
    Send an A/B test email using the EmailTemplate assigned to the variant.
    """
    variant = assign_ab_test_variant(ab_test_id, recipient_email)
    if not variant or not variant.email_template:
        return False
        
    template = variant.email_template
    
    context = {
        'email': recipient_email,
        'ab_test_variant': variant.variant,
        'subject': template.subject,
        'unsubscribe_url': f"https://salescompass.com/marketing/ab-test/unsubscribe/{variant.id}/{recipient_email}/",
        **kwargs
    }
    
    html_content = render_to_string('marketing/email_wrapper.html', {
        'content': template.content, # Updated from html_content to content
        'context': context
    })
    
    try:
        send_mail(
            subject=template.subject,
            message='', 
            html_message=html_content,
            from_email='noreply@salescompass.com',
            recipient_list=[recipient_email]
        )
        
        # Update variant metrics
        variant.sent_count += 1
        variant.save(update_fields=['sent_count'])
        return True
    except Exception as e:
        logger.error(f"Failed to send A/B test email: {e}")
        return False


def track_ab_test_event(event_type: str, ab_test_variant_id: int, recipient_email: str, 
                        value: float = 0.0, ip: str = None, ua: str = None) -> bool:
    """
    Unified tracking for Open, Click, and Conversion to reduce code duplication.
    """
    try:
        response, created = ABTestResponse.objects.get_or_create(
            ab_test_variant_id=ab_test_variant_id,
            email=recipient_email
        )
        
        variant = response.ab_test_variant
        now = timezone.now()
        updated_fields = []

        if event_type == 'open' and not response.opened_at:
            response.opened_at = now
            variant.open_count += 1
            updated_fields = ['opened_at']
        elif event_type == 'click' and not response.clicked_at:
            response.clicked_at = now
            variant.click_count += 1
            updated_fields = ['clicked_at']
        elif event_type == 'conversion' and not response.conversion_at:
            response.conversion_at = now
            response.conversion_value = value
            variant.conversion_count += 1
            updated_fields = ['conversion_at', 'conversion_value']

        if updated_fields:
            response.ip_address = ip
            response.user_agent = ua
            response.save(update_fields=updated_fields + ['ip_address', 'user_agent'])
            variant.save(update_fields=[f'{event_type}_count'])
            
        return True
    except Exception as e:
        logger.error(f"Error tracking AB event {event_type}: {e}")
        return False


def calculate_ab_test_statistics(ab_test_id: int) -> dict:
    """
    Calculate statistics using model properties for consistency.
    """
    try:
        ab_test = ABTest.objects.prefetch_related('variants').get(id=ab_test_id)
        variants_data = []
        
        for v in ab_test.variants.all():
            variants_data.append({
                'variant': v.variant,
                'display': v.get_variant_display(),
                'sent': v.sent_count,
                'opens': v.open_count,
                'clicks': v.click_count,
                'conversions': v.conversion_count,
                'open_rate': v.open_rate,
                'click_rate': v.click_rate,
                'ctr': v.ctr,
                'conv_rate': v.conversion_rate,
            })
            
        return {
            'ab_test_name': ab_test.name,
            'variants': variants_data,
            'total_responses': ab_test.total_responses,
        }
    except ABTest.DoesNotExist:
        return {}


def declare_ab_test_winner(ab_test_id: int, metric: str = 'ctr') -> str:
    """
    Declare winner based on updated ABTest model fields.
    """
    try:
        ab_test = ABTest.objects.get(id=ab_test_id)
        if ab_test.is_winner_declared:
            return ab_test.winner_variant
            
        stats = calculate_ab_test_statistics(ab_test_id)
        if not stats.get('variants'):
            return None
            
        # Find winner
        winner_data = max(stats['variants'], key=lambda x: x.get(metric, 0))
        
        ab_test.winner_variant = winner_data['variant']
        ab_test.is_winner_declared = True
        ab_test.end_date = timezone.now()
        ab_test.save(update_fields=['winner_variant', 'is_winner_declared', 'end_date'])
            
        return ab_test.winner_variant
    except ABTest.DoesNotExist:
        return None

def track_email_open_event(recipient_id: int) -> bool:
    """
    Track when a standard campaign email is opened.
    """
    try:
        recipient = CampaignRecipient.objects.get(id=recipient_id)
        if not recipient.opened_at:
            recipient.opened_at = timezone.now()
            recipient.status = 'opened'
            recipient.save(update_fields=['opened_at', 'status'])
        return True
    except CampaignRecipient.DoesNotExist:
        return False