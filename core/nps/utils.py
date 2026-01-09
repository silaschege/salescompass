from django.utils import timezone
from datetime import timedelta
from .models import NpsResponse, NpsDetractorAlert, NpsTrendSnapshot, NpsSurvey, NpsEscalationRule, NpsEscalationAction, NpsEscalationActionLog
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from accounts.models import Account
from tenants.models import TenantMember, TenantRole, TenantTerritory
from  cases.utils import escalate_case,calculate_sla_due_date


def calculate_nps_score(account_id: int = None, tenant_id: str = None) -> float:
    """
    Calculate Net Promoter Score: % Promoters - % Detractors.
    Returns score from -100 to +100.
    """
    responses = NpsResponse.objects.all()
    if account_id:
        responses = responses.filter(account_id=account_id)
    if tenant_id:
        responses = responses.filter(tenant_id=tenant_id)
     
    if not responses.exists():
        return 0.0
    
    total = responses.count()
    promoters = responses.filter(score__gte=9).count()
    detractors = responses.filter(score__lte=6).count()
    
    nps = ((promoters - detractors) / total) * 100
    return round(nps, 1)


def create_detractor_alert(response_id: int) -> None:
    """Create alert for NPS detractor."""
    response = NpsResponse.objects.get(id=response_id)
    if response.is_detractor:
        alert, created = NpsDetractorAlert.objects.get_or_create(
            response=response,
            defaults={'status': 'open'}
        )
        
        # Emit event for automation
        from automation.utils import emit_event
        emit_event('nps.detractor_alert', {
            'response_id': response.id,
            'account_id': response.account_id,
            'score': response.score,
            'tenant_id': response.tenant_id,
        })


def create_nps_trend_snapshot(tenant_id: str = None) -> NpsTrendSnapshot:
    """Create daily NPS snapshot."""
    today = timezone.now().date()
    responses = NpsResponse.objects.filter(created_at__date=today)
    if tenant_id:
        responses = responses.filter(tenant_id=tenant_id)
    
    total = responses.count()
    if total == 0:
        return None
    
    promoters = responses.filter(score__gte=9).count()
    passives = responses.filter(score__in=[7,8]).count()
    detractors = responses.filter(score__lte=6).count()
    nps_score = ((promoters - detractors) / total) * 100
    
    snapshot, created = NpsTrendSnapshot.objects.update_or_create(
        date=today,
        tenant_id=tenant_id,
        defaults={
            'nps_score': round(nps_score, 1),
            'total_responses': total,
            'promoters': promoters,
            'passives': passives,
            'detractors': detractors,
        }
    )
    return snapshot
 

