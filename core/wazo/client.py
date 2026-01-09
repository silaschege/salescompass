"""
Core Wazo API client with multi-service support for SalesCompass CRM.
Handles authentication, requests, and health checks for all Wazo services.
"""
import logging
import requests
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WazoAPIClient:
    """
    Core Wazo API client handling authentication and requests.
    Supports multiple Wazo services (auth, calld, chatd, etc.)
    """
    
    # Default service URLs
    SERVICE_URLS = {
        'auth': '/api/auth/0.1',
        'calld': '/api/calld/1.0',
        'chatd': '/api/chatd/1.0',
        'confd': '/api/confd/1.1',
        'agentd': '/api/agentd/1.0',
        'call-logd': '/api/call-logd/1.0',
        'webhookd': '/api/webhookd/1.0',
    }
    
    def __init__(self, service: str = 'auth'):
        self.base_url = getattr(settings, 'WAZO_API_URL', None)
        self.api_key = getattr(settings, 'WAZO_API_KEY', None)
        self.tenant_uuid = getattr(settings, 'WAZO_TENANT_UUID', None)
        self.service = service
        self._session = None
        
        # Service-specific URLs from settings
        self.service_urls = {
            'calld': getattr(settings, 'WAZO_CALLD_URL', None),
            'chatd': getattr(settings, 'WAZO_CHATD_URL', None),
            'confd': getattr(settings, 'WAZO_CONFD_URL', None),
            'agentd': getattr(settings, 'WAZO_AGENTD_URL', None),
            'call-logd': getattr(settings, 'WAZO_CALL_LOG_URL', None),
            'webhookd': getattr(settings, 'WAZO_WEBHOOKD_URL', None),
        }
    
    def is_configured(self) -> bool:
        """Check if Wazo is configured with required settings."""
        return bool(self.base_url and self.api_key)
    
    def get_service_url(self, service: str = None) -> Optional[str]:
        """Get the base URL for a specific Wazo service."""
        svc = service or self.service
        
        # Check for service-specific URL from settings
        if svc in self.service_urls and self.service_urls[svc]:
            return self.service_urls[svc]
        
        # Fall back to base URL + service path
        if self.base_url:
            return f"{self.base_url.rstrip('/')}{self.SERVICE_URLS.get(svc, '')}"
        
        return None
    
    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session with auth headers."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'X-Auth-Token': self.api_key or '',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            })
            if self.tenant_uuid:
                self._session.headers['Wazo-Tenant'] = self.tenant_uuid
        return self._session
    
    def _request(self, method: str, endpoint: str, service: str = None, **kwargs) -> Dict:
        """Make an HTTP request to Wazo API."""
        if not self.is_configured():
            logger.error("Wazo API is not configured.")
            return {"error": "Not configured", "success": False}
        
        base = self.get_service_url(service)
        if not base:
            return {"error": f"Service {service} not configured", "success": False}
            
        url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            # Convert 'data' to 'json' for proper JSON request
            if 'data' in kwargs and isinstance(kwargs['data'], dict):
                kwargs['json'] = kwargs.pop('data')
            
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            
            result = response.json() if response.content else {}
            result['success'] = True
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Wazo API Timeout: {url}")
            return {"error": "Request timeout", "success": False}
        except requests.exceptions.ConnectionError:
            logger.error(f"Wazo API Connection Error: {url}")
            return {"error": "Connection failed", "success": False}
        except requests.exceptions.HTTPError as e:
            logger.error(f"Wazo API HTTP Error: {e}")
            return {"error": str(e), "success": False, "status_code": e.response.status_code}
        except Exception as e:
            logger.error(f"Wazo API Request Error: {e}")
            return {"error": str(e), "success": False}

    def get(self, endpoint: str, service: str = None, **kwargs) -> Dict:
        """HTTP GET request."""
        return self._request('GET', endpoint, service, **kwargs)

    def post(self, endpoint: str, service: str = None, **kwargs) -> Dict:
        """HTTP POST request."""
        return self._request('POST', endpoint, service, **kwargs)

    def put(self, endpoint: str, service: str = None, **kwargs) -> Dict:
        """HTTP PUT request."""
        return self._request('PUT', endpoint, service, **kwargs)

    def delete(self, endpoint: str, service: str = None, **kwargs) -> Dict:
        """HTTP DELETE request."""
        return self._request('DELETE', endpoint, service, **kwargs)
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all Wazo services."""
        results = {}
        
        for service in ['auth', 'calld', 'chatd', 'confd']:
            try:
                response = self.get('status', service=service)
                results[service] = response.get('success', False)
            except Exception:
                results[service] = False
        
        return results
    
    def get_token(self, username: str, password: str) -> Optional[str]:
        """
        Get authentication token from Wazo auth service.
        Used for initial setup or token refresh.
        """
        try:
            # Temporarily remove token header for auth request
            old_token = self.session.headers.get('X-Auth-Token')
            self.session.headers.pop('X-Auth-Token', None)
            
            response = self.post('token', service='auth', data={
                'username': username,
                'password': password,
                'expiration': 3600 * 24,  # 24 hours
            })
            
            # Restore token header
            if old_token:
                self.session.headers['X-Auth-Token'] = old_token
            
            if response.get('success'):
                return response.get('data', {}).get('token')
            return None
            
        except Exception as e:
            logger.error(f"Failed to get Wazo token: {e}")
            return None


# Singleton instance for default client
wazo_client = WazoAPIClient()
