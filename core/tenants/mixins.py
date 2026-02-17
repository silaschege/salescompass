# File: /home/silaskimani/Documents/replit/git/salescompass/core/tenants/mixins.py
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from .models import TenantFeatureEntitlement
from .views import FeatureEnforcementMiddleware
from core.utils import check_cross_tenant_access
from django.core.exceptions import ImproperlyConfigured
from core.access_control.controller import UnifiedAccessController
 
class ModuleRequiredMixin:
    """
    Updated mixin to enforce module access using unified access control
    """
    module_required = None
    redirect_url = None
    message = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.module_required:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define 'module_required' attribute."
            )
        
        # Use unified access controller for consistency
        if not UnifiedAccessController.has_access(request.user, self.module_required, 'access'):
            error_msg = self.message or f"You don't have access to the '{self.module_required}' module."
            
            if self.redirect_url:
                messages.error(request, error_msg)
                return redirect(self.redirect_url)
            else:
                return HttpResponseForbidden(error_msg)
        
        return super().dispatch(request, *args, **kwargs)


class FeatureRequiredMixin:
    """
    Updated mixin to enforce feature access using unified access control
    """
    feature_required = None
    redirect_url = None
    message = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.feature_required:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define 'feature_required' attribute."
            )
        
        # Use unified access controller for consistency
        if not UnifiedAccessController.has_access(request.user, self.feature_required, 'access'):
            error_msg = self.message or f"You don't have access to the '{self.feature_required}' feature."
            
            if self.redirect_url:
                messages.error(request, error_msg)
                return redirect(self.redirect_url)
            else:
                return HttpResponseForbidden(error_msg)
        
        # Check if it's a trial feature and if the trial has expired
        try:
            feature_entitlement = TenantFeatureEntitlement.objects.get(
                tenant=request.user.tenant,
                feature_key=self.feature_required
            )
            
            if (feature_entitlement.entitlement_type == 'trial' and 
                feature_entitlement.trial_end_date and 
                feature_entitlement.trial_end_date < request.user.tenant.now()):
                error_msg = f"The trial for '{self.feature_required}' has expired."
                
                if self.redirect_url:
                    messages.error(request, error_msg)
                    return redirect(self.redirect_url)
                else:
                    return HttpResponseForbidden(error_msg)
        except TenantFeatureEntitlement.DoesNotExist:
            pass
        
        return super().dispatch(request, *args, **kwargs)


class TenantAwareViewMixin:
    """
    Mixin to filter querysets by the current user's tenant.
    This ensures data isolation in multi-tenant environments.
    """
    def get_queryset(self):
        # Allow views to define a base queryset
        if hasattr(super(), 'get_queryset'):
            queryset = super().get_queryset()
        elif hasattr(self, 'model') and self.model:
            queryset = self.model.objects.all()
        else:
             # Fallback or error, but let's assume usage in generic views
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not have a model or get_queryset method."
            )
        
        # Apply tenant filtering if the model inherits from TenantAwareModel
        if hasattr(self.model, 'tenant') or hasattr(queryset.model, 'tenant'):
            return queryset.filter(tenant=self.request.user.tenant)
        
        return queryset


class UnifiedAccessRequiredMixin:
    """
    NEW: A unified mixin that works with the central access control system
    """
    required_access = None
    access_action = 'access'
    redirect_url = None
    message = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.required_access:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define 'required_access' attribute."
            )
        
        if not UnifiedAccessController.has_access(request.user, self.required_access, self.access_action):
            error_msg = self.message or f"You don't have access to perform '{self.access_action}' on '{self.required_access}'."
            
            if self.redirect_url:
                messages.error(request, error_msg)
                return redirect(self.redirect_url)
            else:
                return HttpResponseForbidden(error_msg)
        
        return super().dispatch(request, *args, **kwargs)