"""
Utility functions for global alerts module.
Provides helpers for alert filtering, delivery, dismissal, and analytics.
"""
from django.utils import timezone
from django.db.models import Count, Q
from .models import Alert


def get_alerts_for_tenant(tenant_id, include_global=True):
    """
    Get all active alerts for a specific tenant.
    
    Args:
        tenant_id: Tenant ID
        include_global: Include global alerts (default True)
    
    Returns:
        QuerySet of active alerts
    """
    return Alert.get_active_alerts_for_tenant(tenant_id if include_global else None)


def get_active_alerts():
    """
    Get all currently active alerts.
    
    Returns:
        QuerySet of active alerts
    """
    now = timezone.now()
    return Alert.objects.filter(
        is_active=True,
        start_time__lte=now
    ).filter(
        Q(end_time__isnull=True) | Q(end_time__gte=now)
    )


def get_scheduled_alerts():
    """
    Get alerts scheduled for the future.
    
    Returns:
        QuerySet of scheduled alerts
    """
    now = timezone.now()
    return Alert.objects.filter(
        is_active=True,
        start_time__gt=now
    )


def get_alerts_by_type(alert_type):
    """
    Get alerts filtered by type.
    
    Args:
        alert_type: Alert type ('maintenance', 'outage', etc.)
    
    Returns:
        QuerySet of alerts
    """
    return Alert.objects.filter(alert_type=alert_type, is_active=True)


def get_alerts_by_severity(severity):
    """
    Get alerts filtered by severity.
    
    Args:
        severity: Severity level ('info', 'warning', 'critical')
    
    Returns:
        QuerySet of alerts
    """
    return Alert.objects.filter(severity=severity, is_active=True)


def get_global_alerts():
    """
    Get all global alerts.
    
    Returns:
        QuerySet of global alerts
    """
    return Alert.objects.filter(is_global=True, is_active=True)


def get_tenant_specific_alerts():
    """
    Get all tenant-specific alerts.
    
    Returns:
        QuerySet of tenant-specific alerts
    """
    return Alert.objects.filter(is_global=False, is_active=True)


def create_alert(title, message, alert_type='general', severity='info', 
                created_by='admin', **kwargs):
    """
    Create a new alert.
    
    Args:
        title: Alert title
        message: Alert message
        alert_type: Type of alert
        severity: Severity level
        created_by: User who created the alert
        **kwargs: Additional alert parameters
    
    Returns:
        Alert instance
    """
    alert = Alert.objects.create(
        title=title,
        message=message,
        alert_type=alert_type,
        severity=severity,
        created_by=created_by,
        **kwargs
    )
    return alert


def schedule_alert(title, message, start_time, end_time=None, **kwargs):
    """
    Schedule an alert for future display.
    
    Args:
        title: Alert title
        message: Alert message
        start_time: When to start showing the alert
        end_time: When to stop showing the alert (optional)
        **kwargs: Additional alert parameters
    
    Returns:
        Alert instance
    """
    return create_alert(
        title=title,
        message=message,
        start_time=start_time,
        end_time=end_time,
        **kwargs
    )


def dismiss_alert_for_user(user, alert):
    """
    Mark an alert as dismissed for a specific user.
    Note: This is a placeholder - you'd need to implement a UserAlertDismissal model
    to properly track dismissals per user.
    
    Args:
        user: User instance
        alert: Alert instance
    
    Returns:
        bool: Success status
    """
    # TODO: Implement UserAlertDismissal tracking
    return True


def get_alert_statistics():
    """
    Get statistics about alerts.
    
    Returns:
        dict: Alert statistics
    """
    total_alerts = Alert.objects.count()
    active_alerts = get_active_alerts().count()
    scheduled_alerts = get_scheduled_alerts().count()
    
    # Breakdown by type
    type_breakdown = Alert.objects.values('alert_type').annotate(
        count=Count('id')
    )
    
    # Breakdown by severity
    severity_breakdown = Alert.objects.values('severity').annotate(
        count=Count('id')
    )
    
    return {
        'total_alerts': total_alerts,
        'active_alerts': active_alerts,
        'scheduled_alerts': scheduled_alerts,
        'inactive_alerts': total_alerts - active_alerts - scheduled_alerts,
        'type_breakdown': list(type_breakdown),
        'severity_breakdown': list(severity_breakdown),
        'global_alerts': Alert.objects.filter(is_global=True).count(),
        'tenant_specific_alerts': Alert.objects.filter(is_global=False).count(),
    }


def get_upcoming_alerts(days=7):
    """
    Get alerts scheduled to start in the next N days.
    
    Args:
        days: Number of days to look ahead
    
    Returns:
        QuerySet of upcoming alerts
    """
    now = timezone.now()
    future_date = now + timezone.timedelta(days=days)
    
    return Alert.objects.filter(
        is_active=True,
        start_time__gte=now,
        start_time__lte=future_date
    )


def get_expired_alerts():
    """
    Get alerts that have expired (past end_time).
    
    Returns:
        QuerySet of expired alerts
    """
    now = timezone.now()
    return Alert.objects.filter(
        end_time__isnull=False,
        end_time__lt=now
    )


def bulk_deactivate_alerts(alert_ids):
    """
    Deactivate multiple alerts at once.
    
    Args:
        alert_ids: List of alert IDs
    
    Returns:
        int: Number of alerts deactivated
    """
    return Alert.objects.filter(id__in=alert_ids).update(is_active=False)


def get_critical_alerts():
    """
    Get all critical severity alerts.
    
    Returns:
        QuerySet of critical alerts
    """
    return get_alerts_by_severity('critical')


def validate_alert_targeting(is_global, target_tenant_ids):
    """
    Validate alert targeting configuration.
    
    Args:
        is_global: Boolean indicating if alert is global
        target_tenant_ids: List of target tenant IDs
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if is_global and target_tenant_ids:
        return False, "Global alerts cannot have specific tenant targets"
    
    if not is_global and not target_tenant_ids:
        return False, "Non-global alerts must specify target tenants"
    
    return True, None
