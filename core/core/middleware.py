import threading
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from django.template.response import TemplateResponse
from tenants.models import Tenant
import logging



_thread_locals = threading.local()

logger = logging.getLogger(__name__)

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


class BusinessMetricsAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce access controls for business metrics
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define protected URL patterns for business metrics
        self.protected_patterns = [
            'clv_dashboard',
            'cac_analytics',
            'sales_velocity_dashboard',
            'export_clv_metrics',
            'export_cac_metrics',
            'export_sales_velocity_metrics',
            'export_roi_metrics',
            'export_conversion_funnel_metrics',
            'export_all_metrics',
            'clv_metrics_api',
            'cac_metrics_api',
            'sales_velocity_metrics_api',
            'roi_metrics_api',
            'conversion_funnel_metrics_api',
            'metrics_trend_api',
            'business_metrics_api',
        ]

    def __call__(self, request):
        # Process request before view
        response = self.process_request(request)
        
        if response:
            return response
        
        # Get response from view
        response = self.get_response(request)
        
        # Process response after view
        response = self.process_response(request, response)
        
        return response

    def process_request(self, request):
        return None

    def process_response(self, request, response):
        return response


class ForbiddenAccessMiddleware(MiddlewareMixin):
    """
    Middleware to handle 403 Forbidden responses consistently across the system.
    If user is authenticated, show a custom 403 page.
    If user is not authenticated, redirect to login page.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if response is 403 Forbidden
        if response.status_code == 403:
            # Check if user is authenticated
            if request.user.is_authenticated:
                # User is logged in but doesn't have permission
                # Render custom 403 template
                context = {
                    'message': 'You do not have permission to access this page.',
                    'contact_admin': True,
                }
                response = TemplateResponse(
                    request, 
                    'core/403.html', 
                    context, 
                    status=403
                )
                response.render()
                return response
            else:
                # User is not logged in, redirect to login page
                # Preserve the next parameter so they can be redirected back after login
                from django.urls import reverse
                login_url = reverse('accounts:login')
                from django.shortcuts import redirect
                redirect_url = f"{login_url}?next={request.path}"
                return redirect(redirect_url)
                
        return response




