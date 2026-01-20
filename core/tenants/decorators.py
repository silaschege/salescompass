# File: /home/silaskimani/Documents/replit/git/salescompass/core/tenants/decorators.py
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from .models import TenantFeatureEntitlement
from .views import FeatureEnforcementMiddleware
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from core.utils import check_cross_tenant_access
from core.access_control.controller import UnifiedAccessController
from core.access_control.utils import access_required as unified_access_required
 
def feature_required(feature_key, redirect_url=None, message=None):
    """
    Updated decorator to enforce feature access using unified access control
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Use unified access controller for consistency
            if not UnifiedAccessController.has_access(request.user, feature_key, 'access'):
                error_msg = message or f"You don't have access to the '{feature_key}' feature."
                
                if redirect_url:
                    messages.error(request, error_msg)
                    return redirect(redirect_url)
                else:
                    return HttpResponseForbidden(error_msg)
            
            # Check if it's a trial feature and if the trial has expired
            try:
                feature_entitlement = TenantFeatureEntitlement.objects.get(
                    tenant=request.user.tenant,
                    feature_key=feature_key
                )
                
                if (feature_entitlement.entitlement_type == 'trial' and 
                    feature_entitlement.trial_end_date and 
                    feature_entitlement.trial_end_date < request.user.tenant.now()):
                    error_msg = f"The trial for '{feature_key}' has expired."
                    
                    if redirect_url:
                        messages.error(request, error_msg)
                        return redirect(redirect_url)
                    else:
                        return HttpResponseForbidden(error_msg)
            except TenantFeatureEntitlement.DoesNotExist:
                pass
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def cross_tenant_access_check(resource_param_name='obj', action='access'):
    """
    Decorator to check for cross-tenant access attempts.
    
    Args:
        resource_param_name: Name of the parameter that contains the resource to check
        action: The type of action being performed ('access', 'read', 'update', 'delete')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Get the resource from the view's context or parameters
            resource = None
            
            # Try to get resource from kwargs first
            if resource_param_name in kwargs:
                resource = kwargs[resource_param_name]
            else:
                # If not in kwargs, call the view function first to get the resource
                # This is more complex and might require different approach
                pass
            
            # Check for cross-tenant access if resource is available
            if resource:
                access_allowed = check_cross_tenant_access(request.user, resource, action)
                if not access_allowed:
                    raise PermissionDenied("You do not have permission to access this resource.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# DEPRECATED: Keep for backward compatibility but encourage use of unified system
def feature_required_legacy(feature_key, redirect_url=None, message=None):
    """
    LEGACY: Decorator to enforce feature access for function-based views
    Use the unified access control system instead
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user has access to the feature
            if not FeatureEnforcementMiddleware.has_feature_access(request.user, feature_key):
                error_msg = message or f"You don't have access to the '{feature_key}' feature."
                
                if redirect_url:
                    messages.error(request, error_msg)
                    return redirect(redirect_url)
                else:
                    return HttpResponseForbidden(error_msg)
            
            # Check if it's a trial feature and if the trial has expired
            try:
                feature_entitlement = TenantFeatureEntitlement.objects.get(
                    tenant=request.user.tenant,
                    feature_key=feature_key
                )
                
                if (feature_entitlement.entitlement_type == 'trial' and 
                    feature_entitlement.trial_end_date and 
                    feature_entitlement.trial_end_date < request.user.tenant.now()):
                    error_msg = f"The trial for '{feature_key}' has expired."
                    
                    if redirect_url:
                        messages.error(request, error_msg)
                        return redirect(redirect_url)
                    else:
                        return HttpResponseForbidden(error_msg)
            except TenantFeatureEntitlement.DoesNotExist:
                pass
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator