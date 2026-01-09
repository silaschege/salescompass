from django.utils import timezone
from datetime import date
from .models import Setting, SettingChangeLog
from commissions.models import Quota
from tenants.models import TenantMember, TenantRole, TenantTerritory
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from automation.utils import emit_event
from django.db import models

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
    emit_event('crm_setting.changed', {
        'setting_key': key,
        'old_value': old_value,
        'new_value': str(value),
        'tenant_id': tenant_id,
    })


def calculate_quota_achievement(team_member_id: int):
    """Calculate current quota achievement."""
    team_member = TenantMember.objects.get(id=team_member_id)
    
    # Get current period
    today = date.today()
    from datetime import timedelta
    if team_member.quota_period == 'monthly':
        period_start = today.replace(day=1)
        next_month = today.month % 12 + 1
        next_month_year = today.year + (1 if today.month == 12 else 0)
        period_end = date(next_month_year, next_month, 1) - timedelta(days=1)
    elif team_member.quota_period == 'quarterly':
        quarter = (today.month - 1) // 3 + 1
        quarter_start_month = (quarter - 1) * 3 + 1
        period_start = today.replace(month=quarter_start_month, day=1)
        period_end = period_start.replace(month=period_start.month + 2, day=28)  # Approximate
    else:  # yearly
        period_start = today.replace(month=1, day=1)
        period_end = today.replace(month=12, day=31)
    
    # Get actual amount from opportunities
    # Update or create quota record
    quota, created = Quota.objects.update_or_create(
        user=team_member.user,
        period_start=period_start,
        period_end=period_end,
        defaults={
            'target_amount': team_member.quota_amount or 1, # Default to 1 to avoid div by zero if not set
            'tenant_id': team_member.tenant_id
        }
    )
    
    # Calculate achievement
    from opportunities.models import Opportunity
    actual = Opportunity.objects.filter(
        owner=team_member.user,
        stage__is_won=True,
        close_date__gte=period_start,
        close_date__lte=period_end
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    # We might want to store attainment somewhere or return it
    # Note: Quota model doesn't seem to have attainment field, it's a target record.
    # The calculate_quota_achievement function return the quota object.
    
    return quota


def onboard_new_team_member(user_id: int) -> bool:
    """
    Execute comprehensive onboarding workflow for new team members.
    """
    try:
        from core.models import User
        user = User.objects.get(id=user_id)
        
        # 1. Create or get TenantMember profile
        team_member, created = TenantMember.objects.get_or_create(
            user=user,
            defaults={
                'status': 'onboarding',
                'hire_date': timezone.now().date(),
                'tenant_id': user.tenant_id
            }
        )
        
        if not team_member.role:
            default_role = TenantRole.objects.filter(
                name='sales_rep',
                tenant_id=user.tenant_id
            ).first()
            
            if not default_role:
                default_role = TenantRole.objects.create(
                    name='sales_rep',
                    description='Sales Representative',
                    is_system_role=True,
                    tenant_id=user.tenant_id
                )
            
            team_member.role = default_role
            team_member.save(update_fields=['role'])
        
        # 3. Assign territory
        _assign_territory(team_member)
        
        # 4. Send welcome email
        _send_welcome_email(user, team_member)
        
        # 5. Create onboarding tasks
        _create_onboarding_tasks(user, team_member)
        
        # 6. Enroll in onboarding courses
        _enroll_in_onboarding_courses(user)
        
        # 7. Emit automation event
        emit_event('team.member_onboarded', {
            'user_id': user.id,
            'team_member_id': team_member.id,
            'email': user.email,
            'tenant_id': user.tenant_id
        })
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error onboarding team member {user_id}: {str(e)}")
        return False


def _assign_territory(team_member: TenantMember) -> None:
    territories = TenantTerritory.objects.filter(tenant_id=team_member.tenant_id, is_active=True).order_by('id')
    if territories.exists():
        team_count = TenantMember.objects.filter(tenant_id=team_member.tenant_id, status__in=['active', 'onboarding']).count()
        territory_index = (team_count - 1) % territories.count()
        team_member.territory = territories[territory_index]
        team_member.save(update_fields=['territory'])


def _send_welcome_email(user, team_member):
    manager_email = "admin@salescompass.com"
    if team_member.manager and team_member.manager.user:
        manager_email = team_member.manager.user.email
    
    html_content = render_to_string('crm_settings/welcome_email.html', {
        'user': user,
        'team_member': team_member,
        'manager_email': manager_email,
        'company_name': getattr(settings, 'COMPANY_NAME', 'SalesCompass')
    })
    
    send_mail(
        subject=f"Welcome to {getattr(settings, 'COMPANY_NAME', 'SalesCompass')}!",
        message="Welcome to our team!",
        html_message=html_content,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salescompass.com'),
        recipient_list=[user.email],
        fail_silently=True
    )


def _enroll_in_onboarding_courses(user):
    try:
        from core.learn.models import Course, UserProgress, Category
        onboarding_categories = Category.objects.filter(category_name__icontains='onboarding', tenant_id=user.tenant_id)
        onboarding_courses = Course.objects.filter(category__in=onboarding_categories, status='published', tenant_id=user.tenant_id)
        
        for course in onboarding_courses:
            first_lesson = course.lessons.order_by('order_in_course').first()
            if first_lesson:
                UserProgress.objects.get_or_create(
                    user=user,
                    course=course,
                    lesson=first_lesson,
                    tenant_id=user.tenant_id,
                    defaults={'completion_status': 'not_started'}
                )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error enrolling user {user.id} in onboarding courses: {str(e)}")


def _create_onboarding_tasks(user, team_member):
    try:
        from apps.tasks.models import Task
        onboarding_tasks = [
            {'title': 'Complete Profile Setup', 'description': 'Update your profile information', 'days': 2},
            {'title': 'Review Team Documentation', 'description': 'Read guidelines', 'days': 5},
            {'title': 'CRM Training Completion', 'description': 'Complete training modules in Learn section', 'days': 14}
        ]
        for t in onboarding_tasks:
            Task.objects.create(
                title=t['title'],
                description=t['description'],
                assigned_to=user,
                due_date=timezone.now().date() + timezone.timedelta(days=t['days']),
                priority='high',
                status='todo',
                tenant_id=user.tenant_id
            )
    except Exception:
        pass


def complete_team_member_onboarding(team_member_id: int) -> bool:
    try:
        team_member = TenantMember.objects.get(id=team_member_id)
        team_member.status = 'active'
        team_member.save(update_fields=['status'])
        emit_event('team.onboarding_completed', {'team_member_id': team_member.id, 'user_id': team_member.user.id})
        return True
    except Exception:
        return False