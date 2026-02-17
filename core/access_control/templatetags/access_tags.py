from django import template  
from access_control.controller import UnifiedAccessController

register = template.Library()

@register.filter
def user_can_access(user, resource_key):
    """Check if user has access to a resource in templates"""
    return UnifiedAccessController.has_access(user, resource_key, 'access')

@register.filter
def user_can_perform(user, resource_key):
    """Alias for user_can_access"""
    return UnifiedAccessController.has_access(user, resource_key, 'access')

@register.filter
def has_permission(user, resource_key):
    """Check if user has any permission for a resource (default action)"""
    return UnifiedAccessController.has_access(user, resource_key, 'access')

@register.simple_tag
def get_user_permissions(user):
    """Get all permissions for a user"""
    from core.access_control.utils import get_user_permissions_summary
    return get_user_permissions_summary(user)

@register.simple_tag
def get_available_resources(user):
    """Get available resources for a user"""
    from core.access_control.utils import get_user_available_apps
    return get_user_available_apps(user)