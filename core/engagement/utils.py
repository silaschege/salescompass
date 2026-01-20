from django.utils import timezone
from datetime import timedelta
import logging
from .models import EngagementEvent, EngagementStatus
 
logger = logging.getLogger(__name__)

# Decay configuration
# Reduce score by DECAY_RATE percent for every DECAY_PERIOD_DAYS of inactivity
DECAY_RATE = 0.05  # 5% decay
DECAY_PERIOD_DAYS = 7
INACTIVITY_THRESHOLD_DAYS = 14

# Enhanced scoring weights based on event types
SCORE_WEIGHTS = {
    'email_opened': 1,
    'link_clicked': 2,
    'proposal_viewed': 5,
    'demo_completed': 10,
    'content_downloaded': 3,
    'task_lead_contact_completed': 3,
    'task_lead_review_completed': 2,
    'task_lead_qualify_completed': 4,
    'task_opportunity_demo_completed': 8,
    'task_case_escalation_completed': 2,
    'task_user_followup_completed': 3,
    'task_proposal_followup_completed': 4,
    'lead_created': 2,
    'lead_contacted': 3,
    'user_followup_completed': 3,
    'case_escalation_handled': 4,
    'detractor_followup_completed': 3,
    'renewal_reminder': 2,
    'nps_submitted': 5,
    'social_interaction': 2,
    'website_visit': 1,
    'document_view': 2,
    'webinar_attended': 6,
    'support_ticket': 1,
    'video_viewed': 3,
    'video_watched_full': 5,
    'forum_post_created': 2,
    'forum_reply_created': 1,
    'product_usage_session': 4,
    'feature_used': 2,
    'login_event': 1,
    'page_view_duration': 1,

    # Cross-Module Integration Weights
    'whatsapp_sent': 2,
    'whatsapp_received': 3,  # Higher weight for customer response
    'whatsapp_read': 1,      # Message was read by recipient
    'linkedin_inmail_tracked': 3,
    'payment_received': 8,
    'course_completed': 5,
    'win_probability_update': 4,
    'task_overdue': -5,  # Penalty for inaction
    'task_assigned': 1,
    'support_ticket_created': 1,
}

def calculate_engagement_score(account, tenant_id=None):
    """
    Recalculate the engagement score for a given account.
    Considers recent events and applies time-based decay.
    Now uses tenant-specific configurations if available.
    """
    from .models import EngagementScoringConfig, ScoringRule
    
    # 1. Load configuration
    config = None
    if tenant_id:
        config = EngagementScoringConfig.objects.filter(tenant_id=tenant_id).first()
    
    # Use config values or defaults
    rolling_window = config.rolling_window_days if config else 30
    decay_rate = float(config.decay_rate) if config else DECAY_RATE
    decay_period = config.decay_period_days if config else DECAY_PERIOD_DAYS
    inactivity_threshold = config.inactivity_threshold_days if config else INACTIVITY_THRESHOLD_DAYS
    
    # Load scoring rules for weights
    weights = SCORE_WEIGHTS.copy()
    if tenant_id:
        rules = ScoringRule.objects.filter(tenant_id=tenant_id, rule_is_active=True)
        for rule in rules:
            weights[rule.event_type] = float(rule.weight)

    # 2. Base Score from recent events
    cutoff_date = timezone.now() - timedelta(days=rolling_window)
    events_query = EngagementEvent.objects.filter(
        account=account,
        created_at__gte=cutoff_date
    )
    
    if tenant_id:
        events_query = events_query.filter(tenant_id=tenant_id)
        
    events = events_query.all()
    
    # Weighted scoring logic
    base_score = 0
    for event in events:
        weight = weights.get(event.event_type, 1)
        base_score += weight + (event.engagement_score * 0.1)
        
    # Cap base score at 100
    final_score = min(base_score, 100.0)
    
    # 3. Apply Decay if inactive
    status, created = EngagementStatus.objects.get_or_create(account=account)
    
    last_activity = status.last_engaged_at
    if not last_activity:
        latest_event_query = EngagementEvent.objects.filter(account=account)
        if tenant_id:
            latest_event_query = latest_event_query.filter(tenant_id=tenant_id)
            
        latest_event = latest_event_query.order_by('-created_at').first()
        if latest_event:
            last_activity = latest_event.created_at
            status.last_engaged_at = last_activity
            status.save()
            
    if last_activity:
        days_inactive = (timezone.now() - last_activity).days
        
        if days_inactive > inactivity_threshold:
            decay_periods = (days_inactive - inactivity_threshold) // decay_period
            if decay_periods > 0:
                decay_factor = (1 - decay_rate) ** decay_periods
                final_score = final_score * decay_factor
                
    return round(final_score, 2)

