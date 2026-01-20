from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .models import AccessControl
from .controller import UnifiedAccessController

def check_user_access(user, resource_key, action='access'):
    """
    Wrapper function to check if a user has access to a specific resource
    """
    return UnifiedAccessController.has_access(user, resource_key, action)


def get_user_available_apps(user):
    """
    Get list of applications available to a specific user
    """
    return UnifiedAccessController.get_available_resources(user)


def create_access_control_entry(name, key, access_type, scope_type, is_enabled=True, **kwargs):
    """
    Helper function to create access control entries with common parameters
    
    kwargs can include:
    - user: User instance (for scope_type='user')
    - role: Role instance (for scope_type='role')  
    - tenant: Tenant instance (for scope_type='tenant')
    - description: Description text
    - rollout_percentage: For feature flags
    - config_data: JSON configuration
    """
    entry = AccessControl.objects.create(
        name=name,
        key=key,
        access_type=access_type,
        scope_type=scope_type,
        is_enabled=is_enabled,
        **{k: v for k, v in kwargs.items() if k in ['user', 'role', 'tenant', 'description', 'rollout_percentage', 'config_data']}
    )
    return entry


def bulk_create_access_controls(entries_list):
    """
    Bulk create multiple access control entries
    
    Each entry in entries_list should be a dict with required parameters
    """
    created_entries = []
    for entry_data in entries_list:
        entry = create_access_control_entry(**entry_data)
        created_entries.append(entry)


# NEW: Decorator for function-based views
def access_required(resource_key, action='access'):
    """
    Decorator to enforce access control for function-based views
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not UnifiedAccessController.has_access(request.user, resource_key, action):
                return HttpResponseForbidden(f"Access denied to {resource_key}")
            return view_func(request, *args, **kwargs)
        
        # Add attributes for middleware to detect
        _wrapped_view._access_required = True
        _wrapped_view._access_resource = resource_key
        _wrapped_view._access_action = action
        return _wrapped_view
    return decorator


def get_user_permissions_summary(user):
    """
    Get all permissions for a user for debugging purposes
    """
    return UnifiedAccessController.get_user_permissions_summary(user)


def has_access_with_reason(user, resource_key, action='access'):
    """
    Check access and return detailed reason for debugging
    """
    return UnifiedAccessController.has_access_with_reason(user, resource_key, action)