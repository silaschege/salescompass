import threading
from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()

def get_current_user():
    """Get the current user from thread locals."""
    return getattr(_thread_locals, 'user', None)

class ThreadLocalUserMiddleware(MiddlewareMixin):
    """
    Middleware to store the request user in thread local storage.
    This allows models to access the current user during save() without
    passing the user object explicitly.
    """
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)

    def process_response(self, request, response):
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        return response


class DataVisibilityMiddleware(MiddlewareMixin):
    """
    Middleware to inject visibility context into the user object.
    Sets request.user.visibility_context based on the user's role data_visibility_rules.
    """
    def process_request(self, request):
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            # Initialize visibility_context
            visibility_context = {}
            
            if user.is_superuser:
                # Superusers have 'all' visibility for everything
                visibility_context = {'default': 'all'}
            elif user.role and hasattr(user.role, 'data_visibility_rules'):
                # Use the role's data_visibility_rules
                visibility_context = user.role.data_visibility_rules.copy()
            else:
                # Default to 'own_only' for all models
                visibility_context = {'default': 'own_only'}
            
            # Attach to user object
            user.visibility_context = visibility_context
        
        return None