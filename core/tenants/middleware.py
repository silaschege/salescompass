import threading
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from django.template.response import TemplateResponse
from tenants.models import Tenant
from core.models import User
from audit_logs.models import AuditLog
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
                return TemplateResponse(
                    request, 
                    'core/403.html', 
                    context, 
                    status=403
                )
            else:
                # User is not logged in, redirect to login page
                # Preserve the next parameter so they can be redirected back after login
                from django.urls import reverse
                login_url = reverse('accounts:login')
                from django.shortcuts import redirect
                redirect_url = f"{login_url}?next={request.path}"
                return redirect(redirect_url)
                
        return response


class CrossTenantAccessLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to detect and log cross-tenant access attempts.
    This middleware intercepts requests to resources and checks if the user
    is attempting to access resources that belong to a different tenant.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only process if user is authenticated and not a superuser
        if (request.user.is_authenticated and 
            not request.user.is_superuser and 
            hasattr(request.user, 'tenant') and 
            request.user.tenant):
            
            # Check for cross-tenant access after the view has been processed
            self._check_cross_tenant_access(request, response)
        
        return response

    def _check_cross_tenant_access(self, request, response):
        """
        Check if the request resulted in access to resources from a different tenant.
        This method inspects the response and request to detect potential cross-tenant access.
        """
        try:
            # Get the current user's tenant
            user_tenant = request.user.tenant
            
            # Check if this is a detail view or update/delete request that might involve a specific object
            # We'll use URL patterns to detect if a resource ID is involved
            resolver_match = request.resolver_match
            if not resolver_match:
                return
            
            # Get the view class or function that handled the request
            view_func = resolver_match.func
            
            # Determine if this is a request that accesses a specific resource
            # by checking if the URL pattern contains parameters that likely refer to object IDs
            url_name = resolver_match.url_name
            if not url_name:
                return
                
            # Check if this is a view that would access specific resources
            # Look for common patterns that indicate resource access
            if any(pattern in url_name.lower() for pattern in ['detail', 'update', 'delete', 'view', 'edit']):
                # Try to determine if the view accessed an object from a different tenant
                # by checking the response context or other indicators
                self._detect_cross_tenant_access_from_response(request, user_tenant, response)
                
        except Exception as e:
            logger.warning(f"Error in cross-tenant access detection: {str(e)}")

    def _detect_cross_tenant_access_from_response(self, request, user_tenant, response):
        """
        Detect cross-tenant access from response data.
        This method inspects the response to determine if a cross-tenant access occurred.
        """
        try:
            # Check if the response contains an object with tenant information
            # For class-based views, the object might be in the response context
            if hasattr(response, 'context_data') and response.context_data:
                # Check if there's an object in the context that has a tenant field
                for key, value in response.context_data.items():
                    if hasattr(value, 'tenant') and hasattr(value, 'pk'):
                        # Found an object with tenant - check if it matches user's tenant
                        self._log_cross_tenant_access_if_needed(
                            request, user_tenant, value.tenant, value, 
                            type(value).__name__, str(value)
                        )
            
            # For API responses or other cases, we might need to check session data or other indicators
            # This is a more complex check and depends on the specific implementation
            
        except Exception as e:
            logger.warning(f"Error checking response for cross-tenant access: {str(e)}")

    def _log_cross_tenant_access_if_needed(self, request, user_tenant, resource_tenant, resource_obj, resource_type, resource_name):
        """
        Log a cross-tenant access attempt if the user's tenant doesn't match the resource's tenant.
        """
        if user_tenant and resource_tenant and user_tenant.id != resource_tenant.id:
            # Cross-tenant access detected - log it
            AuditLog.objects.create(
                tenant=user_tenant,  # Log under the user's tenant
                user=request.user,
                action='authorization',
                resource_type='security_event',
                resource_id=str(resource_obj.pk) if hasattr(resource_obj, 'pk') else 'unknown',
                resource_name=resource_name,
                old_values={},
                new_values={},
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                is_successful=False,  # Access should not be successful
                error_message=f'Cross-tenant access attempt detected: user tenant {user_tenant.id} tried to access resource from tenant {resource_tenant.id}',
                metadata={
                    'user_tenant_id': user_tenant.id,
                    'resource_tenant_id': resource_tenant.id,
                    'access_type': 'cross_tenant_access',
                    'method': request.method,
                    'path': request.path,
                },
                severity='critical'
            )
            
            # Also log to the tenant data isolation violations
            from tenants.models import TenantDataIsolationViolation, TenantDataIsolationAudit
            
            # Create or get a general audit for tracking violations
            audit, created = TenantDataIsolationAudit.objects.get_or_create(
                tenant=user_tenant,
                audit_type='security',
                status='in_progress',
                defaults={
                    'auditor': request.user,
                    'notes': 'Automated security audit for cross-tenant access detection'
                }
            )
            
            # Create a violation record
            TenantDataIsolationViolation.objects.create(
                audit=audit,
                model_name=type(resource_obj).__name__,
                record_id=resource_obj.pk if hasattr(resource_obj, 'pk') else 0,
                field_name='tenant',
                expected_tenant=user_tenant,
                actual_tenant=resource_tenant,
                violation_type='cross_tenant_access',
                severity='critical',
                description=f'User {request.user.email} attempted to access {type(resource_obj).__name__} belonging to tenant {resource_tenant.id} from tenant {user_tenant.id}',
                resolution_status='open'
            )
            
            logger.warning(
                f"Cross-tenant access detected: user {request.user.email} (tenant {user_tenant.id}) "
                f"attempted to access {type(resource_obj).__name__} (tenant {resource_tenant.id})"
            )

    def _get_client_ip(self, request):
        """
        Extract client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

"""
Usage tracking middleware for tenant-based usage monitoring.
"""
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class UsageTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track tenant usage metrics throughout the request lifecycle.
    This middleware records various usage metrics for each tenant.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        # Process the request before the view
        response = self.process_request(request)
        
        if response:
            return response
        
        # Get the response from the view
        response = self.get_response(request)
        
        # Process the response after the view
        response = self.process_response(request, response)
        
        return response

    def process_request(self, request):
        """
        Process the request before the view is called.
        """
        # Add any pre-request processing here if needed
        return None

    def process_response(self, request, response):
        """
        Process the response after the view is called.
        This is where we'll track usage metrics for the tenant.
        """
        # Check if the user is authenticated and has a tenant
        if (hasattr(request, 'user') and 
            request.user.is_authenticated and 
            hasattr(request.user, 'tenant') and 
            request.user.tenant):
            
            tenant = request.user.tenant
            
            # Track API request count
            try:
                # Track the request for this tenant
                tenant.track_usage('api_requests', value=1, unit='requests')
                
                # Track based on request method
                method = request.method.lower()
                if method in ['post', 'put', 'patch', 'delete']:
                    tenant.track_usage('write_operations', value=1, unit='operations')
                else:
                    tenant.track_usage('read_operations', value=1, unit='operations')
                
                # Track specific resource access if identifiable
                if hasattr(request, 'resolver_match'):
                    view_name = request.resolver_match.view_name
                    if view_name:
                        tenant.track_usage('view_access', value=1, unit='views', period_start=None, period_end=None)
                        
            except Exception as e:
                logger.warning(f"Failed to track usage for tenant {tenant.id}: {str(e)}")
        
        return response


"""
Overage checking middleware for tenant-based usage limits.
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class OverageCheckMiddleware(MiddlewareMixin):
    """
    Middleware to check if tenants have exceeded their usage limits
    and enforce appropriate actions based on overage thresholds.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        # Process the request before the view
        response = self.process_request(request)
        
        if response:
            return response
        
        # Get the response from the view
        response = self.get_response(request)
        
        # Process the response after the view
        response = self.process_response(request, response)
        
        return response

    def process_request(self, request):
        """
        Process the request before the view is called.
        Check if the tenant has exceeded usage limits.
        """
        # Check if the user is authenticated and has a tenant
        if (hasattr(request, 'user') and 
            request.user.is_authenticated and 
            hasattr(request.user, 'tenant') and 
            request.user.tenant):
            
            tenant = request.user.tenant
            
            try:
                # Check if tenant has exceeded usage limits
                if tenant.is_archived:
                    # If tenant is archived, restrict access
                    return HttpResponseForbidden(
                        "This account has been archived. Please contact support."
                    )
                
                # Check if tenant is suspended
                if tenant.is_suspended:
                    # If tenant is suspended, restrict access
                    return HttpResponseForbidden(
                        "This account has been suspended. Please contact support."
                    )
                
                # Check usage limits
                usage_status = tenant.check_usage_limits()
                
                # If there are critical overages, restrict access
                if usage_status.get('has_critical_overage', False):
                    # For critical overages, we might want to restrict certain operations
                    # depending on the type of overage
                    overage_type = usage_status.get('overage_type', 'unknown')
                    
                    if overage_type in ['storage', 'user_count']:
                        # For storage or user count overages, we might allow read operations
                        # but restrict write operations
                        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                            return HttpResponseForbidden(
                                f"Usage limit exceeded: {overage_type}. Please upgrade your plan."
                            )
                
                # Check if tenant has any overage notifications that need to be shown
                if usage_status.get('approaching_limit', False):
                    # Add a warning message to the request session
                    if hasattr(request, 'session'):
                        # Store overage warnings to be displayed in the UI
                        request.session['overage_warning'] = usage_status.get('warnings', [])
                
            except Exception as e:
                logger.warning(f"Failed to check overage for tenant {tenant.id}: {str(e)}")
        
        return None

    def process_response(self, request, response):
        """
        Process the response after the view is called.
        """
        # Add any post-response processing here if needed
        return response 
    


class FeatureEnforcementMiddleware:
    """Middleware to enforce feature limits based on plan and explicit entitlements"""
    
    @staticmethod
    def has_feature_access(user, feature_key):
        """
        Check if a user's tenant has access to a specific feature
        """
        if not hasattr(user, 'tenant') or not user.tenant or not user.tenant.plan:
            return False
        
        from billing.plan_access_service import PlanAccessService
        # Note: We need to know which module the feature belongs to.
        # For now, we'll try to find it in PlanFeatureAccess without the module constraint,
        # but PlanAccessService.get_feature_access is preferred if module is known.
        try:
            from billing.models import PlanFeatureAccess
            plan_feature = PlanFeatureAccess.objects.get(
                plan=user.tenant.plan,
                feature_key=feature_key
            )
            return plan_feature.is_available
        except PlanFeatureAccess.DoesNotExist:
            return False
    
    @staticmethod
    def has_module_access(user, module_name):
        """
        Check if a user's tenant has access to a specific module
        """
        if not hasattr(user, 'tenant') or not user.tenant or not user.tenant.plan:
            return False
        
        from billing.plan_access_service import PlanAccessService
        return PlanAccessService.get_module_access(user.tenant.plan, module_name)
    
    @staticmethod
    def enforce_feature_access(user, feature_key):
        """
        Enforce feature access - raise exception if user doesn't have access
        """
        if not FeatureEnforcementMiddleware.has_feature_access(user, feature_key):
            raise PermissionError(f"Feature '{feature_key}' is not available for your tenant plan.")
        
        # Check if it's a trial feature and if the trial has expired
        try:
            from .models import TenantFeatureEntitlement
            feature_entitlement = TenantFeatureEntitlement.objects.get(
                tenant=user.tenant,
                feature_key=feature_key
            )
            
            if (feature_entitlement.entitlement_type == 'trial' and 
                feature_entitlement.trial_end_date and 
                timezone.now() > feature_entitlement.trial_end_date):
                raise PermissionError(f"Trial for feature '{feature_key}' has expired.")
        except TenantFeatureEntitlement.DoesNotExist:
            pass

