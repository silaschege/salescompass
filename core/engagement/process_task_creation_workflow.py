from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .models import EngagementStatus, NextBestAction
from .utils import calculate_engagement_score
from automation.engine import WorkflowEngine
from automation.models import Workflow, WorkflowAction
from communication.email_service import EmailService, EmailMessage
from tasks.models import Task

def trigger_low_engagement_sequence(account):
    """
    Trigger an automated email sequence for accounts with low engagement scores.
    This workflow creates a series of emails to be sent over time to re-engage the account.
    """
    # Calculate current engagement score
    engagement_score = calculate_engagement_score(account, account.tenant_id)
    
    # Only proceed if score is below threshold (30)
    if engagement_score >= 30:
        return
    
    # Check if a sequence is already running for this account
    existing_nba = NextBestAction.objects.filter(
        account=account,
        action_type='send_email',
        next_best_action_description__icontains='low engagement',
        completed=False,
        tenant_id=account.tenant_id
    ).exists()
    
    if existing_nba:
        return  # Don't create duplicate sequences
    
    # Create a workflow for the email sequence
    workflow = Workflow.objects.create(
        workflow_name=f"Low Engagement Sequence - {account.name}",
        workflow_description=f"Automated email sequence for re-engaging account {account.name} with low engagement score ({engagement_score})",
        workflow_trigger_type='account.low_engagement',
        workflow_is_active=True,
        created_by=account.owner if hasattr(account, 'owner') else None,
        tenant_id=account.tenant_id
    )
    
    # Create initial email action
    WorkflowAction.objects.create(
        workflow=workflow,
        workflow_action_type='send_email',
        workflow_action_parameters={
            'to': account.email,
            'subject': 'We miss you!',
            'template': 'engagement/low_engagement_initial.html',
            'context': {
                'account_name': account.name,
                'engagement_score': engagement_score
            }
        },
        workflow_action_order=1,
        workflow_action_is_active=True
    )
    
    # Create follow-up NBA for manual outreach if no response
    NextBestAction.objects.create(
        account=account,
        action_type='send_email',
        next_best_action_description=f"Follow up on low engagement sequence. Initial email sent for score {engagement_score}.",
        due_date=timezone.now() + timedelta(days=3),
        priority='medium',
        source='Low Engagement Workflow',
        status='open',
        assigned_to=account.owner if hasattr(account, 'owner') else account,
        tenant_id=account.tenant_id
    )


def create_engagement_threshold_tasks(account):
    """
    Create tasks based on engagement thresholds.
    """
    # Calculate current engagement score
    engagement_score = calculate_engagement_score(account, account.tenant_id)
    
    # High engagement - create upsell task
    if engagement_score > 80:
        # Check if task already exists
        exists = NextBestAction.objects.filter(
            account=account,
            action_type='send_proposal',
            next_best_action_description__icontains='high engagement',
            completed=False,
            tenant_id=account.tenant_id
        ).exists()
        
        if not exists:
            NextBestAction.objects.create(
                account=account,
                action_type='send_proposal',
                next_best_action_description=f"Account showing high engagement ({engagement_score}). Consider presenting upgrade or expansion opportunity.",
                due_date=timezone.now() + timedelta(days=2),
                priority='high',
                source='Engagement Threshold Workflow',
                status='open',
                assigned_to=account.owner if hasattr(account, 'owner') else account,
                tenant_id=account.tenant_id
            )
    
    # Medium-low engagement - create check-in task
    elif engagement_score < 40 and engagement_score >= 30:
        exists = NextBestAction.objects.filter(
            account=account,
            action_type='check_in',
            next_best_action_description__icontains='medium-low engagement',
            completed=False,
            tenant_id=account.tenant_id
        ).exists()
        
        if not exists:
            NextBestAction.objects.create(
                account=account,
                action_type='check_in',
                next_best_action_description=f"Account showing medium-low engagement ({engagement_score}). Personal check-in recommended.",
                due_date=timezone.now() + timedelta(days=3),
                priority='medium',
                source='Engagement Threshold Workflow',
                status='open',
                assigned_to=account.owner if hasattr(account, 'owner') else account,
                tenant_id=account.tenant_id
            )


