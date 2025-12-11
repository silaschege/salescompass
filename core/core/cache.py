"""
Caching utilities for business metrics calculations
"""
from django.core.cache import cache
from core.services.business_metrics_service import BusinessMetricsService
from datetime import timedelta
import hashlib


class BusinessMetricsCache:
    """
    Cache class for business metrics calculations
    """
    
    @staticmethod
    def get_cache_key(metric_type, tenant_id=None, user_id=None, **kwargs):
        """
        Generate a unique cache key for the specified metric type and parameters
        """
        key_parts = [metric_type]
        if tenant_id:
            key_parts.append(f"tenant:{tenant_id}")
        if user_id:
            key_parts.append(f"user:{user_id}")
        
        # Add any additional parameters to the key
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        # Create a hash of the key parts to ensure consistent length
        key_string = ":".join(key_parts)
        return f"metrics:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    @classmethod
    def get_clv_metrics(cls, tenant_id=None, user_id=None, timeout=3600):
        """
        Get cached CLV metrics or calculate and cache them
        """
        cache_key = cls.get_cache_key("clv", tenant_id=tenant_id, user_id=user_id)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Calculate metrics
        result = BusinessMetricsService.calculate_clv_metrics(tenant_id=tenant_id)
        
        # Cache the result
        cache.set(cache_key, result, timeout=timeout)
        
        return result
    
    @classmethod
    def get_cac_metrics(cls, tenant_id=None, user_id=None, timeout=3600):
        """
        Get cached CAC metrics or calculate and cache them
        """
        cache_key = cls.get_cache_key("cac", tenant_id=tenant_id, user_id=user_id)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Calculate metrics
        result = BusinessMetricsService.calculate_cac_metrics(tenant_id=tenant_id)
        
        # Cache the result
        cache.set(cache_key, result, timeout=timeout)
        
        return result
    
    @classmethod
    def get_sales_velocity_metrics(cls, tenant_id=None, user_id=None, timeout=3600):
        """
        Get cached sales velocity metrics or calculate and cache them
        """
        cache_key = cls.get_cache_key("sales_velocity", tenant_id=tenant_id, user_id=user_id)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Calculate metrics
        result = BusinessMetricsService.calculate_sales_velocity_metrics(tenant_id=tenant_id)
        
        # Cache the result
        cache.set(cache_key, result, timeout=timeout)
        
        return result
    
    @classmethod
    def get_roi_metrics(cls, tenant_id=None, user_id=None, timeout=3600):
        """
        Get cached ROI metrics or calculate and cache them
        """
        cache_key = cls.get_cache_key("roi", tenant_id=tenant_id, user_id=user_id)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Calculate metrics
        result = BusinessMetricsService.calculate_roi_metrics(tenant_id=tenant_id)
        
        # Cache the result
        cache.set(cache_key, result, timeout=timeout)
        
        return result
    
    @classmethod
    def get_conversion_funnel_metrics(cls, tenant_id=None, user_id=None, timeout=3600):
        """
        Get cached conversion funnel metrics or calculate and cache them
        """
        cache_key = cls.get_cache_key("conversion_funnel", tenant_id=tenant_id, user_id=user_id)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Calculate metrics
        result = BusinessMetricsService.calculate_conversion_funnel_metrics(tenant_id=tenant_id)
        
        # Cache the result
        cache.set(cache_key, result, timeout=timeout)
        
        return result
    
    @classmethod
    def get_metrics_trend(cls, days=30, tenant_id=None, user_id=None, timeout=7200):
        """
        Get cached metrics trend or calculate and cache them
        """
        cache_key = cls.get_cache_key("trend", tenant_id=tenant_id, user_id=user_id, days=days)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Calculate metrics
        result = BusinessMetricsService.calculate_metrics_trend(days=days, tenant_id=tenant_id)
        
        # Cache the result (with longer timeout since trends take longer to compute)
        cache.set(cache_key, result, timeout=timeout)
        
        return result
    
    @classmethod
    def invalidate_metrics_cache(cls, metric_type=None, tenant_id=None, user_id=None):
        """
        Invalidate cached metrics for a specific metric type and tenant/user
        """
        if metric_type:
            cache_key = cls.get_cache_key(metric_type, tenant_id=tenant_id, user_id=user_id)
            cache.delete(cache_key)
        else:
            # If no specific metric type, invalidate all metrics for tenant/user
            for metric_type in ["clv", "cac", "sales_velocity", "roi", "conversion_funnel", "trend"]:
                cache_key = cls.get_cache_key(metric_type, tenant_id=tenant_id, user_id=user_id)
                cache.delete(cache_key)
    
    @classmethod
    def invalidate_all_metrics_cache(cls, tenant_id=None):
        """
        Invalidate all cached metrics for a specific tenant
        """
        # This would require a more sophisticated cache implementation
        # that supports pattern-based deletion
        pass
