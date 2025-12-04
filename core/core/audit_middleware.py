"""
Audit Logging Middleware for SalesCompass CRM

Automatically captures audit logs for:
- User authentication events
- Data modifications (create, update, delete)
- Sensitive operations
- API access
"""
import json
import logging
from typing import Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def get_request_metadata(request) -> dict:
    """Extract metadata from request for audit logging."""
    return {
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'path': request.path,
        'method': request.method,
        'timestamp': timezone.now().isoformat(),
    }


class AuditLoggingMiddleware:
    """
    Middleware to automatically log audit events.
    
    Captures:
    - User login/logout events
    - API requests to sensitive endpoints
    - Data modification operations
    """
    
    SENSITIVE_PATHS = [
        '/admin/',
        '/api/',
        '/billing/',
        '/settings/',
        '/users/',
        '/roles/',
        '/tenants/',
    ]
    
    AUDIT_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request._audit_metadata = get_request_metadata(request)
        
        response = self.get_response(request)
        
        if self._should_audit(request, response):
            self._log_request(request, response)
        
        return response
    
    def _should_audit(self, request, response) -> bool:
        """Determine if request should be audited."""
        if request.method not in self.AUDIT_METHODS:
            return False
        
        for path in self.SENSITIVE_PATHS:
            if request.path.startswith(path):
                return True
        
        return False
    
    def _log_request(self, request, response) -> None:
        """Log the request to audit logs (non-blocking, graceful degradation)."""
        try:
            from audit_logs.models import AuditLog
            
            user = request.user if request.user.is_authenticated else None
            action_type = self._determine_action_type(request)
            severity = self._determine_severity(request, response)
            
            AuditLog.log_action(
                user=user,
                action_type=action_type,
                resource_type=self._extract_resource_type(request.path),
                resource_id=self._extract_resource_id(request.path),
                description=f"{request.method} {request.path}",
                severity=severity,
                ip_address=request._audit_metadata.get('ip_address', '0.0.0.0'),
                user_agent=request._audit_metadata.get('user_agent', ''),
                response_status=response.status_code,
            )
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Audit log failed (non-fatal): {e}")
    
    def _determine_action_type(self, request) -> str:
        """Determine action type from request."""
        method_mapping = {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE',
        }
        
        base_action = method_mapping.get(request.method, 'ACCESS')
        resource = self._extract_resource_type(request.path)
        return f"{resource}_{base_action}".upper()
    
    def _determine_severity(self, request, response) -> str:
        """Determine severity based on action and result."""
        if response.status_code >= 500:
            return 'error'
        if request.method == 'DELETE':
            return 'warning'
        if 'billing' in request.path or 'payment' in request.path:
            return 'warning'
        return 'info'
    
    def _extract_resource_type(self, path: str) -> str:
        """Extract resource type from URL path."""
        parts = [p for p in path.split('/') if p]
        if parts:
            return parts[0].replace('-', '_')
        return 'unknown'
    
    def _extract_resource_id(self, path: str) -> str:
        """Extract resource ID from URL path."""
        parts = [p for p in path.split('/') if p]
        for part in parts[1:]:
            if part.isdigit():
                return part
        return ''


def log_model_change(sender, instance, action: str, user=None, 
                     state_before: dict = None, state_after: dict = None,
                     request=None) -> None:
    """
    Log a model change to audit logs.
    
    Usage:
        from core.audit_middleware import log_model_change
        
        # Before save
        state_before = model_to_dict(instance)
        instance.save()
        state_after = model_to_dict(instance)
        
        log_model_change(
            sender=Instance.__class__,
            instance=instance,
            action='UPDATE',
            user=request.user,
            state_before=state_before,
            state_after=state_after,
            request=request,
        )
    """
    try:
        from audit_logs.models import AuditLog
        
        ip_address = '0.0.0.0'
        user_agent = ''
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        model_name = sender.__name__ if hasattr(sender, '__name__') else str(sender)
        
        AuditLog.log_action(
            user=user,
            action_type=f"{model_name}_{action}".upper(),
            resource_type=model_name,
            resource_id=str(instance.pk) if instance.pk else '',
            description=f"{action} {model_name}",
            severity='info' if action == 'CREATE' else 'warning' if action == 'DELETE' else 'info',
            state_before=state_before,
            state_after=state_after,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except ImportError:
        logger.debug("Audit logs module not available")
    except Exception as e:
        logger.error(f"Failed to log model change: {e}")
