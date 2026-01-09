# File: /home/silaskimani/Documents/replit/git/salescompass/core/tenants/mixins.py
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from .models import TenantFeatureEntitlement
from .views import FeatureEnforcementMiddleware
from core.utils import check_cross_tenant_access
from django.core.exceptions import ImproperlyConfigured



class ModuleRequiredMixin:
    """
    Mixin to enforce module access for class-based views
    """
    module_required = None
    redirect_url = None
    message = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.module_required:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define 'module_required' attribute."
            )
        
        # Check if user has access to the module
        if not FeatureEnforcementMiddleware.has_module_access(request.user, self.module_required):
            error_msg = self.message or f"You don't have access to the '{self.module_required}' module."
            
            if self.redirect_url:
                messages.error(request, error_msg)
                return redirect(self.redirect_url)
            else:
                return HttpResponseForbidden(error_msg)
        
        return super().dispatch(request, *args, **kwargs)


class FeatureRequiredMixin:
    """
    Mixin to enforce feature access for class-based views
    """
    feature_required = None
    redirect_url = None
    message = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.feature_required:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define 'feature_required' attribute."
            )
        
        # Check if user has access to the feature
        if not FeatureEnforcementMiddleware.has_feature_access(request.user, self.feature_required):
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
             return None 
             
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            return queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset

    def get_object(self, queryset=None):
        """
        Override get_object to check for cross-tenant access when retrieving a single object.
        """
        obj = super().get_object(queryset)
        
        # Check if this is a cross-tenant access attempt
        access_allowed = check_cross_tenant_access(self.request.user, obj, 'read')
        
        if not access_allowed:
            # Log the attempt and raise permission denied
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to access this resource.")
        
        return obj

    def get_form_kwargs(self):
        """
        Inject tenant into form kwargs if available.
        This allows forms to filter dynamic choices by tenant.
        """
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            # Fetch the actual Tenant object if needed by the form, or just pass the ID
            # Based on LeadsForm, it expects 'tenant' object (or at least something with .id)
            # For efficiency we might just pass the user.tenant object if available
            # Assuming user.tenant is available via relation
            if hasattr(self.request.user, 'tenant'):
                 kwargs['tenant'] = self.request.user.tenant
        return kwargs

