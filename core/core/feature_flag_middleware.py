"""
Feature Flag Enforcement Middleware for SalesCompass CRM

Provides:
- Automatic feature flag checking based on URL patterns
- Template context with feature flags
- API for checking feature flags programmatically
"""
import re
import logging
from typing import Optional, Dict, Any
from functools import lru_cache
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


class FeatureFlagCache:
    """In-memory cache for feature flags to reduce database queries."""
    
    _cache: Dict[str, Any] = {}
    _cache_timeout = 60
    
    @classmethod
    def get(cls, key: str, user) -> Optional[bool]:
        """Get cached flag status for user."""
        cache_key = f"{key}:{user.id if user else 'anon'}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        return None
    
    @classmethod
    def set(cls, key: str, user, value: bool) -> None:
        """Cache flag status for user."""
        cache_key = f"{key}:{user.id if user else 'anon'}"
        cls._cache[cache_key] = value
    
    @classmethod
    def clear(cls) -> None:
        """Clear the cache."""
        cls._cache = {}


def is_feature_enabled(feature_key: str, user=None) -> bool:
    """
    Check if a feature is enabled for a user.
    
    Args:
        feature_key: The feature flag key (e.g., 'new_dashboard')
        user: Optional user object
    
    Returns:
        bool: True if feature is enabled, False otherwise
    
    Usage:
        from core.feature_flag_middleware import is_feature_enabled
        
        if is_feature_enabled('new_dashboard', request.user):
            return render(request, 'new_dashboard.html')
        else:
            return render(request, 'old_dashboard.html')
    """
    if user and hasattr(user, 'is_superuser') and user.is_superuser:
        return True
    
    if user and hasattr(user, 'is_staff') and user.is_staff:
        return True
    
    cached = FeatureFlagCache.get(feature_key, user)
    if cached is not None:
        return cached
    
    try:
        from feature_flags.models import FeatureFlag
        
        flag = FeatureFlag.objects.filter(key=feature_key).first()
        if not flag:
            FeatureFlagCache.set(feature_key, user, False)
            return False
        
        enabled = flag.is_enabled_for_user(user) if user else flag.is_active
        FeatureFlagCache.set(feature_key, user, enabled)
        return enabled
        
    except ImportError:
        return True
    except Exception as e:
        logger.warning(f"Feature flag check failed (allowing access): {e}")
        return True


def get_all_features(user=None) -> Dict[str, bool]:
    """
    Get all feature flags and their status for a user.
    
    Returns:
        Dict[str, bool]: Dictionary of feature keys to enabled status
    """
    try:
        from feature_flags.models import FeatureFlag
        
        flags = FeatureFlag.objects.filter(is_active=True)
        return {
            flag.key: flag.is_enabled_for_user(user) if user else flag.is_active
            for flag in flags
        }
    except ImportError:
        return {}
    except Exception as e:
        logger.error(f"Error getting feature flags: {e}")
        return {}


class FeatureFlagMiddleware:
    """
    Middleware to enforce feature flags based on URL patterns.
    
    Configure in settings.py:
        FEATURE_FLAG_URL_RULES = {
            '/new-dashboard/': 'new_dashboard',
            '/beta/': 'beta_features',
            '/api/v2/': 'api_v2',
        }
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.url_rules = getattr(settings, 'FEATURE_FLAG_URL_RULES', {})
        self._compiled_rules = self._compile_rules()
    
    def _compile_rules(self) -> list:
        """Compile URL patterns for faster matching."""
        compiled = []
        for pattern, flag_key in self.url_rules.items():
            if pattern.startswith('^') or pattern.endswith('$'):
                compiled.append((re.compile(pattern), flag_key))
            else:
                compiled.append((pattern, flag_key))
        return compiled
    
    def __call__(self, request):
        try:
            required_flag = self._get_required_flag(request.path)
            
            if required_flag:
                user = request.user if request.user.is_authenticated else None
                
                if not is_feature_enabled(required_flag, user):
                    return self._handle_disabled_feature(request, required_flag)
            
            request.feature_flags = lambda key: is_feature_enabled(key, request.user if request.user.is_authenticated else None)
            request.all_features = lambda: get_all_features(request.user if request.user.is_authenticated else None)
        except Exception as e:
            logger.warning(f"Feature flag middleware error (allowing request): {e}")
        
        response = self.get_response(request)
        return response
    
    def _get_required_flag(self, path: str) -> Optional[str]:
        """Get the feature flag required for a path."""
        for rule, flag_key in self._compiled_rules:
            if isinstance(rule, str):
                if path.startswith(rule):
                    return flag_key
            else:
                if rule.match(path):
                    return flag_key
        return None
    
    def _handle_disabled_feature(self, request, flag_key: str):
        """Handle access to a disabled feature."""
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'feature_disabled',
                'message': f'This feature is not available yet.',
                'feature': flag_key,
            }, status=403)
        
        return render(request, 'core/feature_disabled.html', {
            'feature_key': flag_key,
        }, status=403)


def feature_flag_context_processor(request):
    """
    Context processor to add feature flags to templates.
    
    Usage in template:
        {% if features.new_dashboard %}
            <a href="/new-dashboard/">Try New Dashboard</a>
        {% endif %}
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        features = get_all_features(request.user)
    else:
        features = get_all_features()
    
    return {
        'features': features,
        'is_feature_enabled': lambda key: is_feature_enabled(key, getattr(request, 'user', None)),
    }


def require_feature(feature_key: str):
    """
    Decorator to require a feature flag for a view.
    
    Usage:
        @require_feature('new_reports')
        def new_reports_view(request):
            ...
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            user = request.user if request.user.is_authenticated else None
            
            if not is_feature_enabled(feature_key, user):
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'feature_disabled',
                        'message': 'This feature is not available yet.',
                    }, status=403)
                return render(request, 'core/feature_disabled.html', {
                    'feature_key': feature_key,
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