def log_website_visit(user, page_url, duration_sec=None, tenant_id=None):
    """Log a website visit event."""
    return log_engagement_event(
        tenant_id=tenant_id or getattr(user, 'tenant_id', None),
        event_type='website_visit',
        description=f"Visited page: {page_url}",
        account=user,
        title="Website Visit",
        metadata={'url': page_url, 'duration_sec': duration_sec} if duration_sec else {'url': page_url},
        engagement_score=SCORE_WEIGHTS.get('website_visit', 1)
    )

def log_document_interaction(user, document_name, action_type='view', tenant_id=None):
    """Log document interactions like view, download, or share."""
    event_type = 'document_view' if action_type == 'view' else 'content_downloaded'
    return log_engagement_event(
        tenant_id=tenant_id or getattr(user, 'tenant_id', None),
        event_type=event_type,
        description=f"{action_type.capitalize()}ed document: {document_name}",
        account=user,
        title=f"Document {action_type.capitalize()}",
        metadata={'document': document_name, 'action': action_type},
        engagement_score=SCORE_WEIGHTS.get(event_type, 2)
    )

def log_video_engagement(user, video_title, watch_time_sec, completed=False, tenant_id=None):
    """Log video engagement metrics."""
    event_type = 'video_watched_full' if completed else 'video_viewed'
    return log_engagement_event(
        tenant_id=tenant_id or getattr(user, 'tenant_id', None),
        event_type=event_type,
        description=f"{'Completed' if completed else 'Watched'} video: {video_title}",
        account=user,
        title="Video Engagement",
        metadata={'video': video_title, 'watch_time': watch_time_sec, 'completed': completed},
        engagement_score=SCORE_WEIGHTS.get(event_type, 3)
    )

def apply_decay_to_all_accounts(tenant_id=None):
    """
    Batch process to update engagement scores with decay.
    Should be run via Celery task.
    """
    # Iterate through all engagement statuses
    # In a real system, we'd batch this query
    statuses = EngagementStatus.objects.all()
    if tenant_id:
        statuses = statuses.filter(account__tenant_id=tenant_id)
        
    for status in statuses:
        new_score = calculate_engagement_score(status.account, tenant_id)
        
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
        'demo_completed', 'webinar_attended', 'video_watched_full',
        'forum_post_created', 'feature_used'
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
# ... existing code ...


def evaluate_engagement_workflows(event):
    """
    Evaluate and trigger engagement workflows based on an engagement event.
    """
    from .models import EngagementWorkflow, EngagementWorkflowExecution
    from django.utils import timezone
    from datetime import timedelta
    
    if not hasattr(event, 'tenant_id') or not event.tenant_id:
        return
    
    # Get active workflows for this tenant
    workflows = EngagementWorkflow.objects.filter(
        tenant_id=event.tenant_id, 
        engagement_work_flow_is_active=True
    )
    
    for workflow in workflows:
        should_trigger = False
        
        # Evaluate trigger conditions
        if workflow.trigger_condition == 'low_engagement' and event.engagement_score < 30:
            should_trigger = True
        elif workflow.trigger_condition == 'high_engagement' and event.engagement_score > 80:
            should_trigger = True
        elif workflow.trigger_condition == 'inactivity':
            # Check for inactivity (no events in last 7 days)
            week_ago = timezone.now() - timedelta(days=7)
            recent_events = EngagementEvent.objects.filter(
                account=event.account,
                tenant_id=event.tenant_id,
                created_at__gte=week_ago
            ).exclude(id=event.id)
            if not recent_events.exists():
                should_trigger = True
        elif workflow.trigger_condition == 'milestone' and event.is_important:
            should_trigger = True
        elif workflow.trigger_condition == 'nps_promoter' and event.event_type == 'nps_submitted' and event.nps_response and event.nps_response.score >= 9:
            should_trigger = True
        elif workflow.trigger_condition == 'nps_detractor' and event.event_type == 'nps_submitted' and event.nps_response and event.nps_response.score <= 6:
            should_trigger = True
            
        # Create execution if workflow is triggered
        if should_trigger:
            execution, created = EngagementWorkflowExecution.objects.get_or_create(
                workflow=workflow,
                engagement_event=event,
                account=event.account,
                tenant_id=event.tenant_id,
                defaults={
                    'status': 'pending'
                }
            )
            
            if created:
                # Process workflow based on type
                if workflow.workflow_type == 'email_sequence':
                    process_email_sequence_workflow(execution, workflow, event)
                elif workflow.workflow_type == 'task_creation':
                    process_task_creation_workflow(execution, workflow, event)
                elif workflow.workflow_type == 'escalation':
                    process_escalation_workflow(execution, workflow, event)


