from django.utils import timezone
from datetime import timedelta
from .models import EngagementStatus, NextBestAction, EngagementEvent

def evaluate_auto_nba_rules(account):
    """
    Evaluate rules for a specific account and create NBAs if necessary.
    Now uses dynamic AutoNBARule definitions.
    """
    from .models import AutoNBARule, NextBestAction
    
    tenant_id = getattr(account, 'tenant_id', None)
    rules = AutoNBARule.objects.filter(tenant_id=tenant_id, auto_nba_is_active=True)
    
    for rule in rules:
        should_trigger = False
        
        if rule.trigger_event == 'low_engagement_score':
            status, _ = EngagementStatus.objects.get_or_create(account=account)
            if status.engagement_score < 30: # Threshold could be moved to rule metadata later
                should_trigger = True
        
        elif rule.trigger_event == 'no_engagement_7_days':
            week_ago = timezone.now() - timedelta(days=7)
            recent_events = EngagementEvent.objects.filter(
                account=account,
                tenant_id=tenant_id,
                created_at__gte=week_ago
            )
            if not recent_events.exists():
                should_trigger = True
                
        # Only process periodic rules here, event-triggered ones are in utils.py
        if should_trigger:
            # Check for existing open NBA of same type/source to avoid duplicates
            exists = NextBestAction.objects.filter(
                account=account,
                action_type=rule.action_type,
                source=f'Auto NBA Rule: {rule.rule_name}',
                completed=False
            ).exists()
            
            if not exists:
                NextBestAction.objects.create(
                    account=account,
                    tenant_id=tenant_id,
                    action_type=rule.action_type,
                    next_best_action_description=rule.description_template.format(
                        account_name=account.name,
                        engagement_score=getattr(account, 'engagement_status', None).engagement_score if hasattr(account, 'engagement_status') else 0,
                        event_type='Periodic Check'
                    ),
                    due_date=timezone.now() + timedelta(days=rule.due_in_days),
                    priority=rule.priority,
                    source=f'Auto NBA Rule: {rule.rule_name}',
                    status='open',
                    assigned_to=account.owner if hasattr(account, 'owner') and account.owner else account
                )

def run_auto_nba_check():
    """
    Batch process to evaluate rules for all accounts.
    """
    for status in EngagementStatus.objects.all():
        if status.account:
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
