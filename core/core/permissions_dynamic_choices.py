from django.core.exceptions import PermissionDenied
from .permissions import PermissionRequiredMixin
from .models import User


class DynamicChoicePermissionMixin(PermissionRequiredMixin):
    """
    Mixin for dynamic choice model permissions.
    Provides role-based access control for managing different dynamic choice models.
    """
    permission_model = None  # To be set in subclasses (e.g., 'system_config_type')
    
    # Define permission actions
    permission_actions = {
        'list': 'view',
        'create': 'add',
        'update': 'change',
        'delete': 'delete',
    }
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required")
        
        # Determine the action based on the request method
        action = self.get_permission_action()
        
        # Check if user has the required permission
        if not self.has_permission(request.user, action):
            raise PermissionDenied(f"You do not have permission to {action} {self.permission_model} records.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_permission_action(self):
        """
        Determine the permission action based on the request method.
        """
        if hasattr(self, 'permission_action'):
            return self.permission_action
        
        method = self.request.method.lower()
        if method == 'get':
            # Check if this is a list view (no pk in URL) or detail view (has pk in URL)
            if self.__class__.__name__.endswith('ListView'):
                return 'view'
            else:
                return 'view'
        elif method == 'post':
            # Check if this is a create view (no pk in URL) or update view (has pk in URL)
            if 'pk' in self.kwargs or 'id' in self.kwargs:
                return 'change'
            else:
                return 'add'
        elif method == 'put':
            return 'change'
        elif method == 'delete':
            return 'delete'
        else:
            return 'view'
    
    def has_permission(self, user, action):
        """
        Check if the user has permission to perform the specified action on the model.
        """
        if user.is_superuser:
            return True
        
        # Build permission string in the format: app_label.action_modelname
        # e.g., core.add_systemconfigtype, core.change_systemconfigtype
        permission = f"core.{action}_{self.permission_model}"
        
        # Check if user has the specific permission
        if user.has_perm(permission):
            return True
        
        # Check if user has role-based permissions
        if hasattr(user, 'role') and user.role:
            # Check role-specific permissions
            role_permission = f"role.{user.role.name}.{action}_{self.permission_model}"
            if user.has_perm(role_permission):
                return True
        
        # For tenant admins, allow all dynamic choice management
        if hasattr(user, 'role') and user.role and user.role.name.lower() in ['admin', 'manager', 'superuser']:
            return True
        
        return False


class SystemConfigTypePermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'systemconfigtype'


class SystemConfigCategoryPermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'systemconfigcategory'


class SystemEventTypePermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'systemeventtype'


class SystemEventSeverityPermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'systemeventseverity'


class HealthCheckTypePermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'healthchecktype'


class HealthCheckStatusPermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'healthcheckstatus'


class MaintenanceStatusPermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'maintenancestatus'


class MaintenanceTypePermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'maintenancetype'


class PerformanceMetricTypePermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'performancemetrictype'


class PerformanceEnvironmentPermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'performanceenvironment'


class NotificationTypePermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'notificationtype'


class NotificationPriorityPermissionMixin(DynamicChoicePermissionMixin):
    permission_model = 'notificationpriority'


def check_dynamic_choice_permission(user, action, model_name):
    """
    Utility function to check if a user has permission to perform an action on a dynamic choice model.
    
    Args:
        user: The user to check permissions for
        action: The action to perform (view, add, change, delete)
        model_name: The name of the model (e.g., 'systemconfigtype')
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if user.is_superuser:
        return True
    
    # Build permission string
    permission = f"core.{action}_{model_name}"
    
    # Check direct permission
    if user.has_perm(permission):
        return True
    
    # Check role-based permissions
    if hasattr(user, 'role') and user.role:
        role_permission = f"role.{user.role.name}.{action}_{model_name}"
        if user.has_perm(role_permission):
            return True
    
    # For tenant admins, allow all dynamic choice management
    if hasattr(user, 'role') and user.role and user.role.name.lower() in ['admin', 'manager', 'superuser']:
        return True
    
    return False


def require_dynamic_choice_permission(action, model_name):
    """
    Decorator to require specific permission for dynamic choice operations.
    
    Usage:
        @require_dynamic_choice_permission('change', 'systemconfigtype')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if not check_dynamic_choice_permission(request.user, action, model_name):
                raise PermissionDenied(f"You do not have permission to {action} {model_name} records.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