def escalate_critical_account(account):
    """
    Escalate workflows for critical accounts (very low engagement or long inactivity).
    """
    status, _ = EngagementStatus.objects.get_or_create(account=account)
    engagement_score = calculate_engagement_score(account, account.tenant_id)
    
    # Criteria for critical account:
    # 1. Engagement score < 20 OR
    # 2. No engagement for more than 30 days
    is_critical = False
    reason = ""
    
    if engagement_score < 20:
        is_critical = True
        reason = f"Very low engagement score: {engagement_score}"
    elif status.last_engaged_at:
        days_since_engagement = (timezone.now() - status.last_engaged_at).days
        if days_since_engagement > 30:
            is_critical = True
            reason = f"No engagement for {days_since_engagement} days"
    
    if not is_critical:
        return
    
    # Check if escalation already exists
    exists = NextBestAction.objects.filter(
        account=account,
        action_type='schedule_call',
        next_best_action_description__icontains='critical account',
        completed=False,
        tenant_id=account.tenant_id
    ).exists()
    
    if exists:
        return
    
    # Create escalation task for senior account manager
    NextBestAction.objects.create(
        account=account,
        action_type='schedule_call',
        next_best_action_description=f"Critical account escalation: {reason}. Immediate senior attention required.",
        due_date=timezone.now() + timedelta(days=1),
        priority='critical',
        source='Critical Account Escalation Workflow',
        status='open',
        assigned_to=account.owner.manager if hasattr(account, 'owner') and hasattr(account.owner, 'manager') else account.owner if hasattr(account, 'owner') else account,
        tenant_id=account.tenant_id
    )
    
    # Notify management team via email
    try:
        # Get management team emails (this would be customized per tenant)
        management_emails = ['management@company.com']  # Placeholder
        
        email_service = EmailService()
        message = EmailMessage(
            to=management_emails,
            subject=f'Critical Account Escalation: {account.name}',
            html_content=f"""
            <p>Hello Team,</p>
            <p>The account <strong>{account.name}</strong> has been flagged as critical and requires immediate attention:</p>
            <p><strong>Reason:</strong> {reason}</p>
            <p><strong>Account Owner:</strong> {account.owner.email if hasattr(account, 'owner') else 'Unassigned'}</p>
            <p>Please review this account and take appropriate action.</p>
            <p>Regards,<br>SalesCompass CRM</p>
            """,
            text_content=f"""
            Hello Team,
            
            The account {account.name} has been flagged as critical and requires immediate attention:
            
            Reason: {reason}
            Account Owner: {account.owner.email if hasattr(account, 'owner') else 'Unassigned'}
            
            Please review this account and take appropriate action.
            
            Regards,
            SalesCompass CRM
            """
        )
        email_service.send(message)
    except Exception as e:
        # Log error but don't fail the escalation
        print(f"Failed to send critical account escalation email: {e}")


def integrate_with_automation_module(account):
    """
    Integrate engagement workflows with the existing automation module.
    This function creates automation-compatible events and triggers.
    """
    from automation.models import Automation
    from automation.engine import execute_automations_sync
    
    # Calculate engagement score
    engagement_score = calculate_engagement_score(account, account.tenant_id)
    
    # Create payload for automation module
    payload = {
        'account': {
            'id': account.id,
            'name': account.name,
            'email': account.email,
            'tenant_id': account.tenant_id,
        },
        'engagement': {
            'score': engagement_score,
            'last_engaged_at': None,
        },
        'trigger': 'engagement_score_update'
    }
    
    # Add engagement status info if exists
    try:
        status = EngagementStatus.objects.get(account=account)
        payload['engagement']['last_engaged_at'] = status.last_engaged_at
    except EngagementStatus.DoesNotExist:
        pass
    
    # Execute automations for engagement score updates
    execute_automations_sync('engagement.score_updated', payload)
    
    # If engagement is low, trigger specific automations
    if engagement_score < 30:
        execute_automations_sync('engagement.score_low', payload)
    
    # If engagement is high, trigger upsell automations
    if engagement_score > 80:
        execute_automations_sync('engagement.score_high', payload)


def process_all_engagement_workflows(account):
    """
    Main function to process all engagement workflows for an account.
    This function should be called when engagement scores are updated.
    """
    # Trigger low engagement sequence if applicable
    trigger_low_engagement_sequence(account)
    
    # Create tasks based on engagement thresholds
    create_engagement_threshold_tasks(account)
    
    # Escalate critical accounts
    escalate_critical_account(account)
    
    # Integrate with automation module
    integrate_with_automation_module(account)