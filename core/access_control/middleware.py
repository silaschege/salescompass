from django.http import HttpResponseForbidden
from .controller import UnifiedAccessController


class AccessControlMiddleware:
    """
    Middleware to enforce access control on requests
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Check if the view has access control requirements
        if hasattr(view_func, 'required_access'):
            resource_key = view_func.required_access
            action = getattr(view_func, 'access_action', 'access')
            
            if not request.user.is_authenticated:
                return None  # Let login_required decorator handle this
            
            if not UnifiedAccessController.has_access(request.user, resource_key, action):
                return HttpResponseForbidden("Access denied")
        
        # Also check for class-based views
        if hasattr(view_func, '__class__'):
            view_class = view_func.__class__
            if hasattr(view_class, 'required_access'):
                resource_key = view_class.required_access
                action = getattr(view_class, 'access_action', 'access')
                
                if not request.user.is_authenticated:
                    return None
                
                if not UnifiedAccessController.has_access(request.user, resource_key, action):
                    return HttpResponseForbidden("Access denied")
        
        # NEW: Enhanced checking for function-based views with decorators
        # Check for @access_required decorator equivalent
        if hasattr(view_func, '_access_required'):
            resource_key = getattr(view_func, '_access_resource', None)
            action = getattr(view_func, '_access_action', 'access')
            
            if resource_key and not request.user.is_authenticated:
                return None
                
            if resource_key and not UnifiedAccessController.has_access(request.user, resource_key, action):
                return HttpResponseForbidden("Access denied")
        
        return None