from django.utils import timezone
from datetime import timedelta
from .models import EngagementEvent, EngagementStatus, NextBestAction
from django.http import JsonResponse
import json
from accounts.models import Account
from opportunities.models import Opportunity
from .consumers import broadcast_engagement_event
from django.db.models import Avg
from .models import EngagementEvent
from automation.engine import evaluate_automation, execute_automations_sync
from .models import NextBestAction
from django.db.models import Avg
     
# Permission check
from core.object_permissions import AccountObjectPolicy
from leads.models import Lead
from django.shortcuts import get_object_or_404
def log_engagement_event(
    account_id: int,
    event_type: str,
    description: str,
    user_id: int = None,
    contact_email: str = None,
    opportunity_id: int = None,
    metadata: dict = None,
    engagement_score: float = 10.0,
    tenant_id: str = None
) -> EngagementEvent:
    """Log a new engagement event and trigger updates."""
    
    
    account = Account.objects.get(id=account_id)
    opportunity = None
    if opportunity_id:
        
        opportunity = Opportunity.objects.filter(id=opportunity_id).first()
    
    event = EngagementEvent.objects.create(
        account=account,
        opportunity=opportunity,
        event_type=event_type,
        description=description,
        title=description[:100],
        user_id=user_id,
        contact_email=contact_email,
        metadata=metadata or {},
        engagement_score=engagement_score,
        is_important=event_type in [
            'proposal_viewed', 'proposal_esg_viewed', 'nps_submitted', 
            'esg_content_viewed', 'opportunity_created'
        ],
        tenant_id=tenant_id or account.tenant_id
    )
    
    # Update engagement status
    update_engagement_status(account_id)
    
    # Generate next-best actions
    generate_next_best_actions(account_id)
    
    # Emit event for automation
    from automation.utils import emit_event
    emit_event(f'engagement.{event_type}', {
        'event_id': event.id,
        'account_id': account_id,
        'opportunity_id': opportunity_id,
        'user_id': user_id,
        'tenant_id': tenant_id or account.tenant_id,
    })
    
    # Send to WebSocket for real-time updates
    
    broadcast_engagement_event(event)
    
    return event


def update_engagement_status(account_id: int) -> None:
    """Update EngagementStatus for an account."""

    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    events = EngagementEvent.objects.filter(
        account_id=account_id,
        created_at__gte=thirty_days_ago
    )
    
    if not events.exists():
        score = 0.0
    else:
        avg_score = events.aggregate(avg=Avg('engagement_score'))['avg']
        score = avg_score or 0.0
    
    EngagementStatus.objects.update_or_create(
        account_id=account_id,
        defaults={
            'engagement_score': score,
            'last_engaged_at': timezone.now()
        }
    )


def generate_next_best_actions(account_id: int) -> None:
    """Generate next-best actions based on recent events."""
    
    account = Account.objects.get(id=account_id)
    
    # Get recent events
    events = EngagementEvent.objects.filter(
        account_id=account_id,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')
    
    # Rule 1: Proposal viewed but no follow-up
    if events.filter(event_type='proposal_viewed').exists():
        if not events.filter(event_type='email_sent', metadata__contains='follow_up').exists():
            NextBestAction.objects.get_or_create(
                account=account,
                action_type='send_email',
                defaults={
                    'description': 'Follow up on proposal view',
                    'due_date': timezone.now() + timedelta(days=2),
                    'source': 'Engagement Engine',
                    'priority': 'high'
                }
            )
    
    # Rule 2: ESG content viewed
    if events.filter(event_type='esg_content_viewed').exists():
        NextBestAction.objects.get_or_create(
            account=account,
            action_type='share_esg_brief',
            defaults={
                'description': 'Share detailed ESG impact report',
                'due_date': timezone.now() + timedelta(days=1),
                'source': 'ESG Engine',
                'priority': 'medium'
            }
        )
    
    # Rule 3: Health score dropping
    if hasattr(account, 'health_score') and account.health_score < 50:
        NextBestAction.objects.get_or_create(
            account=account,
            action_type='check_in',
            defaults={
                'description': 'Account health is low - proactive check-in required',
                'due_date': timezone.now() + timedelta(hours=24),
                'source': 'Health Monitor',
                'priority': 'critical'
            }
        )


def get_engagement_score(account_id: int = None, tenant_id: str = None) -> float:
    """Calculate 30-day engagement score (0–100)."""

    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    events = EngagementEvent.objects.filter(created_at__gte=thirty_days_ago)
    
    if account_id:
        events = events.filter(account_id=account_id)
    if tenant_id:
        events = events.filter(tenant_id=tenant_id)
    
    if not events.exists():
        return 0.0
    
    avg_score = events.aggregate(avg=Avg('engagement_score'))['avg']
    return round(avg_score, 2) if avg_score else 0.0

def get_lead_score(lead: Lead) -> int:
    """
    Calculates the lead score based on the lead's engagement score and the number of opportunities associated with the lead.
    """
    opportunity_count = Opportunity.objects.filter(lead=lead).count()
    return int(lead.engagement_score * opportunity_count)

def complete_next_best_action(request):
    """AJAX endpoint to mark next best action as completed."""
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        action_id = data.get('action_id')

        
        action = get_object_or_404(NextBestAction, id=action_id)
 
        if not AccountObjectPolicy.can_change(request.user, action.account):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        action.completed = True
        action.completed_at = timezone.now()
        action.save(update_fields=['completed', 'completed_at'])

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

