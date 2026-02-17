"""
API endpoints for business metrics
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from core.services.business_metrics_service import BusinessMetricsService
import json


@require_http_methods(["GET"])
@login_required
def clv_metrics_api(request):
    """
    API endpoint to get CLV metrics
    """
    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_clv_metrics(tenant_id=tenant_id)
    
    return JsonResponse(metrics)


@require_http_methods(["GET"])
@login_required
def cac_metrics_api(request):
    """
    API endpoint to get CAC metrics
    """
    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_cac_metrics(tenant_id=tenant_id)
    
    return JsonResponse(metrics)


@require_http_methods(["GET"])
@login_required
def sales_velocity_metrics_api(request):
    """
    API endpoint to get sales velocity metrics
    """
    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_sales_velocity_metrics(tenant_id=tenant_id)
    
    return JsonResponse(metrics)


@require_http_methods(["GET"])
@login_required
def roi_metrics_api(request):
    """
    API endpoint to get ROI metrics
    """
    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_roi_metrics(tenant_id=tenant_id)
    
    return JsonResponse(metrics)


@require_http_methods(["GET"])
@login_required
def conversion_funnel_metrics_api(request):
    """
    API endpoint to get conversion funnel metrics
    """
    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_conversion_funnel_metrics(tenant_id=tenant_id)
    
    return JsonResponse(metrics)


@require_http_methods(["GET"])
@login_required
def metrics_trend_api(request):
    """
    API endpoint to get metrics trends
    """
    days = int(request.GET.get('days', 30))
    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_metrics_trend(days=days, tenant_id=tenant_id)
    
    return JsonResponse(metrics)


class BusinessMetricsAPIView(View):
    """
    Class-based view for business metrics API
    """
    
    @method_decorator(login_required)
    def get(self, request):
        """
        Get all business metrics
        """
        tenant_id = getattr(request.user, 'tenant_id', None)
        
        clv_metrics = BusinessMetricsService.calculate_clv_metrics(tenant_id=tenant_id)
        cac_metrics = BusinessMetricsService.calculate_cac_metrics(tenant_id=tenant_id)
        sales_velocity_metrics = BusinessMetricsService.calculate_sales_velocity_metrics(tenant_id=tenant_id)
        roi_metrics = BusinessMetricsService.calculate_roi_metrics(tenant_id=tenant_id)
        funnel_metrics = BusinessMetricsService.calculate_conversion_funnel_metrics(tenant_id=tenant_id)
        
        all_metrics = {
            'clv_metrics': clv_metrics,
            'cac_metrics': cac_metrics,
            'sales_velocity_metrics': sales_velocity_metrics,
            'roi_metrics': roi_metrics,
            'funnel_metrics': funnel_metrics,
        }
        
        return JsonResponse(all_metrics)
