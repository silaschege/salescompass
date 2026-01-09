from django import template
from ..controller import UnifiedAccessController

register = template.Library()

@register.simple_tag
def can_access(user, resource_key, action='access'):
    """
    Template tag to check if user can access a resource
    Usage: {% can_access user 'dashboard.view' 'access' as has_access %}
    """
    return UnifiedAccessController.has_access(user, resource_key, action)

@register.inclusion_tag('access_control/available_apps.html')
def render_available_apps(user):
    """
    Render available apps for user
    """
    available_resources = UnifiedAccessController.get_available_resources(user)
    return {'available_resources': available_resources}
