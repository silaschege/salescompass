"""
Core Utilities for SalesCompass CRM

Provides:
- Business metrics calculations
- Utility functions for multi-tenancy
- Common helper functions used throughout the application
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from core.models import (
    User, SystemConfiguration, SystemEventLog, SystemHealthCheck, 
    MaintenanceWindow, PerformanceMetric, SystemNotification
)

logger = logging.getLogger(__name__)


# === Business Metrics Utilities ===

def calculate_clv_simple(user: User) -> float:
    """
    Calculate Customer Lifetime Value using the simple formula:
    CLV = Average Order Value × Purchase Frequency × Customer Lifespan
    
    Args:
        user: User instance to calculate CLV for
        
    Returns:
        float: Calculated CLV value
    """
    avg_order_value = user.avg_order_value or 0
    purchase_frequency = user.purchase_frequency or 0
    
    # Calculate customer lifespan in years
    if user.customer_since:
        customer_start = user.customer_since
    else:
        customer_start = user.date_joined.date()
    
    tenure_days = (timezone.now().date() - customer_start).days
    customer_lifespan = max(0.5, tenure_days / 365.0)
    
    clv = float(avg_order_value) * purchase_frequency * customer_lifespan
    return max(0.0, clv)


def calculate_customer_lifespan(user: User) -> float:
    """
    Calculate the average customer lifespan in years.
    
    Args:
        user: User instance
        
    Returns:
        float: Customer lifespan in years
    """
    if not user.customer_since:
        customer_start = user.date_joined.date()
    else:
        customer_start = user.customer_since
    
    from datetime import date
    today = date.today()
    tenure_days = (today - customer_start).days
    
    # For customers with more than 2 years of tenure, we'll use actual tenure
    # For newer customers, we'll use a projected average based on retention
    if tenure_days > 730:  # More than 2 years
        return tenure_days / 365.0
    else:
        # For newer customers, estimate based on retention rate
        retention_rate = float(user.retention_rate or 0.85)
        if retention_rate > 0 and retention_rate < 1:
            # Inverse of churn rate as a simple lifetime calculation
            # Churn rate = 1 - retention_rate
            # Average lifetime = 1 / churn_rate
            churn_rate = 1 - retention_rate
            if churn_rate > 0:
                return min(10.0, 1 / churn_rate)  # Cap at 10 years
        return max(0.5, tenure_days / 365.0)


def calculate_roi(user: User, expected_revenue: Optional[float] = None) -> float:
    """
    Calculate ROI: (Expected Revenue - CAC) / CAC
    
    Args:
        user: User instance
        expected_revenue: Expected revenue (defaults to calculated CLV if not provided)
        
    Returns:
        float: ROI value
    """
    cac = user.acquisition_cost or 0
    if expected_revenue is None:
        # Use calculated CLV as expected revenue if not provided
        expected_revenue = user.customer_lifetime_value or calculate_clv_simple(user)
    
    if cac == 0:
        # Avoid division by zero
        return float('inf') if expected_revenue > 0 else 0
    
    roi = (expected_revenue - cac) / cac
    return roi


# === System Configuration Utilities ===

def get_system_config(key: str, default: Any = None) -> Any:
    """
    Get a system configuration value by key.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    try:
        config = SystemConfiguration.objects.get(key=key)
        return config.value
    except SystemConfiguration.DoesNotExist:
        return default


def set_system_config(key: str, value: Any, description: str = "", 
                      data_type: str = "string", category: str = "general") -> None:
    """
    Set a system configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
        description: Description of the configuration
        data_type: Data type of the value
        category: Category of the configuration
    """
    SystemConfiguration.objects.update_or_create(
        key=key,
        defaults={
            'value': str(value),
            'description': description,
            'data_type': data_type,
            'category': category
        }
    )


# === Tenant Utilities ===