def process_email_sequence_workflow(execution, workflow, event):
    """
    Process email sequence workflow.
    """
    # Mark as in progress
    execution.status = 'in_progress'
    execution.save(update_fields=['status'])
    
    try:
        # In a real implementation, this would queue emails to be sent
        # according to the sequence defined in workflow.email_template_ids
        # with delays specified by workflow.delay_between_emails
        
        # For now, we'll just mark as completed
        execution.status = 'completed'
        execution.execution_data = {
            'message': 'Email sequence workflow triggered',
            'template_ids': workflow.email_template_ids,
            'account': event.account.id
        }
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'execution_data', 'completed_at'])
        
    except Exception as e:
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'error_message', 'completed_at'])


def process_task_creation_workflow(execution, workflow, event):
    """
    Process task creation workflow.
    """
    from tasks.models import Task
    
    execution.status = 'in_progress'
    execution.save(update_fields=['status'])
    
    try:
        # Create a task based on the workflow configuration
        due_date = timezone.now() + timedelta(days=workflow.task_due_date_offset)
        
        task = Task.objects.create(
            title=workflow.task_title_template.format(
                account_name=event.account.name,
                event_type=event.get_event_type_display()
            ) if workflow.task_title_template else f"Follow up on {event.get_event_type_display()}",
            task_description=workflow.task_description_template.format(
                account_name=event.account.name,
                event_type=event.get_event_type_display(),
                engagement_score=event.engagement_score
            ) if workflow.task_description_template else f"Engagement event: {event.get_event_type_display()} for {event.account.name}",
            account=event.account,
            due_date=due_date,
            priority=workflow.task_priority,
            tenant_id=execution.tenant_id,
            task_type='account_followup'
        )
        
        execution.status = 'completed'
        execution.execution_data = {
            'message': 'Task created successfully',
            'task_id': task.id,
            'account': event.account.id
        }
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'execution_data', 'completed_at'])
        
    except Exception as e:
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'error_message', 'completed_at'])


def process_escalation_workflow(execution, workflow, event):
    """
    Process escalation workflow.
    """
    execution.status = 'in_progress'
    execution.save(update_fields=['status'])
    
    try:
        # In a real implementation, this would send notifications to
        # escalation recipients after the specified delay
        
        execution.status = 'completed'
        execution.execution_data = {
            'message': 'Escalation workflow triggered',
            'recipients': workflow.escalation_recipients,
            'account': event.account.id
        }
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'execution_data', 'completed_at'])
        
    except Exception as e:
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save(update_fields=['status', 'error_message', 'completed_at'])


def integrate_with_automation_module(event):
    """
    Integrate with the existing automation module by emitting events
    that the automation engine can listen to.
    """
    from automation.utils import emit_event
    
    # Emit event for automation engine
    emit_event('engagement.workflow_triggered', {
        'event_id': event.id,
        'event_type': event.event_type,
        'account_id': event.account.id,
        'engagement_score': event.engagement_score,
        'tenant_id': event.tenant_id,
        'timestamp': event.created_at.isoformat()
    })


