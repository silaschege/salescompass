from django.utils import timezone
from datetime import timedelta
from .models import EngagementStatus, NextBestAction, EngagementEvent

def evaluate_auto_nba_rules(account):
    """
    Evaluate rules for a specific account and create NBAs if necessary.
    """
    status, _ = EngagementStatus.objects.get_or_create(account=account)
    
    # Rule 1: Low Engagement Score -> Check In
    if status.engagement_score < 30:
        # Check if an open NBA of this type already exists to avoid spam
        exists = NextBestAction.objects.filter(
            account=account,
            action_type='check_in',
            completed=False
        ).exists()
        
        if not exists:
            NextBestAction.objects.create(
                account=account,
                action_type='check_in',
                next_best_action_description="Engagement score is critically low. Personal check-in required.",
                due_date=timezone.now() + timedelta(days=2),
                priority='high',
                source='Auto-Rule: Low Engagement',
                status='open',
                # Assign to account owner or default admin
                assigned_to=account.owner if hasattr(account, 'owner') and account.owner else account, 
                tenant_id=account.tenant_id if hasattr(account, 'tenant_id') else None
            )

    # Rule 2: Inactivity > 30 days -> Send Email (Re-engagement)
    if status.last_engaged_at:
        days_inactive = (timezone.now() - status.last_engaged_at).days
        if days_inactive > 30:
            exists = NextBestAction.objects.filter(
                account=account,
                action_type='send_email',
                source__contains='Inactivity', # Simple tag check
                completed=False
            ).exists()
            
            if not exists:
                NextBestAction.objects.create(
                    account=account,
                    action_type='send_email',
                    next_best_action_description="Account has been inactive for over 30 days. Send re-engagement email.",
                    due_date=timezone.now() + timedelta(days=3),
                    priority='medium',
                    source='Auto-Rule: Inactivity',
                    status='open',
                    assigned_to=account.owner if hasattr(account, 'owner') and account.owner else account,
                    tenant_id=account.tenant_id if hasattr(account, 'tenant_id') else None
                )

def run_auto_nba_check():
    """
    Batch process to evaluate rules for all accounts.
    """
    for status in EngagementStatus.objects.all():
        evaluate_auto_nba_rules(status.account)


def check_churn_risk(account):
    """
    Check for churn risk indicators and create high-priority NBAs.
    Risk Factors:
    1. Score drop > 20% in 7 days (requires history, approximating with current low score vs previous not fully tracked here without history model)
    2. No activity for > 45 days.
    """
    from .models import EngagementStatus, NextBestAction
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        status = EngagementStatus.objects.get(account=account)
    except EngagementStatus.DoesNotExist:
        return

    # Rule 1: Prolonged Inactivity (> 45 days)
    if status.last_engaged_at and status.last_engaged_at < timezone.now() - timedelta(days=45):
        # Check if we already have an open 'Churn Risk' action
        exists = NextBestAction.objects.filter(
            account=account,
            action_type='schedule_call',
            next_best_action_description__startswith="Churn Risk Alert: No activity",
            completed=False
        ).exists()
        
        if not exists:
            NextBestAction.objects.create(
                account=account,
                tenant_id=account.tenant_id if hasattr(account, 'tenant_id') else None,
                action_type='schedule_call',
                next_best_action_description="Churn Risk Alert: No activity for 45+ days. Immediate outreach required.",
                priority='critical',
                due_date=timezone.now() + timedelta(days=2),
                source='Churn Risk Detector',
                status='open'
            )
            print(f"Created Churn Risk NBA for {account} (Inactivity)")

    # Rule 2: Critically Low Score (< 15) for previously active accounts
    if status.engagement_score < 15 and status.last_engaged_at:
         exists = NextBestAction.objects.filter(
            account=account,
            next_best_action_description__startswith="Churn Risk Alert: Engagement score critical",
            completed=False
        ).exists()
         
         if not exists:
            NextBestAction.objects.create(
                account=account,
                tenant_id=account.tenant_id if hasattr(account, 'tenant_id') else None,
                action_type='share_esg_brief', # Re-assess strategy
                next_best_action_description=f"Churn Risk Alert: Engagement score critical ({status.engagement_score:.1f}). Re-assess strategy.",
                priority='high',
                due_date=timezone.now() + timedelta(days=5),
                source='Churn Risk Detector',
                status='open'
            )
            print(f"Created Churn Risk NBA for {account} (Low Score)")
