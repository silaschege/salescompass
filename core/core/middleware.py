import threading
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
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
        """
        Process the request and check permissions
        """
        # Get the current URL name
        try:
            resolver_match = resolve(request.path_info)
            url_name = resolver_match.url_name
            app_name = resolver_match.app_name
        except:
            # If we can't resolve the URL, continue with the request
            return None

        # Check if this is a protected business metrics URL
        full_url_name = f"{app_name}:{url_name}" if app_name else url_name
        
        if url_name in self.protected_patterns or full_url_name in self.protected_patterns:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.error(request, "You need to be logged in to access business metrics.")
                return redirect('accounts:login')
            
            # Check if user has permission to access business metrics
            if not request.user.has_perm('reports.read') and not request.user.has_perm('core.read'):
                logger.warning(f"User {request.user.email} tried to access business metrics without permission: {full_url_name}")
                messages.error(request, "You don't have permission to access business metrics.")
                return HttpResponseForbidden("Access denied")
            
            # Additional tenant-based access control
            if hasattr(request.user, 'tenant_id') and request.user.tenant_id:
                # Verify that the user belongs to a valid tenant
                try:
                    tenant = Tenant.objects.get(id=request.user.tenant_id)
                    if not tenant.is_active:
                        logger.warning(f"User {request.user.email} tried to access metrics for inactive tenant {request.user.tenant_id}")
                        messages.error(request, "Your tenant account is inactive.")
                        return HttpResponseForbidden("Tenant inactive")
                except Tenant.DoesNotExist:
                    logger.warning(f"User {request.user.email} has invalid tenant_id: {request.user.tenant_id}")
                    messages.error(request, "Invalid tenant account.")
                    return HttpResponseForbidden("Invalid tenant")
        
        return None
    
    def process_response(self, request, response):
        """
        Process the response after the view has been executed
        """
        # Add security headers for sensitive metrics data
        if any(pattern in request.path for pattern in ['/api/metrics/', '/reports/', '/dashboard/']):
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
        
        return response