def send_nps_survey(survey_id: int, account_id: int, contact_email: str = None) -> bool:
    """Send NPS survey via email."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    survey = NpsSurvey.objects.get(id=survey_id)
    account = Account.objects.get(id=account_id)
    
    if not contact_email:
        contact = account.contacts.filter(is_primary=True).first()
        if not contact:
            return False
        contact_email = contact.email
    
    # Generate unique response URL
    from uuid import uuid4
    response_uuid = uuid4()
    
    # In production, store in a PendingNpsResponse model
    html_content = render_to_string('engagement/nps_survey.html', {
        'survey': survey,
        'account': account,
        'contact_email': contact_email,
        'response_uuid': response_uuid,
    })
    
    send_mail(
        subject="We'd love your feedback!",
        message="",
        html_message=html_content,
        from_email="feedback@salescompass.com",
        recipient_list=[contact_email]
    )
    return True


def get_nps_trend_data(tenant_id: str = None, period: str = 'daily') -> list:
    """Get NPS trend data for charting."""

    
    # Determine date range
    if period == 'yearly':
        start_date = timezone.now().date() - timedelta(days=365*2)
        date_field = 'date__year'
    elif period == 'monthly':
        start_date = timezone.now().date() - timedelta(days=365)
        date_field = 'date__month'
    elif period == 'weekly':
        start_date = timezone.now().date() - timedelta(days=90)
        date_field = 'date__week'
    else:  # daily
        start_date = timezone.now().date() - timedelta(days=30)
        date_field = 'date'
    
    snapshots = NpsTrendSnapshot.objects.filter(
        date__gte=start_date
    )
    if tenant_id:
        snapshots = snapshots.filter(tenant_id=tenant_id)
    
    # Group by period
    if period == 'yearly':
        data = snapshots.values('date__year').annotate(
            avg_nps=Avg('nps_score'),
            total=Sum('total_responses')
        ).order_by('date__year')
        return [{'date': f"{item['date__year']}", 'nps': item['avg_nps']} for item in data]
    elif period == 'monthly':
        data = snapshots.values('date__year', 'date__month').annotate(
            avg_nps=Avg('nps_score')
        ).order_by('date__year', 'date__month')
        return [{'date': f"{item['date__year']}-{item['date__month']:02d}", 'nps': item['avg_nps']} for item in data]
    elif period == 'weekly':
        data = snapshots.extra(select={'week': "strftime('%%Y-%%W', date)"}).values('week').annotate(
            avg_nps=Avg('nps_score')
        ).order_by('week')
        return [{'date': item['week'], 'nps': item['avg_nps']} for item in data]
    else:  # daily
        data = snapshots.order_by('date')
        return [{'date': item.date.isoformat(), 'nps': item.nps_score} for item in data]
    
def apply_escalation_rules(nps_response: NpsResponse) -> None:
    """
    Apply escalation rules to an NPS response.
    
    Args:
        nps_response: The NPS response to apply rules to
    """
    # Get active escalation rules for this tenant
    rules = NpsEscalationRule.objects.filter(
        tenant=nps_response.tenant,
        is_active=True
    ).order_by('id')
    
    # Apply each rule that matches
    for rule in rules:
        if rule.applies_to_response(nps_response):
            # Get ordered actions for this rule
            rule_actions = rule.actions.through.objects.filter(
                escalation_rule=rule
            ).select_related('escalation_action').order_by('order')
            
            # Execute each action
            for rule_action in rule_actions:
                action = rule_action.escalation_action
                _execute_escalation_action(action, nps_response, rule)


def _execute_escalation_action(action: NpsEscalationAction, nps_response: NpsResponse, rule: NpsEscalationRule) -> None:
    """
    Execute a specific escalation action.
    
    Args:
        action: The escalation action to execute
        nps_response: The NPS response to act on
        rule: The escalation rule that triggered this action
    """
    from automation.utils import emit_event
    from tasks.models import Task
    from cases.models import Case
    
    # Create action log
    action_log = NpsEscalationActionLog.objects.create(
        escalation_rule=rule,
        action=action,
        nps_response=nps_response,
        tenant=nps_response.tenant,
        status='in_progress',
        executed_at=timezone.now()
    )
    
    try:
        if action.action_type == 'create_case':
            # Create a case based on the action parameters
            case_subject = action.action_parameters.get(
                'subject_template', 
                f"NPS Response Escalation: {nps_response.survey.nps_survey_name}"
            )
            
            case_description = action.action_parameters.get(
                'description_template',
                f"NPS response received (score: {nps_response.score})\n\n"
                f"Comment: {nps_response.comment}\n\n"
                f"Survey: {nps_response.survey.nps_survey_name}\n"
                f"Response Date: {nps_response.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            case = Case.objects.create(
                account=nps_response.account,
                subject=case_subject,
                case_description=case_description,
                priority=action.action_parameters.get('priority', 'medium'),
                tenant=nps_response.tenant,
                assigned_team=action.action_parameters.get('assigned_team', 'Support')
            )
            
            # Assign to appropriate person based on role if specified
            assigned_role_id = action.action_parameters.get('assigned_to_role')
            if assigned_role_id:
                assignee = TenantMember.objects.filter(
                    tenant=nps_response.tenant,
                    role_id=assigned_role_id
                ).select_related('user').first()
                
                if assignee:
                    case.owner = assignee.user
                    case.save()
            
            # Set SLA if specified
            sla_hours = action.action_parameters.get('sla_response_hours')
            if sla_hours:
                case.sla_response_hours = sla_hours
                case.sla_due = calculate_sla_due_date(case.priority)
                case.save()
            
            # Escalate if needed
            escalation_level = action.action_parameters.get('escalation_level')
            if escalation_level and escalation_level != 'none':
                escalate_case(
                    case.id,
                    escalation_level,
                    nps_response.account.tenant.owner_id
                )
                
            # Update action log
            action_log.result_data = {'case_id': case.id}
            action_log.status = 'completed'
            action_log.completed_at = timezone.now()
            action_log.save()
            
            # Emit event
            emit_event('nps.case_escalated', {
                'response_id': nps_response.id,
                'account_id': nps_response.account_id,
                'case_id': case.id,
                'score': nps_response.score,
                'tenant_id': nps_response.tenant_id,
                'rule_id': rule.id,
                'action_id': action.id,
            })
            
        elif action.action_type == 'assign_task':
            # Create a task based on the action
            task_title = action.action_parameters.get(
                'title_template',
                f"NPS Follow-up: {nps_response.survey.nps_survey_name}"
            )
            
            task_description = action.action_parameters.get(
                'description_template',
                f"Follow up on NPS response (score: {nps_response.score})\n\n"
                f"Comment: {nps_response.comment}\n\n"
                f"Survey: {nps_response.survey.nps_survey_name}"
            )
            
            # Calculate due date
            due_days = action.action_parameters.get('due_days', 2)
            due_date = timezone.now() + timedelta(days=due_days)
            
            task = Task.objects.create(
                account=nps_response.account,
                task_title=task_title,
                task_description=task_description,
                task_type=action.action_parameters.get('task_type', 'nps_followup'),
                priority=action.action_parameters.get('priority', 'medium'),
                tenant=nps_response.tenant,
                due_date=due_date
            )
            
            # Assign to appropriate person based on role if specified
            assigned_role_id = action.action_parameters.get('assigned_to_role')
            if assigned_role_id:
                assignee = TenantMember.objects.filter(
                    tenant=nps_response.tenant,
                    role_id=assigned_role_id
                ).select_related('user').first()
                
                if assignee:
                    task.assigned_to = assignee.user
                    task.save()
            
            # Update action log
            action_log.result_data = {'task_id': task.id}
            action_log.status = 'completed'
            action_log.completed_at = timezone.now()
            action_log.save()
            
            # Emit event
            emit_event('nps.task_assigned', {
                'response_id': nps_response.id,
                'account_id': nps_response.account_id,
                'task_id': task.id,
                'score': nps_response.score,
                'tenant_id': nps_response.tenant_id,
                'rule_id': rule.id,
                'action_id': action.id,
            })
            
        elif action.action_type == 'send_notification':
            # Send notification (implementation would depend on notification system)
            action_log.result_data = {'message': 'Notification sent'}
            action_log.status = 'completed'
            action_log.completed_at = timezone.now()
            action_log.save()
            
            emit_event('nps.notification_sent', {
                'response_id': nps_response.id,
                'account_id': nps_response.account_id,
                'score': nps_response.score,
                'tenant_id': nps_response.tenant_id,
                'rule_id': rule.id,
                'action_id': action.id,
            })
            
        elif action.action_type == 'trigger_workflow':
            # Trigger workflow (implementation would depend on workflow system)
            action_log.result_data = {'message': 'Workflow triggered'}
            action_log.status = 'completed'
            action_log.completed_at = timezone.now()
            action_log.save()
            
            emit_event('nps.workflow_triggered', {
                'response_id': nps_response.id,
                'account_id': nps_response.account_id,
                'score': nps_response.score,
                'tenant_id': nps_response.tenant_id,
                'rule_id': rule.id,
                'action_id': action.id,
            })
            
        else:
            # Handle other action types or mark as not implemented
            action_log.result_data = {'message': f'Action type {action.action_type} not implemented'}
            action_log.status = 'completed'
            action_log.completed_at = timezone.now()
            action_log.save()
            
    except Exception as e:
        # Log the error
        action_log.status = 'failed'
        action_log.error_message = str(e)
        action_log.completed_at = timezone.now()
        action_log.save()
        
        # Re-raise the exception
        raise

def calculate_response_rate(account_id: int = None, tenant_id: str = None) -> float:
    """
    Calculate the NPS response rate: (Total Responses / Total Surveys Sent) * 100
    
    Args:
        account_id: Optional account ID to filter by
        tenant_id: Optional tenant ID to filter by
        
    Returns:
        float: Response rate as percentage (0-100)
    """
    from .models import NpsSurvey
    
    # Get total responses
    responses = NpsResponse.objects.all()
    if account_id:
        responses = responses.filter(account_id=account_id)
    if tenant_id:
        responses = responses.filter(tenant_id=tenant_id)
    
    total_responses = responses.count()
    
    if total_responses == 0:
        return 0.0
    
    # Get total surveys sent (this is a simplification - in a real system you'd track deliveries)
    surveys = NpsSurvey.objects.all()
    if tenant_id:
        surveys = surveys.filter(tenant_id=tenant_id)
    
    total_surveys = surveys.count()
    
    if total_surveys == 0:
        return 0.0
    
    response_rate = (total_responses / total_surveys) * 100
    return round(response_rate, 1)


def get_detractor_resolution_time(tenant_id: str = None) -> dict:
    """
    Calculate average time to resolve detractor alerts.
    
    Args:
        tenant_id: Optional tenant ID to filter by
        
    Returns:
        dict: Statistics about detractor resolution times
    """
    alerts = NpsDetractorAlert.objects.filter(status='resolved')
    if tenant_id:
        alerts = alerts.filter(tenant_id=tenant_id)
    
    if not alerts.exists():
        return {
            'average_resolution_hours': 0,
            'median_resolution_hours': 0,
            'total_resolved': 0
        }
    
    resolution_times = []
    for alert in alerts:
        if alert.resolved_at and alert.created_at:
            resolution_delta = alert.resolved_at - alert.created_at
            resolution_hours = resolution_delta.total_seconds() / 3600
            resolution_times.append(resolution_hours)
    
    if not resolution_times:
        return {
            'average_resolution_hours': 0,
            'median_resolution_hours': 0,
            'total_resolved': len(resolution_times)
        }
    
    average_resolution = sum(resolution_times) / len(resolution_times)
    
    # Calculate median
    sorted_times = sorted(resolution_times)
    n = len(sorted_times)
    if n % 2 == 0:
        median_resolution = (sorted_times[n//2 - 1] + sorted_times[n//2]) / 2
    else:
        median_resolution = sorted_times[n//2]
    
    return {
        'average_resolution_hours': round(average_resolution, 1),
        'median_resolution_hours': round(median_resolution, 1),
        'total_resolved': len(resolution_times)
    }


def get_nps_by_segment(segment_type: str, tenant_id: str = None) -> dict:
    """
    Get NPS scores segmented by role or territory.
    
    Args:
        segment_type: Either 'role' or 'territory'
        tenant_id: Optional tenant ID to filter by
        
    Returns:
        dict: NPS scores by segment
    """
    from tenants.models import TenantMember
    
    segments = {}
    
    if segment_type == 'role':
        # Get all roles
        roles = TenantMember.objects.filter(tenant_id=tenant_id).values_list(
            'role__name', flat=True).distinct()
        
        for role in roles:
            if role:
                responses = NpsResponse.objects.filter(
                    account__tenant_member__role__name=role
                )
                if tenant_id:
                    responses = responses.filter(tenant_id=tenant_id)
                
                if responses.exists():
                    total = responses.count()
                    promoters = responses.filter(score__gte=9).count()
                    detractors = responses.filter(score__lte=6).count()
                    nps = ((promoters - detractors) / total) * 100
                    segments[role] = round(nps, 1)
    
    elif segment_type == 'territory':
        # Get all territories
        territories = TenantMember.objects.filter(tenant_id=tenant_id).values_list(
            'territory__name', flat=True).distinct()
        
        for territory in territories:
            if territory:
                responses = NpsResponse.objects.filter(
                    account__tenant_member__territory__name=territory
                )
                if tenant_id:
                    responses = responses.filter(tenant_id=tenant_id)
                
                if responses.exists():
                    total = responses.count()
                    promoters = responses.filter(score__gte=9).count()
                    detractors = responses.filter(score__lte=6).count()
                    nps = ((promoters - detractors) / total) * 100
                    segments[territory] = round(nps, 1)
    
    return segments


def identify_promoter_referral_opportunities(tenant_id: str = None) -> list:
    """
    Identify potential promoter referral opportunities.
    
    Args:
        tenant_id: Optional tenant ID to filter by
        
    Returns:
        list: List of potential referral opportunities
    """
    # Find promoters with high scores and comments
    promoters = NpsResponse.objects.filter(score__gte=9).exclude(comment='')
    if tenant_id:
        promoters = promoters.filter(tenant_id=tenant_id)
    
    opportunities = []
    for response in promoters:
        opportunities.append({
            'response_id': response.id,
            'account_id': response.account_id,
            'account_email': response.account.email,
            'score': response.score,
            'comment': response.comment[:100] + '...' if len(response.comment) > 100 else response.comment,
            'survey_name': response.survey.nps_survey_name,
            'created_at': response.created_at
        })
    
    return opportunities