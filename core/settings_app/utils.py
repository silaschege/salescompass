from django.utils import timezone
from datetime import date
from .models import Setting, TeamMember, Quota
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import TeamMember
from automation.utils import emit_event

def get_setting_value(key: str, tenant_id: str = None):
    """Get setting value by key."""
    try:
        setting = Setting.objects.get(key=key, tenant_id=tenant_id)
        return setting.get_value()
    except Setting.DoesNotExist:
        # Return default based on key
        defaults = {
            'pipeline.stages': ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost'],
            'esg.threshold_high': 70,
            'esg.threshold_medium': 40,
            'automation.enabled': True,
            'account.tiers': ['bronze', 'silver', 'gold', 'platinum'],
        }
        return defaults.get(key)


def update_setting_value(key: str, value, user=None, reason: str = "", tenant_id: str = None):
    """Update setting value with audit logging."""
    setting = Setting.objects.get(key=key, tenant_id=tenant_id)
    
    old_value = str(setting.get_value())
    setting.set_value(value)
    setting.last_modified_by = user
    setting.save()
    
    # Log change
    SettingChangeLog.objects.create(
        setting=setting,
        old_value=old_value,
        new_value=str(value),
        changed_by=user,
        change_reason=reason,
        tenant_id=tenant_id
    )
    
    # Emit automation event
    from automation.utils import emit_event
    emit_event('crm_setting.changed', {
        'setting_key': key,
        'old_value': old_value,
        'new_value': str(value),
        'tenant_id': tenant_id,
    })


