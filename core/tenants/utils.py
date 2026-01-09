from .models import TenantUsageMetric
from django.utils import timezone
from django.db.models import Sum
import datetime

def track_usage(tenant, metric_type, value=1, unit='', period_start=None, period_end=None):
    """
    Track usage for a tenant
    """
    if period_start is None:
        period_start = timezone.now() - timezone.timedelta(days=1)
    if period_end is None:
        period_end = timezone.now()
     
    metric = TenantUsageMetric.objects.create(
        tenant=tenant,
        metric_type=metric_type,
        value=value,
        unit=unit,
        period_start=period_start,
        period_end=period_end
    )
    return metric

def get_current_usage(tenant, metric_type, period_start=None, period_end=None):
    """
    Get current usage for a tenant and metric type
    """
    if period_start is None:
        period_start = timezone.now() - timezone.timedelta(days=1)
    if period_end is None:
        period_end = timezone.now()
    
    metrics = TenantUsageMetric.objects.filter(
        tenant=tenant,
        metric_type=metric_type,
        timestamp__gte=period_start,
        timestamp__lte=period_end
    )
    
    return sum([m.value for m in metrics])

def get_usage_trend(tenant, metric_type, days=30):
    """
    Get usage trend for the specified number of days
    """
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=days)
    
    # Group by date and sum the values
    daily_usage = TenantUsageMetric.objects.filter(
        tenant=tenant,
        metric_type=metric_type,
        timestamp__date__gte=start_date.date(),
        timestamp__date__lte=end_date.date()
    ).values('timestamp__date').annotate(total=Sum('value')).order_by('timestamp__date')
    
    dates = []
    values = []
    
    for entry in daily_usage:
        dates.append(entry['timestamp__date'].strftime('%Y-%m-%d'))
        values.append(float(entry['total']) if entry['total'] else 0)
    
    return {'dates': dates, 'values': values}

def check_usage_limits(tenant):
    """
    Check if tenant is approaching or exceeding usage limits
    """
    alerts = []
    
    # Check user limit
    current_users = get_current_usage(tenant, 'users_total')
    if tenant.user_limit > 0 and current_users >= tenant.user_limit * 0.8:
        status = 'warning' if current_users < tenant.user_limit else 'danger'
        alerts.append({
            'type': status,
            'message': f'User limit approaching ({current_users}/{tenant.user_limit})',
            'metric': 'users_total'
        })
    
    # Check storage limit
    current_storage = get_current_usage(tenant, 'storage_used_mb')
    if tenant.storage_limit_mb > 0 and current_storage >= tenant.storage_limit_mb * 0.8:
        status = 'warning' if current_storage < tenant.storage_limit_mb else 'danger'
        alerts.append({
            'type': status,
            'message': f'Storage limit approaching ({current_storage}/{tenant.storage_limit_mb} MB)',
            'metric': 'storage_used_mb'
        })
    
    # Check API call limit
    current_api_calls = get_current_usage(tenant, 'api_calls')
    if tenant.api_call_limit > 0 and current_api_calls >= tenant.api_call_limit * 0.8:
        status = 'warning' if current_api_calls < tenant.api_call_limit else 'danger'
        alerts.append({
            'type': status,
            'message': f'API call limit approaching ({current_api_calls}/{tenant.api_call_limit})',
            'metric': 'api_calls'
        })
    
    return alerts

def generate_usage_report(tenant, metric_type, start_date, end_date, include_trend=False, include_comparison=False):
    """
    Generate a usage report for a specific metric type and time period
    """
    metrics = TenantUsageMetric.objects.filter(
        tenant=tenant,
        metric_type=metric_type,
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).order_by('timestamp')
    
    # Prepare data for the chart
    chart_data = []
    timestamps = []
    values = []
    
    for metric in metrics:
        timestamps.append(metric.timestamp.strftime('%Y-%m-%d %H:%M'))
        values.append(float(metric.value))
    
    # Calculate statistics
    total_usage = sum([m.value for m in metrics])
    avg_usage = total_usage / len(metrics) if metrics else 0
    max_usage = max([m.value for m in metrics]) if metrics else 0
    min_usage = min([m.value for m in metrics]) if metrics else 0
    
    report_data = {
        'metrics': metrics,
        'chart_data': {
            'timestamps': timestamps,
            'values': values,
            'metric_type': metric_type,
        },
        'statistics': {
            'total_usage': total_usage,
            'avg_usage': avg_usage,
            'max_usage': max_usage,
            'min_usage': min_usage,
            'count': len(metrics),
        }
    }
    
    if include_trend:
        report_data['trend_data'] = get_usage_trend(tenant, metric_type)
    
    if include_comparison:
        # Compare with previous period
        period_duration = end_date - start_date
        prev_start = start_date - period_duration
        prev_end = end_date - period_duration
        
        prev_metrics = TenantUsageMetric.objects.filter(
            tenant=tenant,
            metric_type=metric_type,
            timestamp__gte=prev_start,
            timestamp__lte=prev_end
        )
        
        prev_total = sum([m.value for m in prev_metrics])
        change = ((total_usage - prev_total) / prev_total * 100) if prev_total > 0 else 0
        
        report_data['comparison'] = {
            'previous_total': prev_total,
            'change_percentage': change
        }
    
    return report_data