# Update the existing evaluate_auto_nba_rules function to also trigger workflows
def evaluate_auto_nba_rules(event):
    """
    Evaluate Auto NBA rules when an engagement event occurs.
    Creates Next Best Actions when rules are triggered.
    """
    from .models import AutoNBARule, NextBestAction
    from django.utils import timezone
    from datetime import timedelta
    
    if not hasattr(event, 'tenant_id') or not event.tenant_id:
        return
    
    # Get active rules for this tenant
    rules = AutoNBARule.objects.filter(tenant_id=event.tenant_id, auto_nba_is_active=True)
    
    for rule in rules:
        should_trigger = False
        
        # Evaluate rule trigger conditions
        if rule.trigger_event == 'low_engagement_score' and event.engagement_score < 30:
            should_trigger = True
        elif rule.trigger_event == 'no_engagement_7_days':
            # Check if this is the first event in 7 days
            week_ago = timezone.now() - timedelta(days=7)
            recent_events = EngagementEvent.objects.filter(
                account=event.account,
                tenant_id=event.tenant_id,
                created_at__gte=week_ago,
                created_at__lt=event.created_at
            )
            if not recent_events.exists():
                should_trigger = True
        elif rule.trigger_event == 'proposal_viewed' and event.event_type == 'proposal_viewed':
            should_trigger = True
        elif rule.trigger_event == 'high_engagement_score' and event.engagement_score > 80:
            should_trigger = True
        elif rule.trigger_event == 'nps_submitted_promoter' and event.event_type == 'nps_submitted' and event.nps_response and event.nps_response.score >= 9:
            should_trigger = True
        elif rule.trigger_event == 'nps_submitted_detractor' and event.event_type == 'nps_submitted' and event.nps_response and event.nps_response.score <= 6:
            should_trigger = True
        elif rule.trigger_event == 'email_opened' and event.event_type == 'email_opened':
            should_trigger = True
        elif rule.trigger_event == 'link_clicked' and event.event_type == 'link_clicked':
            should_trigger = True
            
        # Create NBA if rule is triggered
        if should_trigger:
            nba_params = {
                'account': event.account,
                'action_type': rule.action_type,
                'description': rule.description_template.format(
                    account_name=event.account.name,
                    engagement_score=event.engagement_score,
                    event_type=event.get_event_type_display()
                ),
                'due_date': timezone.now() + timedelta(days=rule.due_in_days),
                'priority': rule.priority,
                'tenant_id': event.tenant_id,
                'source': f'Auto NBA Rule: {rule.rule_name}'
            }
            
            # Assign to creator if specified
            if rule.assigned_to_creator and event.created_by:
                nba_params['assigned_to'] = event.created_by
            else:
                # Could assign to account owner or default user
                nba_params['assigned_to'] = event.account  # Simplified assignment
            
            NextBestAction.objects.create(**nba_params)
    
    # Also evaluate engagement workflows
    evaluate_engagement_workflows(event)
    
    # Integrate with automation module
    integrate_with_automation_module(event)




def process_mentions(content, tenant_id):
    """
    Process @mentions in content and return content with links and list of mentioned users.
    """
    import re
    from core.models import User
    
    # Pattern to match @username mentions
    mention_pattern = r'@(\w+)'
    
    # Find all mentions
    mentions = re.findall(mention_pattern, content)
    mentioned_users = []
    
    # Replace mentions with links
    def replace_mention(match):
        username = match.group(1)
        try:
            user = User.objects.get(username=username, tenant_id=tenant_id)
            mentioned_users.append(user)
            # Return HTML link to user profile (you can customize this)
            return f'<a href="#" class="mention" data-user-id="{user.id}">@{username}</a>'
        except User.DoesNotExist:
            # If user doesn't exist, return the original mention
            return f'@{username}'
    
    # Process content and replace mentions
    processed_content = re.sub(mention_pattern, replace_mention, content)
    
    return processed_content, mentioned_users

def process_utm_parameters(request, engagement_event):
    """
    Process UTM parameters from request and update engagement event.
    """
    # Extract UTM parameters from request
    utm_source = request.GET.get('utm_source') or request.POST.get('utm_source')
    utm_medium = request.GET.get('utm_medium') or request.POST.get('utm_medium')
    utm_campaign = request.GET.get('utm_campaign') or request.POST.get('utm_campaign')
    utm_term = request.GET.get('utm_term') or request.POST.get('utm_term')
    utm_content = request.GET.get('utm_content') or request.POST.get('utm_content')
    
    # Extract referrer information
    referrer_url = request.META.get('HTTP_REFERER')
    referring_domain = None
    if referrer_url:
        from urllib.parse import urlparse
        try:
            parsed_url = urlparse(referrer_url)
            referring_domain = parsed_url.netloc
        except:
            pass
    
    # Update engagement event with attribution data
    if utm_source:
        engagement_event.utm_source = utm_source
    if utm_medium:
        engagement_event.utm_medium = utm_medium
    if utm_campaign:
        engagement_event.utm_campaign = utm_campaign
    if utm_term:
        engagement_event.utm_term = utm_term
    if utm_content:
        engagement_event.utm_content = utm_content
    if referrer_url:
        engagement_event.referrer_url = referrer_url
    if referring_domain:
        engagement_event.referring_domain = referring_domain

def get_attribution_data(engagement_event):
    """
    Get attribution data for an engagement event.
    Returns a dictionary with attribution information.
    """
    return {
        'utm_source': engagement_event.utm_source,
        'utm_medium': engagement_event.utm_medium,
        'utm_campaign': engagement_event.utm_campaign,
        'utm_term': engagement_event.utm_term,
        'utm_content': engagement_event.utm_content,
        'referrer_url': engagement_event.referrer_url,
        'referring_domain': engagement_event.referring_domain,
        'campaign_name': engagement_event.campaign_name,
        'campaign_source': engagement_event.campaign_source,
    }

