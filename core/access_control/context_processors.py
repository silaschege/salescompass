"""
Context processors for access control app
"""

def access_control(request):
    """
    Add access control utilities to template context
    """
    if request.user.is_authenticated:
        from .controller import UnifiedAccessController
        from .utils import get_user_available_apps, check_user_access
        
        return {
            'user_available_apps': get_user_available_apps(request.user),
            'has_access': lambda resource_key, action='access': check_user_access(
                request.user, resource_key, action
            ),
            # NEW: Add utility functions for templates
            'can_access': lambda resource_key, action='access': UnifiedAccessController.has_access(
                request.user, resource_key, action
            ),
            'user_permissions_summary': lambda: {
                'permissions': [perm['key'] for perm in get_user_available_apps(request.user)]
            },
            'all_user_permissions': lambda: get_user_available_apps(request.user)
        }
    
    return {}