from django import template
from tenants.middleware import FeatureEnforcementMiddleware

register = template.Library()

@register.simple_tag(takes_context=True)
def has_module_access(context, module_name):
    """
    Template tag to check if the current user has access to a specific module.
    Usage: {% has_module_access 'leads' as leads_access %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    # Superusers have access to everything
    if request.user.is_superuser:
        return True
        
    return FeatureEnforcementMiddleware.has_module_access(request.user, module_name)

@register.simple_tag(takes_context=True)
def has_feature_access(context, feature_key):
    """
    Template tag to check if the current user has access to a specific feature.
    Usage: {% has_feature_access 'lead_scoring' as scoring_access %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
        
    if request.user.is_superuser:
        return True
        
    return FeatureEnforcementMiddleware.has_feature_access(request.user, feature_key)
