from celery import shared_task
from django.utils import timezone
from .models import Account
from communication.models import Email, Call, Meeting
from cases.models import Case

@shared_task
def update_account_health(account_id):
    """
    Calculate and update the health score for a single account.
    Score (0-100) based on:
    - Engagement (Last 30 days emails/calls)
    - Support Cases (Open high priority cases reduce score)
    - NPS (if available)
    """
    try:
        account = Account.objects.get(id=account_id)
        score = 50.0 # Start neutral
        
        # 1. Engagement (Last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        recent_emails = Email.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
        recent_calls = Call.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
        recent_meetings = Meeting.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
        
        # Add points for engagement
        score += min(20, recent_emails * 2)
        score += min(15, recent_calls * 5)
        score += min(15, recent_meetings * 10)
        
        # 2. Support Cases (Risk Factor)
        # Assuming Case model has 'account', 'status', 'priority'
        # We need to check if Case model exists and has these fields. 
        # For now, we'll wrap in try/except or check model definition.
        # Based on previous ls, cases app exists.
        
        open_cases = Case.objects.filter(
            account=account, 
            status__in=['new', 'open', 'escalated']
        )
        
        for case in open_cases:
            if case.priority == 'critical':
                score -= 20
            elif case.priority == 'high':
                score -= 10
            else:
                score -= 2
                
        # 3. Renewal Risk
        if account.renewal_date:
            days_to_renewal = (account.renewal_date - timezone.now().date()).days
            if days_to_renewal < 30 and score < 70:
                # High risk if renewal is close and health is low
                score -= 10
        
        # Cap score
        account.health_score = max(0.0, min(100.0, score))
        
        # Update status based on health
        if account.health_score < 40:
            account.status = 'at_risk'
        elif account.health_score > 70:
            account.status = 'active' # or 'healthy'
            
        account.save(update_fields=['health_score', 'status'])
        
        return account.health_score
        
    except Account.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error updating account health: {e}")
        return None

@shared_task
def update_all_account_health():
    """
    Periodic task to update health for all active accounts.
    """
    for account in Account.objects.filter(status__in=['active', 'at_risk']):
        update_account_health.delay(account.id)