def get_tenant_statistics(tenant_id: str) -> Dict[str, Any]:
    """
    Get statistics for a tenant.
    
    Args:
        tenant_id: ID of the tenant
        
    Returns:
        Dictionary with tenant statistics
    """
    stats = {
        'total_users': User.objects.filter(tenant_id=tenant_id).count(),
        'active_users': User.objects.filter(tenant_id=tenant_id, is_active=True).count(),
    }
    return stats


# === Date/Time Utilities ===

def get_date_range(start_date: datetime, end_date: datetime) -> list:
    """
    Get a list of dates between start_date and end_date.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List of dates
    """
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    return date_list


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


# === Validation Utilities ===

def is_valid_email(email: str) -> bool:
    """
    Simple email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password: str) -> bool:
    """
    Check if password meets minimum strength requirements.
    
    Args:
        password: Password to check
        
    Returns:
        True if strong, False otherwise
    """
    if len(password) < 8:
        return False
    
    # Check for at least one uppercase letter, one lowercase letter, one digit
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit


# === Event Logging Utilities ===

def log_system_event(event_type: str, severity: str, message: str, 
                     user=None, ip_address: str = None, details: Dict = None) -> SystemEventLog:
    """
    Log a system event.
    
    Args:
        event_type: Type of event
        severity: Severity level (info, warning, error, critical)
        message: Event message
        user: User associated with the event
        ip_address: IP address
        details: Additional details
        
    Returns:
        Created SystemEventLog instance
    """
    return SystemEventLog.objects.create(
        event_type=event_type,
        severity=severity,
        message=message,
        details=details or {},
        user=user,
        ip_address=ip_address
    )


# === Health Check Utilities ===

def create_health_check(check_type: str, status: str, value: float, unit: str = "",
                        threshold_critical: float = 0, threshold_warning: float = 0,
                        details: str = "") -> SystemHealthCheck:
    """
    Create a system health check record.
    
    Args:
        check_type: Type of health check
        status: Status (healthy, warning, error, critical)
        value: Numeric value of the metric
        unit: Unit of measurement
        threshold_critical: Threshold for critical status
        threshold_warning: Threshold for warning status
        details: Additional details
        
    Returns:
        Created SystemHealthCheck instance
    """
    return SystemHealthCheck.objects.create(
        check_type=check_type,
        status=status,
        value=value,
        unit=unit,
        threshold_critical=threshold_critical,
        threshold_warning=threshold_warning,
        details=details
    )


# === Maintenance Utilities ===

def schedule_maintenance(title: str, description: str, 
                         scheduled_start: datetime, scheduled_end: datetime,
                         maintenance_type: str = "system_update",
                         affected_components: str = "") -> MaintenanceWindow:
    """
    Schedule a maintenance window.
    
    Args:
        title: Maintenance title
        description: Maintenance description
        scheduled_start: Scheduled start time
        scheduled_end: Scheduled end time
        maintenance_type: Type of maintenance
        affected_components: Comma-separated list of affected components
        
    Returns:
        Created MaintenanceWindow instance
    """
    return MaintenanceWindow.objects.create(
        title=title,
        description=description,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        maintenance_type=maintenance_type,
        affected_components=affected_components,
        status="scheduled"
    )


# === Performance Utilities ===

def log_performance_metric(metric_type: str, value: float, unit: str = "ms",
                           component: str = "", environment: str = "production",
                           tenant=None) -> PerformanceMetric:
    """
    Log a performance metric.
    
    Args:
        metric_type: Type of metric
        value: Metric value
        unit: Unit of measurement
        component: Component being measured
        environment: Environment (development, staging, production)
        tenant: Tenant (optional)
        
    Returns:
        Created PerformanceMetric instance
    """
    return PerformanceMetric.objects.create(
        metric_type=metric_type,
        value=value,
        unit=unit,
        component=component,
        environment=environment,
        tenant=tenant
    )


# === Notification Utilities ===

def create_system_notification(title: str, message: str, 
                               notification_type: str = "info",
                               priority: str = "normal",
                               start_datetime: datetime = None,
                               end_datetime: datetime = None,
                               is_active: bool = True,
                               is_dismissible: bool = True) -> SystemNotification:
    """
    Create a system notification.
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        priority: Notification priority
        start_datetime: When to start showing notification
        end_datetime: When to stop showing notification
        is_active: Whether notification is active
        is_dismissible: Whether notification can be dismissed
        
    Returns:
        Created SystemNotification instance
    """
    if start_datetime is None:
        start_datetime = timezone.now()
        
    if end_datetime is None:
        end_datetime = start_datetime + timedelta(days=7)  # Default 1 week
        
    return SystemNotification.objects.create(
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        is_active=is_active,
        is_dismissible=is_dismissible
    )



def get_queryset_for_user(user, model_class):
    """
    Get a queryset for a model filtered by the user's tenant.
    
    Args:
        user: The user object
        model_class: The model class to query
        
    Returns:
        QuerySet filtered by user's tenant
    """
    queryset = model_class.objects.all()
    
    if hasattr(user, 'tenant_id') and user.tenant_id:
        queryset = queryset.filter(tenant_id=user.tenant_id)
    
    return queryset


def check_cross_tenant_access(user, resource, action='access'):
    """
    Utility function to check if a user is attempting to access a resource from a different tenant.
    
    Args:
        user: The user attempting access
        resource: The resource being accessed (should have a tenant attribute)
        action: The type of action being performed ('access', 'read', 'update', 'delete')
    
    Returns:
        bool: True if access is allowed, False if it's a cross-tenant access attempt
    """
    from audit_logs.models import AuditLog
    from tenants.models import TenantDataIsolationViolation, TenantDataIsolationAudit
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Skip check for superusers
    if user.is_superuser:
        return True
    
    # Check if user has a tenant and resource has a tenant
    if not hasattr(user, 'tenant') or not user.tenant:
        return True  # No tenant context to check
    
    if not hasattr(resource, 'tenant') or not resource.tenant:
        return True  # Resource doesn't have tenant context
    
    # Check if tenants match
    if user.tenant.id == resource.tenant.id:
        return True  # Same tenant, access allowed
    
    # Cross-tenant access detected - log it
    AuditLog.objects.create(
        tenant=user.tenant,  # Log under the user's tenant
        user=user,
        action='authorization',
        resource_type='security_event',
        resource_id=str(resource.pk) if hasattr(resource, 'pk') else 'unknown',
        resource_name=str(resource),
        old_values={},
        new_values={},
        ip_address='',  # Would need to get from request context
        user_agent='',  # Would need to get from request context
        is_successful=False,
        error_message=f'Cross-tenant {action} attempt detected: user tenant {user.tenant.id} tried to {action} resource from tenant {resource.tenant.id}',
        metadata={
            'user_tenant_id': user.tenant.id,
            'resource_tenant_id': resource.tenant.id,
            'access_type': 'cross_tenant_access',
            'action': action,
        },
        severity='critical'
    )
    
    # Also log to the tenant data isolation violations
    audit, created = TenantDataIsolationAudit.objects.get_or_create(
        tenant=user.tenant,
        audit_type='security',
        status='in_progress',
        defaults={
            'auditor': user,
            'notes': 'Automated security audit for cross-tenant access detection'
        }
    )
    
    # Create a violation record
    TenantDataIsolationViolation.objects.create(
        audit=audit,
        model_name=type(resource).__name__,
        record_id=resource.pk if hasattr(resource, 'pk') else 0,
        field_name='tenant',
        expected_tenant=user.tenant,
        actual_tenant=resource.tenant,
        violation_type='cross_tenant_access',
        severity='critical',
        description=f'User {user.email} attempted to {action} {type(resource).__name__} belonging to tenant {resource.tenant.id} from tenant {user.tenant.id}',
        resolution_status='open'
    )
    
    logger.warning(
        f"Cross-tenant access detected: user {user.email} (tenant {user.tenant.id}) "
        f"attempted to {action} {type(resource).__name__} (tenant {resource.tenant.id})"
    )
    
    return False  # Access denied
