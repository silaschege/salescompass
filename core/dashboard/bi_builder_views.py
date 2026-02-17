from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.apps import apps
from django.db.models import Count, Sum, Avg, Min, Max, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import datetime

from .models import DashboardConfig, DashboardWidget, WidgetType, WidgetCategory
from .model_introspection import get_available_models, get_model_fields, get_model_class

class BIDashboardBuilderView(LoginRequiredMixin, TemplateView):
    """
    Single-page BI Dashboard Builder.
    Allows users to drag-and-drop widgets, configure data sources from ANY model,
    and visualize data immediately.
    """
    template_name = 'dashboard/bi_builder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Load all available system models
        context['available_models'] = get_available_models()
        
        # Load visualization types (hardcoded for now, could be dynamic)
        context['widget_types'] = [
            {'type': 'line', 'label': 'Line Chart', 'icon': 'bi-graph-up'},
            {'type': 'bar', 'label': 'Bar Chart', 'icon': 'bi-bar-chart-fill'},
            {'type': 'pie', 'label': 'Pie Chart', 'icon': 'bi-pie-chart-fill'},
            {'type': 'doughnut', 'label': 'Doughnut Chart', 'icon': 'bi-circle'},
            {'type': 'number', 'label': 'Big Number', 'icon': 'bi-123'},
            {'type': 'table', 'label': 'Data Table', 'icon': 'bi-table'},
        ]
        
        # Load aggregation functions
        context['aggregations'] = [
            {'value': 'count', 'label': 'Count'},
            {'value': 'sum', 'label': 'Sum'},
            {'value': 'avg', 'label': 'Average'},
            {'value': 'min', 'label': 'Minimum'},
            {'value': 'max', 'label': 'Maximum'},
        ]
        
        return context


class DashboardSaveAPIView(LoginRequiredMixin, View):
    """
    API to save the complete dashboard configuration.
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            dashboard = DashboardConfig.objects.create(
                user=request.user,
                tenant=request.user.tenant,
                dashboard_name=data.get('name', 'New Dashboard'),
                dashboard_description=data.get('description', ''),
                layout=data.get('layout', {}),
                widgets=data.get('widgets', []),
                is_default=data.get('is_default', False)
            )
            
            return JsonResponse({'success': True, 'id': dashboard.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


class DashboardPreviewAPIView(LoginRequiredMixin, View):
    """
    Live Data Preview API.
    Accepts widget configuration and returns calculated chart data in real-time.
    """
    def post(self, request):
        try:
            config = json.loads(request.body)
            model_id = config.get('model')
            chart_type = config.get('type', 'bar')
            
            # 1. Resolve Model
            ModelClass = get_model_class(model_id)
            if not ModelClass:
                return JsonResponse({'error': 'Invalid Model'}, status=400)
            
            # 2. Base Queryset (Tenant Scoped if possible)
            qs = ModelClass.objects.all()
            if hasattr(ModelClass, 'tenant_id'):
                 qs = qs.filter(tenant_id=request.user.tenant_id)
            elif hasattr(ModelClass, 'tenant'):
                 qs = qs.filter(tenant=request.user.tenant)
                 
            # 3. Apply Filters
            filters = config.get('filters', [])
            for f in filters:
                field = f.get('field')
                operator = f.get('operator', 'exact')
                value = f.get('value')
                if field and value is not None:
                    lookup = f"{field}__{operator}"
                    qs = qs.filter(**{lookup: value})
            
            # 4. Aggregation / Grouping Logic
            group_by = config.get('group_by')  # Field to group by (X-Axis)
            agg_func = config.get('aggregation', 'count') # sum, avg, count
            agg_field = config.get('agg_field') # Field to aggregate (Y-Axis)
            
            data = {}
            
            if chart_type == 'number':
                # Single value aggregation
                if agg_func == 'count':
                    value = qs.count()
                else:
                    agg_metric = {
                        'sum': Sum, 'avg': Avg, 'min': Min, 'max': Max
                    }.get(agg_func, Count)
                    result = qs.aggregate(val=agg_metric(agg_field))
                    value = result.get('val', 0)
                
                data = {'value': value, 'label': f"{agg_func.title()} of {agg_field or 'Records'}"}
                
            else:
                # Chart aggregation (Group By)
                if not group_by:
                    return JsonResponse({'error': 'Group By field required for charts'}, status=400)
                
                # Handle Date Grouping
                # Check field type (simplified)
                is_date = 'date' in group_by or 'created' in group_by # simple heuristic or check introspection
                
                # Determine metric
                if agg_func == 'count':
                    metric = Count('id')
                else:
                    agg_class = {'sum': Sum, 'avg': Avg, 'min': Min, 'max': Max}.get(agg_func, Count)
                    metric = agg_class(agg_field)
                
                # Construct Query
                if is_date:
                    # Default to day truncation for date fields
                    qs = qs.annotate(date_group=TruncDate(group_by)).values('date_group')
                    qs = qs.annotate(value=metric).order_by('date_group')
                    
                    labels = [item['date_group'].strftime('%Y-%m-%d') if item['date_group'] else 'None' for item in qs]
                    values = [item['value'] for item in qs]
                else:
                    # Categorical grouping
                    qs = qs.values(group_by).annotate(value=metric).order_by('-value')[:20] # Limit to top 20
                    
                    labels = [str(item[group_by]) for item in qs]
                    values = [item['value'] for item in qs]
                
                data = {
                    'labels': labels,
                    'datasets': [{
                        'label': f"{agg_func.title()} of {agg_field or 'Records'}",
                        'data': values,
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                        'borderColor': 'rgba(54, 162, 235, 1)',
                        'borderWidth': 1
                    }]
                }

            return JsonResponse({'success': True, 'data': data})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