def calculate_attribution_value(engagement_event):
    """
    Calculate the attributed value of an engagement event based on its type and score.
    This is a simplified model that can be expanded based on business requirements.
    """
    # Base values for different event types
    event_values = {
        'email_opened': 1.0,
        'link_clicked': 2.0,
        'proposal_viewed': 10.0,
        'demo_completed': 25.0,
        'content_downloaded': 5.0,
        'webinar_attended': 15.0,
        'nps_submitted': 8.0,
        'social_interaction': 3.0,
        'website_visit': 0.5,
        'document_view': 2.0,
    }
    
    # Get base value for event type
    base_value = event_values.get(engagement_event.event_type, 1.0)
    
    # Adjust based on engagement score (0-100)
    score_multiplier = engagement_event.engagement_score / 100.0
    
    return base_value * (1 + score_multiplier)

def get_multi_touch_attribution(account, days=30):
    """
    Calculate multi-touch attribution for an account over a specified period.
    Uses a linear attribution model (equal credit to all touchpoints).
    """
    from django.utils import timezone
    from datetime import timedelta
    from collections import defaultdict
    
    # Get events in timeframe
    cutoff_date = timezone.now() - timedelta(days=days)
    events = EngagementEvent.objects.filter(
        account=account,
        created_at__gte=cutoff_date
    ).order_by('created_at')
    
    if not events.exists():
        return {}
    
    # Group events by campaign/source
    campaign_touchpoints = defaultdict(list)
    
    for event in events:
        # Try to identify campaign/source
        identifier = None
        if event.utm_campaign:
            identifier = f"Campaign: {event.utm_campaign}"
        elif event.utm_source:
            identifier = f"Source: {event.utm_source}"
        elif event.referring_domain:
            identifier = f"Domain: {event.referring_domain}"
        else:
            identifier = "Direct"
            
        campaign_touchpoints[identifier].append(event)
    
    # Calculate linear attribution (equal credit to all touchpoints)
    total_touchpoints = sum(len(events) for events in campaign_touchpoints.values())
    attribution_results = {}
    
    for identifier, events in campaign_touchpoints.items():
        # Each touchpoint gets equal credit
        touchpoint_credit = 1.0 / total_touchpoints if total_touchpoints > 0 else 0
        total_credit = len(events) * touchpoint_credit
        
        # Calculate value contributed
        total_value = sum(calculate_attribution_value(event) for event in events)
        attributed_value = total_value * touchpoint_credit * len(events)
        
        attribution_results[identifier] = {
            'touchpoints': len(events),
            'credit_share': total_credit * 100,  # Percentage
            'attributed_value': attributed_value,
        }
    
    return attribution_results
def log_engagement_event(tenant_id, event_type, description, **kwargs):
    """
    Centralized helper for logging engagement events from any module.
    Automatically handles common fields and allows overriding/adding others via kwargs.
    """
    params = {
        'tenant_id': tenant_id,
        'event_type': event_type,
        'description': description,
    }
    params.update(kwargs)
    
    event = EngagementEvent.objects.create(**params)
    logger.info(f"Engagement Event Logged: {event_type} for Tenant {tenant_id}")
    return event


def calculate_company_engagement_score(company, tenant_id=None):
    """
    Recalculate the engagement score for a business Account (Company).
    Considers events linked to the account_company and its contacts.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    
    # Events directly linked to the company
    events_query = EngagementEvent.objects.filter(
        account_company=company,
        created_at__gte=cutoff_date
    )
    
    if tenant_id:
        events_query = events_query.filter(tenant_id=tenant_id)
        
    events = events_query.all()
    
    base_score = 0
    for event in events:
        weight = SCORE_WEIGHTS.get(event.event_type, 1)
        base_score += weight + (event.engagement_score * 0.1)
        
    return round(min(base_score, 100.0), 2)


def calculate_lead_engagement_score(lead, tenant_id=None):
    """
    Recalculate the engagement score for a Lead.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    
    events_query = EngagementEvent.objects.filter(
        lead=lead,
        created_at__gte=cutoff_date
    )
    
    if tenant_id:
        events_query = events_query.filter(tenant_id=tenant_id)
        
    events = events_query.all()
    
    base_score = 0
    for event in events:
        weight = SCORE_WEIGHTS.get(event.event_type, 1)
        base_score += weight + (event.engagement_score * 0.1)
        
    return round(min(base_score, 100.0), 2)