def check_feature_access(tenant, feature_key):
    """Check if a tenant has access to a specific feature"""
    try:
        entitlement = TenantFeatureEntitlement.objects.get(
            tenant=tenant,
            feature_key=feature_key
        )
        return entitlement.is_access_valid()
    except TenantFeatureEntitlement.DoesNotExist:
        # By default, features are disabled for tenants without explicit entitlement
        return False

def get_accessible_features(tenant):
    """Get all features accessible to a tenant"""
    entitlements = TenantFeatureEntitlement.objects.filter(
        tenant=tenant,
        is_enabled=True
    )
    
    accessible_features = []
    for entitlement in entitlements:
        if entitlement.is_access_valid():
            accessible_features.append({
                'key': entitlement.feature_key,
                'name': entitlement.feature_name,
                'type': entitlement.entitlement_type,
                'trial_active': entitlement.is_trial_active() if entitlement.entitlement_type == 'trial' else None
            })
    
    return accessible_features

def enforce_feature_access(tenant, feature_key):
    """Decorator to enforce feature access - raises exception if not allowed"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Check if tenant is available on request user
            current_tenant = tenant
            if hasattr(request.user, 'tenant'):
                 current_tenant = request.user.tenant
                 
            if not check_feature_access(current_tenant, feature_key):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied(f"Feature '{feature_key}' is not available for your subscription plan.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def perform_data_isolation_audit(audit):
    """
    Perform a data isolation audit for the given audit record
    """
    from django.apps import apps
    from django.db import models
    from .models import TenantAwareModel, TenantDataIsolationViolation
    
    # This is a simplified version - in a real implementation, you would check
    # for cross-tenant data access in all tenant-aware models
    violations_found = 0
    total_records = 0
    
    # Get all models that inherit from TenantAwareModel
    for model in apps.get_models():
        # Check if the model has a tenant field and belongs to the tenants app or related apps
        if (hasattr(model, '_meta') and 
            any(field.name == 'tenant' for field in model._meta.fields) and
            not model._meta.app_label == 'contenttypes' and
            not model._meta.app_label == 'auth' and
            not model._meta.app_label == 'admin' and
            not model._meta.app_label == 'sessions'):
            
            try:
                # Check for records that don't belong to the correct tenant
                # We need to exclude records that have the correct tenant
                records = model.objects.exclude(tenant=audit.tenant)
                
                # For efficiency, we'll only look at records that have a tenant field
                records_with_tenant = records.filter(tenant__isnull=False)
                
                for record in records_with_tenant:
                    # Check if this record actually belongs to the audit's tenant
                    if hasattr(record, 'tenant') and record.tenant != audit.tenant:
                        # Create a violation record
                        TenantDataIsolationViolation.objects.create(
                            audit=audit,
                            model_name=model.__name__,
                            record_id=record.pk,
                            field_name='tenant',
                            expected_tenant=audit.tenant,
                            actual_tenant=record.tenant if hasattr(record, 'tenant') else None,
                            violation_type='cross_tenant_access',
                            severity='high',
                            description=f'Record with ID {record.pk} in model {model.__name__} belongs to tenant {record.tenant.name if record.tenant else "None"} instead of expected tenant {audit.tenant.name}'
                        )
                        violations_found += 1
                    total_records += 1
            except Exception as e:
                # Log the error but continue with other models
                print(f"Error checking model {model.__name__}: {str(e)}")
    
    # Update the audit record with results
    audit.total_records_checked = total_records
    audit.violations_found = violations_found
    audit.status = 'failed' if violations_found > 0 else 'passed'
    audit.save()
    
    return violations_found, total_records



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


def check_data_residency_compliance(tenant, data_region):
    """
    Check if storing data in the specified region complies with the tenant's data residency settings
    
    Args:
        tenant: The tenant object
        data_region: The region where data is intended to be stored
    
    Returns:
        bool: True if compliant, False otherwise
    """
    try:
        from .models import DataResidencySettings
        data_residency_settings = DataResidencySettings.objects.get(tenant=tenant)
        
        if not data_residency_settings.is_active:
            return True  # Compliance checks disabled
        
        return data_residency_settings.is_compliant_region(data_region)
    except DataResidencySettings.DoesNotExist:
        # If no settings exist, assume global compliance (no restrictions)
        return True


def enforce_data_residency_policy(tenant, data_region, data_type="general"):
    """
    Enforce data residency policy by checking compliance and raising an exception if violated
    
    Args:
        tenant: The tenant object
        data_region: The region where data is intended to be stored
        data_type: Type of data being stored (for logging purposes)
    
    Raises:
        PermissionError: If data residency policy is violated
    """
    is_compliant = check_data_residency_compliance(tenant, data_region)
    
    if not is_compliant:
        raise PermissionError(
            f"Data residency policy violation: "
            f"Tenant {tenant.name} does not allow data of type '{data_type}' to be stored in region '{data_region}'."
        )
    
    return True


def get_data_storage_location(tenant):
    """
    Get the appropriate data storage location based on tenant's data residency settings
    
    Args:
        tenant: The tenant object
    
    Returns:
        str: The region where data should be stored
    """
    try:
        from .models import DataResidencySettings
        data_residency_settings = DataResidencySettings.objects.get(tenant=tenant)
        
        if not data_residency_settings.is_active:
            return 'GLOBAL'  # Default to global if compliance is disabled
        
        return data_residency_settings.primary_region
    except DataResidencySettings.DoesNotExist:
        # If no settings exist, return global as default
        return 'GLOBAL'


def get_backup_storage_locations(tenant):
    """
    Get the appropriate backup storage locations based on tenant's data residency settings
    
    Args:
        tenant: The tenant object
    
    Returns:
        list: List of regions where backups should be stored
    """
    try:
        from .models import DataResidencySettings
        data_residency_settings = DataResidencySettings.objects.get(tenant=tenant)
        
        if not data_residency_settings.is_active:
            return [data_residency_settings.primary_region]  # Use primary region if compliance is disabled
        
        if data_residency_settings.backup_regions:
            return data_residency_settings.backup_regions
        else:
            # If no backup regions specified, use primary region
            return [data_residency_settings.primary_region]
    except DataResidencySettings.DoesNotExist:
        # If no settings exist, return global as default
        return ['GLOBAL']


 



def check_feature_access(tenant, feature_key):
    """Check if a tenant has access to a specific feature based on plan or explicit entitlement"""
    try:
        from .models import TenantFeatureEntitlement
        # Check explicit entitlement first
        entitlement = TenantFeatureEntitlement.objects.get(
            tenant=tenant,
            feature_key=feature_key
        )
        return entitlement.is_enabled
    except TenantFeatureEntitlement.DoesNotExist:
        # Check if feature is available through plan
        if tenant.plan:
            from billing.models import PlanFeatureAccess
            try:
                plan_feature = PlanFeatureAccess.objects.get(
                    plan=tenant.plan,
                    feature_key=feature_key
                )
                return plan_feature.is_available
            except PlanFeatureAccess.DoesNotExist:
                pass
        return False

def get_accessible_features(tenant):
    """Get all features accessible to a tenant based on plan and explicit entitlements"""
    from .models import TenantFeatureEntitlement
    from billing.models import PlanFeatureAccess
    
    # Get explicitly set features
    explicit_features = TenantFeatureEntitlement.objects.filter(
        tenant=tenant,
        is_enabled=True
    )
    
    # Get features from plan
    plan_features = []
    if tenant.plan:
        plan_features = PlanFeatureAccess.objects.filter(
            plan=tenant.plan,
            is_available=True
        )
    
    # Combine both sources
    accessible_features = []
    for entitlement in explicit_features:
        accessible_features.append({
            'key': entitlement.feature_key,
            'name': entitlement.feature_name,
            'type': entitlement.entitlement_type,
            'source': 'explicit'
        })
    
    for plan_feature in plan_features:
        # Only add if not already explicitly set
        if not any(f['key'] == plan_feature.feature_key for f in accessible_features):
            accessible_features.append({
                'key': plan_feature.feature_key,
                'name': plan_feature.feature_name,
                'type': 'plan_based',
                'source': 'plan'
            })
    
    return accessible_features

