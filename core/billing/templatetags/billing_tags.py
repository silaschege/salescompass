from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def filter_by_status(queryset, status):
    """Filter a queryset of subscriptions by status."""
    if not queryset:
        return []
    return [sub for sub in queryset if sub.status == status]

@register.filter
def filter_days_until(queryset, days):
    """Filter subscriptions renewing within X days."""
    if not queryset:
        return []
    
    threshold = timezone.now() + timedelta(days=int(days))
    return [
        sub for sub in queryset 
        if sub.current_period_end and sub.current_period_end <= threshold
    ]

@register.filter
def filter_days_until_range(queryset, range_str):
    """
    Filter subscriptions renewing within a range of days.
    Usage: queryset|filter_days_until_range:"7:14"
    """
    if not queryset:
        return []
    
    try:
        min_days, max_days = map(int, range_str.split(':'))
    except ValueError:
        return []
        
    now = timezone.now()
    min_date = now + timedelta(days=min_days)
    max_date = now + timedelta(days=max_days)
    
    return [
        sub for sub in queryset 
        if sub.current_period_end and min_date <= sub.current_period_end <= max_date
    ]

@register.filter
def map_attr(queryset, attr_path):
    """
    Map a list of objects to a list of attribute values.
    Supports nested attributes like 'plan.price_monthly'.
    """
    if not queryset:
        return []
    
    result = []
    for obj in queryset:
        val = obj
        for attr in attr_path.split('.'):
            if hasattr(val, attr):
                val = getattr(val, attr)
            elif isinstance(val, dict) and attr in val:
                val = val[attr]
            else:
                val = None
                break
        if val is not None:
            result.append(val)
    return result

@register.filter
def sum_values(value_list):
    """Sum a list of values."""
    if not value_list:
        return 0
    return sum(float(v) for v in value_list if v is not None)

# Register 'sum' as an alias for 'sum_values' to match the template usage
register.filter('sum', sum_values)
