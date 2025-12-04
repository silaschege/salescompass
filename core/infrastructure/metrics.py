"""
Infrastructure Metrics Collection for SalesCompass CRM

Provides real-time metrics ingestion for:
- Tenant resource usage (API calls, storage, records)
- System health monitoring
- Performance metrics
- Database connection tracking
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from django.conf import settings
from django.utils import timezone
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and stores metrics for infrastructure monitoring.
    
    Usage:
        from infrastructure.metrics import metrics_collector
        
        # Record an API call
        metrics_collector.record_api_call('tenant_abc', '/api/leads/', 'GET', 200, 0.125)
        
        # Get tenant usage summary
        usage = metrics_collector.get_tenant_usage('tenant_abc')
    """
    
    CACHE_PREFIX = 'metrics:'
    CACHE_TTL = 300
    
    def __init__(self):
        self._local_metrics: Dict[str, Dict] = defaultdict(lambda: {
            'api_calls': 0,
            'api_errors': 0,
            'storage_bytes': 0,
            'records_created': 0,
            'records_updated': 0,
            'records_deleted': 0,
            'active_users': set(),
            'response_times': [],
        })
    
    def record_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: int = None
    ) -> None:
        """Record an API call for a tenant."""
        metrics = self._local_metrics[tenant_id]
        metrics['api_calls'] += 1
        metrics['response_times'].append(response_time)
        
        if status_code >= 400:
            metrics['api_errors'] += 1
        
        if user_id:
            metrics['active_users'].add(user_id)
        
        if len(metrics['response_times']) > 1000:
            metrics['response_times'] = metrics['response_times'][-500:]
        
        self._persist_to_database(tenant_id, 'api_call', {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time,
        })
    
    def record_model_operation(
        self,
        tenant_id: str,
        model_name: str,
        operation: str,
        count: int = 1
    ) -> None:
        """Record model CRUD operations."""
        metrics = self._local_metrics[tenant_id]
        
        if operation == 'create':
            metrics['records_created'] += count
        elif operation == 'update':
            metrics['records_updated'] += count
        elif operation == 'delete':
            metrics['records_deleted'] += count
        
        self._persist_to_database(tenant_id, 'model_operation', {
            'model': model_name,
            'operation': operation,
            'count': count,
        })
    
    def record_storage_usage(self, tenant_id: str, bytes_used: int) -> None:
        """Record storage usage for a tenant."""
        self._local_metrics[tenant_id]['storage_bytes'] = bytes_used
        
        self._persist_to_database(tenant_id, 'storage_update', {
            'bytes_used': bytes_used,
        })
    
    def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get usage summary for a tenant."""
        cache_key = f"{self.CACHE_PREFIX}usage:{tenant_id}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        usage = self._calculate_tenant_usage(tenant_id)
        cache.set(cache_key, usage, self.CACHE_TTL)
        
        return usage
    
    def _calculate_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Calculate comprehensive usage metrics for a tenant."""
        local = self._local_metrics.get(tenant_id, {})
        db_usage = self._get_database_usage(tenant_id)
        
        response_times = local.get('response_times', [])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'tenant_id': tenant_id,
            'timestamp': timezone.now().isoformat(),
            'api_calls': {
                'total': local.get('api_calls', 0) + db_usage.get('api_calls', 0),
                'errors': local.get('api_errors', 0) + db_usage.get('api_errors', 0),
                'avg_response_time_ms': avg_response_time * 1000,
            },
            'records': {
                'created': local.get('records_created', 0),
                'updated': local.get('records_updated', 0),
                'deleted': local.get('records_deleted', 0),
                'total': db_usage.get('total_records', 0),
            },
            'storage': {
                'bytes_used': local.get('storage_bytes', 0) or db_usage.get('storage_bytes', 0),
                'limit_bytes': db_usage.get('storage_limit', 0),
            },
            'users': {
                'active_today': len(local.get('active_users', set())),
                'total': db_usage.get('total_users', 0),
            },
        }
    
    def _get_database_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get usage metrics from database."""
        try:
            from infrastructure.models import TenantUsage
            
            usage = TenantUsage.objects.filter(tenant_id=tenant_id).first()
            
            if usage:
                return {
                    'api_calls': usage.api_calls_count or 0,
                    'api_errors': 0,
                    'total_records': usage.records_count or 0,
                    'storage_bytes': usage.storage_used_mb * 1024 * 1024 if usage.storage_used_mb else 0,
                    'storage_limit': usage.storage_limit_mb * 1024 * 1024 if usage.storage_limit_mb else 0,
                    'total_users': usage.active_users or 0,
                }
            
            return {}
            
        except ImportError:
            logger.debug("Infrastructure models not available")
            return {}
        except Exception as e:
            logger.error(f"Failed to get database usage: {e}")
            return {}
    
    def _persist_to_database(self, tenant_id: str, metric_type: str, data: Dict) -> None:
        """Persist metric to database asynchronously."""
        try:
            from infrastructure.models import TenantUsage
            
            usage, created = TenantUsage.objects.get_or_create(
                tenant_id=tenant_id,
                defaults={
                    'api_calls_count': 0,
                    'records_count': 0,
                }
            )
            
            if metric_type == 'api_call':
                usage.api_calls_count = (usage.api_calls_count or 0) + 1
                usage.last_api_call = timezone.now()
                usage.save(update_fields=['api_calls_count', 'last_api_call'])
            
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Failed to persist metric: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        return {
            'timestamp': timezone.now().isoformat(),
            'database': self._check_database_health(),
            'cache': self._check_cache_health(),
            'celery': self._check_celery_health(),
            'active_tenants': len(self._local_metrics),
        }
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connection health."""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            
            return {
                'status': 'healthy',
                'connections': len(connection.queries),
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
            }
    
    def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache connection health."""
        try:
            test_key = 'health_check_test'
            cache.set(test_key, 'ok', 10)
            result = cache.get(test_key)
            
            return {
                'status': 'healthy' if result == 'ok' else 'degraded',
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
            }
    
    def _check_celery_health(self) -> Dict[str, Any]:
        """Check Celery worker health."""
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', True):
            return {
                'status': 'eager_mode',
                'message': 'Running synchronously (no broker)',
            }
        
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            active = inspect.active()
            
            return {
                'status': 'healthy' if active else 'no_workers',
                'workers': len(active) if active else 0,
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
            }
    
    def flush_metrics(self, tenant_id: str = None) -> None:
        """Flush metrics to database and clear local cache."""
        if tenant_id:
            if tenant_id in self._local_metrics:
                del self._local_metrics[tenant_id]
        else:
            self._local_metrics.clear()
        
        cache.delete_many([
            k for k in cache.keys(f"{self.CACHE_PREFIX}*")
        ] if hasattr(cache, 'keys') else [])


class MetricsMiddleware:
    """
    Middleware to automatically collect API metrics.
    
    Add to MIDDLEWARE in settings.py:
        'infrastructure.metrics.MetricsMiddleware',
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.collector = metrics_collector
    
    def __call__(self, request):
        import time
        start_time = time.time()
        
        response = self.get_response(request)
        
        response_time = time.time() - start_time
        
        if request.path.startswith('/api/'):
            tenant_id = self._get_tenant_id(request)
            user_id = request.user.id if request.user.is_authenticated else None
            
            if tenant_id:
                self.collector.record_api_call(
                    tenant_id=tenant_id,
                    endpoint=request.path,
                    method=request.method,
                    status_code=response.status_code,
                    response_time=response_time,
                    user_id=user_id,
                )
        
        return response
    
    def _get_tenant_id(self, request) -> Optional[str]:
        """Extract tenant ID from request."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return getattr(request.user, 'tenant_id', None)
        return None


metrics_collector = MetricsCollector()
