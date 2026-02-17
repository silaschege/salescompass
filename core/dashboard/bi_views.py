"""
Business Intelligence Dashboard Views for SalesCompass CRM
"""
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.utils import timezone

from .bi_services import (
    RealTimeProcessor,
    DataAggregationService,     
    MetricsCalculationService,
    TrendAnalysisService,
    AdvancedVisualizationService
)
from django.core.paginator import Paginator

import json
from django.apps import apps
from django.db.models import Sum, Count, Avg
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder



class BIDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Main Business Intelligence Dashboard."""
    template_name = 'dashboard/bi/bi_dashboard.html'
    
    def test_func(self):
        # Allow managers, admins, and superusers
        user = self.request.user
        return user.is_staff or user.is_superuser or getattr(user, 'role', None) in ['manager', 'admin']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = getattr(self.request.user, 'tenant', None)
        
        if tenant:
            aggregation = DataAggregationService(tenant)
            metrics = MetricsCalculationService(tenant)
            trends = TrendAnalysisService(tenant)
            viz = AdvancedVisualizationService(tenant)
            
            # Summary data
            context['leads_summary'] = aggregation.get_leads_summary(30)
            context['opportunities_summary'] = aggregation.get_opportunities_summary(30)
            context['accounts_summary'] = aggregation.get_accounts_summary()
            context['cases_summary'] = aggregation.get_cases_summary(30)
            context['tasks_summary'] = aggregation.get_tasks_summary(self.request.user, 30)
            
            # KPIs
            context['kpis'] = metrics.get_all_kpis(30)
            
            # Charts data
            context['leads_trend'] = trends.get_leads_trend(30, 'day')
            context['revenue_trend'] = trends.get_revenue_trend(90, 'week')
            context['pipeline_funnel'] = trends.get_pipeline_funnel()
            context['conversion_trend'] = trends.get_conversion_trend(90)
            
            # Advanced visualization data
            context['heatmap_data'] = viz.get_heatmap_data(30)
            context['forecast_data'] = viz.get_forecast_data(90)
        else:
            context['error'] = 'No tenant associated with user'
        
        context['refresh_interval'] = 300  # 5 minutes default
        return context




class DataExplorerView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Ad-hoc data exploration interface with AJAX support."""
    template_name = 'dashboard/bi/explorer.html'
    
    # Allowed models mapping
    MODEL_MAPPING = {
        'leads': ('leads', 'Lead'),
        'opportunities': ('opportunities', 'Opportunity'),
        'accounts': ('accounts', 'Account'),
        'cases': ('cases', 'Case'),
        'tasks': ('tasks', 'Task'),
    }

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass metadata for left sidebar
        context['modules'] = [
            {'id': k, 'name': k.capitalize(), 'icon': 'bi-database'} 
            for k in self.MODEL_MAPPING.keys()
        ]
        return context

    def post(self, request, *args, **kwargs):
        """Handle AJAX requests for the Visual Builder."""
        try:
            payload = json.loads(request.body)
            action = payload.get('action')
            module_key = payload.get('module')

            if module_key not in self.MODEL_MAPPING:
                return JsonResponse({'error': 'Invalid module'}, status=400)

            app_label, model_name = self.MODEL_MAPPING[module_key]
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                return JsonResponse({'error': 'Model not found'}, status=404)

            if action == 'get_fields':
                # Return fields for the model
                fields = []
                for f in model._meta.get_fields():
                    if f.is_relation and f.many_to_many: continue
                    fields.append({
                        'name': f.name,
                        'label': f.verbose_name.title() if hasattr(f, 'verbose_name') else f.name.title(),
                        'type': f.get_internal_type()
                    })
                return JsonResponse({'fields': fields})

            elif action == 'execute_query':
                # Build QuerySet
                qs = model.objects.filter(tenant=request.user.tenant)
                
                # Apply Filters
                for f in payload.get('filters', []):
                    field = f['field']
                    val = f['value']
                    op = f['condition']
                    
                    if op == 'equals': qs = qs.filter(**{field: val})
                    elif op == 'contains': qs = qs.filter(**{f"{field}__icontains": val})
                    elif op == 'greater_than': qs = qs.filter(**{f"{field}__gt": val})
                    elif op == 'less_than': qs = qs.filter(**{f"{field}__lt": val})

                # Select Fields
                req_fields = [x['name'] for x in payload.get('fields', [])]
                if 'id' not in req_fields: req_fields.insert(0, 'id')
                
                # Execute
                data = list(qs.values(*req_fields)[:100]) # Hard limit
                return JsonResponse({'results': data}, encoder=DjangoJSONEncoder)

            return JsonResponse({'error': 'Unknown action'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class DrillDownView(LoginRequiredMixin, TemplateView):
    """Handle drill-down with server-side pagination."""
    template_name = 'dashboard/bi/drill_down.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        metric = self.kwargs.get('metric', '')
        page_number = self.request.GET.get('page', 1)
        tenant = getattr(self.request.user, 'tenant', None)
        
        context['metric'] = metric
        
        if tenant:
            queryset, summary = self._get_queryset(metric, tenant)
            
            # Pagination
            paginator = Paginator(queryset, 20) # 20 per page
            page_obj = paginator.get_page(page_number)
            
            context['page_obj'] = page_obj
            context['summary'] = summary
        
        return context
    
    def _get_queryset(self, metric, tenant):
        # ... (Import models inside method to avoid circular imports) ...
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        if metric == 'leads':
            qs = Lead.objects.filter(tenant=tenant).order_by('-lead_created_at')
            summary = {'total': qs.count()}
            return qs.values('id', 'first_name', 'last_name', 'status', 'lead_created_at'), summary
            
        elif metric == 'opportunities':
            qs = Opportunity.objects.filter(tenant=tenant).order_by('-opportunity_created_at')
            total_val = qs.aggregate(sum=Sum('amount'))['sum'] or 0
            summary = {'total': qs.count(), 'value': total_val}
            return qs.values('id', 'name', 'stage', 'amount', 'opportunity_created_at'), summary

        # Default empty
        return [], {}

class MetricsAPIView(LoginRequiredMixin, View):
    """API endpoint for real-time metrics updates."""
    
    def get(self, request):
        tenant = getattr(request.user, 'tenant', None)
        
        if not tenant:
            return JsonResponse({'error': 'No tenant'}, status=400)
        
        processor = RealTimeProcessor(tenant)
        metrics = processor.get_live_metrics()
        
        return JsonResponse(metrics)


class ActivityFeedAPIView(LoginRequiredMixin, View):
    """API endpoint for activity feed."""
    
    def get(self, request):
        tenant = getattr(request.user, 'tenant', None)
        limit = int(request.GET.get('limit', 10))
        
        if not tenant:
            return JsonResponse({'error': 'No tenant'}, status=400)
        
        processor = RealTimeProcessor(tenant)
        activities = processor.get_activity_feed(limit)
        
        return JsonResponse({'activities': activities})


class ChartDataAPIView(LoginRequiredMixin, View):
    """API endpoint for chart data updates."""
    
    def get(self, request, chart_type):
        tenant = getattr(request.user, 'tenant', None)
        days = int(request.GET.get('days', 30))
        
        if not tenant:
            return JsonResponse({'error': 'No tenant'}, status=400)
        
        trends = TrendAnalysisService(tenant)
        viz = AdvancedVisualizationService(tenant)
        
        if chart_type == 'leads':
            data = trends.get_leads_trend(days, 'day')
        elif chart_type == 'revenue':
            data = trends.get_revenue_trend(days, 'week')
        elif chart_type == 'funnel':
            data = trends.get_pipeline_funnel()
        elif chart_type == 'conversion':
            data = trends.get_conversion_trend(days)
        elif chart_type == 'heatmap':
            data = viz.get_heatmap_data(days)
        elif chart_type == 'forecast':
            data = viz.get_forecast_data(days)
        else:
            data = []
        
        return JsonResponse({'data': data})


class ComparativeAnalysisAPIView(LoginRequiredMixin, View):
    """API endpoint for comparative analysis."""
    
    def get(self, request):
        tenant = getattr(request.user, 'tenant', None)
        metric = request.GET.get('metric', 'revenue')
        
        if not tenant:
            return JsonResponse({'error': 'No tenant'}, status=400)
        
        viz = AdvancedVisualizationService(tenant)
        analysis = viz.get_comparative_analysis(metric)
        
        return JsonResponse(analysis)


class StreamingDataAPIView(LoginRequiredMixin, View):
    """API endpoint for streaming real-time data."""
    
    def get(self, request):
        tenant = getattr(request.user, 'tenant', None)
        last_timestamp = request.GET.get('since')
        
        if not tenant:
            return JsonResponse({'error': 'No tenant'}, status=400)
        
        processor = RealTimeProcessor(tenant)
        stream_data = processor.get_streaming_data(last_timestamp)
        
        return JsonResponse(stream_data)


    

class MetricsAPIView(LoginRequiredMixin, View):
    """API endpoint for real-time metrics updates."""
    
    def get(self, request):
        tenant = getattr(request.user, 'tenant', None)
        
        if not tenant:
            return JsonResponse({'error': 'No tenant'}, status=400)
        
        processor = RealTimeProcessor(tenant)
        metrics = processor.get_live_metrics()
        
        return JsonResponse(metrics)
