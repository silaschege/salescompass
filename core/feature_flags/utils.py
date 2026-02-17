"""
Utility functions for feature flag checking and analytics
"""
from .models import FeatureFlag, FeatureTarget


def is_feature_enabled(key, user):
    """
    Check if a feature is enabled for a given user
    
    Args:
        key: Feature flag key
        user: User object
    
    Returns:
        bool: True if feature is enabled for user
    """
    try:
        flag = FeatureFlag.objects.get(key=key)
        return flag.is_enabled_for_user(user)
    except FeatureFlag.DoesNotExist:
        return False


def get_feature_flags_for_user(user):
    """
    Get all enabled feature flags for a user
    
    Args:
        user: User object
    
    Returns:
        dict: Dictionary of enabled flags {key: flag_object}
    """
    enabled_flags = {}
    for flag in FeatureFlag.objects.filter(is_active=True):
        if flag.is_enabled_for_user(user):
            enabled_flags[flag.key] = flag
    return enabled_flags


def calculate_adoption_rate(flag):
    """
    Calculate adoption rate for a feature flag
    This is a simplified version - in production, you'd track actual usage
    
    Args:
        flag: FeatureFlag object
    
    Returns:
        dict: Adoption metrics
    """
    return {
        'rollout_percentage': flag.rollout_percentage,
        'is_active': flag.is_active,
        'targeting_rules_count': flag.targets.filter(is_active=True).count(),
        'estimated_reach': flag.rollout_percentage if flag.is_active else 0
    }


def get_rollout_breakdown(flag):
    """
    Get detailed breakdown of rollout configuration
    
    Args:
        flag: FeatureFlag object
    
    Returns:
        dict: Rollout breakdown
    """
    targets = flag.targets.filter(is_active=True)
    
    breakdown = {
        'percentage': flag.rollout_percentage,
        'targeting_rules': {
            'user_ids': list(targets.filter(target_type='user_id').values_list('target_value', flat=True)),
            'tenant_ids': list(targets.filter(target_type='tenant_id').values_list('target_value', flat=True)),
            'roles': list(targets.filter(target_type='role').values_list('target_value', flat=True)),
            'plans': list(targets.filter(target_type='plan').values_list('target_value', flat=True)),
            'cohorts': list(targets.filter(target_type='cohort').values_list('target_value', flat=True)),
        }
    }
    
    return breakdown


def get_feature_analytics(flag):
    """
    Get analytics for a feature flag
    
    Args:
        flag: FeatureFlag object
    
    Returns:
        dict: Analytics data
    """
    # In a real system, you'd track actual usage events
    # For now, return basic metrics
    adoption = calculate_adoption_rate(flag)
    breakdown = get_rollout_breakdown(flag)
    
    return {
        'flag': flag,
        'adoption': adoption,
        'rollout': breakdown,
        'status': 'Active' if flag.is_active else 'Disabled',
        'created_at': flag.created_at,
        'updated_at': flag.updated_at,
    }