def calculate_quota_achievement(team_member_id: int):
    """Calculate current quota achievement."""
    team_member = TeamMember.objects.get(id=team_member_id)
    
    # Get current period
    today = date.today()
    if team_member.quota_period == 'monthly':
        period_start = today.replace(day=1)
        period_end = (period_start.replace(month=period_start.month % 12 + 1, day=1) - timedelta(days=1))
    elif team_member.quota_period == 'quarterly':
        quarter = (today.month - 1) // 3 + 1
        quarter_start_month = (quarter - 1) * 3 + 1
        period_start = today.replace(month=quarter_start_month, day=1)
        period_end = period_start.replace(month=period_start.month + 2, day=28)  # Approximate
    else:  # yearly
        period_start = today.replace(month=1, day=1)
        period_end = today.replace(month=12, day=31)
    
    # Get actual amount from opportunities
    from opportunities.models import Opportunity
    actual = Opportunity.objects.filter(
        owner=team_member.user,
        stage='closed_won',
        close_date__gte=period_start,
        close_date__lte=period_end
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Update or create quota record
    quota, created = Quota.objects.update_or_create(
        team_member=team_member,
        period_start=period_start,
        period_end=period_end,
        defaults={
            'amount': team_member.quota_amount or 0,
            'actual_amount': actual,
            'achieved_percent': (actual / team_member.quota_amount * 100) if team_member.quota_amount else 0
        }
    )
    
    return quota



def onboard_new_team_member(user_id: int) -> bool:
    """
    Execute comprehensive onboarding workflow for new team members.
    
    This function handles:
    - Welcome email sending
    - Default role assignment
    - Territory assignment
    - Training task creation
    - System notification generation
    - Automation event emission
    
    Args:
        user_id (int): ID of the User model instance
        
    Returns:
        bool: True if onboarding completed successfully, False otherwise
    """
    try:
        from core.models import User
        user = User.objects.get(id=user_id)
        
        # 1. Create or get TeamMember profile
        team_member, created = TeamMember.objects.get_or_create(
            user=user,
            defaults={
                'status': 'onboarding',
                'hire_date': timezone.now().date(),
                'tenant_id': user.tenant_id
            }
        )
        
        # 2. Assign default role if not already assigned
        if not team_member.role:
            from .models import TeamRole
            default_role = TeamRole.objects.filter(
                name='Sales Representative',
                tenant_id=user.tenant_id
            ).first()
            
            if not default_role:
                # Create default role if it doesn't exist
                default_role = TeamRole.objects.create(
                    name='Sales Representative',
                    description='Default role for new sales team members',
                    base_permissions=['accounts:read', 'opportunities:read', 'leads:read'],
                    tenant_id=user.tenant_id
                )
            
            team_member.role = default_role
            team_member.save(update_fields=['role'])
        
        # 3. Assign territory based on user's location or round-robin
        if not team_member.territory:
            _assign_territory(team_member)
        
        # 4. Send welcome email
        _send_welcome_email(user, team_member)
        
        # 5. Create onboarding tasks
        _create_onboarding_tasks(user, team_member)
        
        # 6. Emit automation event for additional workflows
        emit_event('team.member_onboarded', {
            'user_id': user.id,
            'team_member_id': team_member.id,
            'email': user.email,
            'role': team_member.role.name if team_member.role else None,
            'territory': team_member.territory.name if team_member.territory else None,
            'tenant_id': user.tenant_id,
            'onboarding_date': timezone.now().isoformat()
        })
        
        # 7. Log onboarding completion
        from .models import SettingChangeLog
        SettingChangeLog.objects.create(
            setting=None,  # No specific setting changed
            old_value="",
            new_value=f"Team member {user.email} onboarded",
            changed_by=user,
            change_reason="Automatic onboarding workflow",
            tenant_id=user.tenant_id
        )
        
        return True
        
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error onboarding team member {user_id}: {str(e)}")
        return False


def _assign_territory(team_member: TeamMember) -> None:
    """
    Assign territory to team member using round-robin or location-based logic.
    """
    from .models import Territory
    
    # Get all active territories for the tenant
    territories = Territory.objects.filter(
        tenant_id=team_member.tenant_id,
        is_active=True
    ).order_by('id')
    
    if territories.exists():
        # Simple round-robin assignment based on team member count
        team_count = TeamMember.objects.filter(
            tenant_id=team_member.tenant_id,
            status__in=['active', 'onboarding']
        ).count()
        
        territory_index = (team_count - 1) % territories.count()
        team_member.territory = territories[territory_index]
        team_member.save(update_fields=['territory'])


def _send_welcome_email(user: 'User', team_member: TeamMember) -> None:
    """
    Send personalized welcome email to new team member.
    """
    # Get manager email if available
    manager_email = "admin@salescompass.com"
    if team_member.manager and team_member.manager.user:
        manager_email = team_member.manager.user.email
    
    # Render email template
    html_content = render_to_string('crm_settings/welcome_email.html', {
        'user': user,
        'team_member': team_member,
        'manager_email': manager_email,
        'company_name': getattr(settings, 'COMPANY_NAME', 'SalesCompass')
    })
    
    # Send email
    send_mail(
        subject=f"Welcome to {getattr(settings, 'COMPANY_NAME', 'SalesCompass')}!",
        message="Welcome to our team! Please view in HTML.",
        html_message=html_content,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salescompass.com'),
        recipient_list=[user.email],
        fail_silently=True
    )


# def _create_onboarding_tasks(user: 'User', team_member: TeamMember) -> None:
#     """
#     Create initial onboarding tasks for the new team member.
#     """
#     try:
#         # Only create tasks if the Tasks app is available
#         from apps.tasks.models import Task
        
#         onboarding_tasks = [
#             {
#                 'title': 'Complete Profile Setup',
#                 'description': 'Update your profile information and upload your photo',
#                 'due_date': timezone.now().date() + timezone.timedelta(days=2)
#             },
#             {
#                 'title': 'Review Team Documentation',
#                 'description': 'Read through team processes and CRM guidelines',
#                 'due_date': timezone.now().date() + timezone.timedelta(days=5)
#             },
#             {
#                 'title': 'Schedule Manager Meeting',
#                 'description': 'Set up your first 1:1 meeting with your manager',
#                 'due_date': timezone.now().date() + timezone.timedelta(days=3)
#             },
#             {
#                 'title': 'CRM Training Completion',
    #             'description': 'Complete the SalesCompass CRM training modules',
    #             'due_date': timezone.now().date() + timezone.timedelta(days=14)
    #         }
    #     ]
        
    #     for task_data in onboarding_tasks:
    #         Task.objects.create(
    #             title=task_data['title'],
    #             description=task_data['description'],
    #             assigned_to=user,
    #             due_date=task_data['due_date'],
    #             priority='high',
    #             status='todo',
    #             tenant_id=user.tenant_id
    #         )
            
    # except ImportError:
    #     # Tasks app not installed, skip task creation
    #     pass


def complete_team_member_onboarding(team_member_id: int) -> bool:
    """
    Complete the onboarding process for a team member.
    
    Args:
        team_member_id (int): ID of the TeamMember instance
        
    Returns:
        bool: True if completion successful, False otherwise
    """
    try:
        team_member = TeamMember.objects.get(id=team_member_id)
        team_member.status = 'active'
        team_member.save(update_fields=['status'])
        
        # Emit completion event
        emit_event('team.onboarding_completed', {
            'team_member_id': team_member.id,
            'user_id': team_member.user.id,
            'email': team_member.user.email,
            'tenant_id': team_member.tenant_id
        })
        
        return True
        
    except TeamMember.DoesNotExist:
        return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error completing onboarding for team member {team_member_id}: {str(e)}")
        return False


def assign_team_member_quota(team_member_id: int, amount: float, period: str = 'quarterly') -> bool:
    """
    Assign quota to a team member.
    
    Args:
        team_member_id (int): ID of the TeamMember instance
        amount (float): Quota amount
        period (str): Quota period ('monthly', 'quarterly', 'yearly')
        
    Returns:
        bool: True if quota assigned successfully, False otherwise
    """
    try:
        team_member = TeamMember.objects.get(id=team_member_id)
        team_member.quota_amount = amount
        team_member.quota_period = period
        team_member.save(update_fields=['quota_amount', 'quota_period'])
        
        return True
        
    except TeamMember.DoesNotExist:
        return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error assigning quota to team member {team_member_id}: {str(e)}")
        return False