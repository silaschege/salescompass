from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView,
    TenantAwareViewMixin
)
from .models import InspectionRule, InspectionLog, NonConformanceReport, InspectionAttachment, CAPA, QualityCheckLibrary
from .forms import InspectionRuleForm, InspectionLogForm, NCRManagementForm, CAPAForm, QualityCheckLibraryForm

class QualityDashboardView(TenantAwareViewMixin, TemplateView):
    template_name = 'quality_control/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        logs = InspectionLog.objects.filter(tenant=tenant)
        total_logs = logs.count()
        passed_logs = logs.filter(status='pass').count()
        
        context['pending_inspections'] = logs.filter(status='pending').count()
        context['passed_rate'] = (passed_logs / total_logs * 100) if total_logs > 0 else 0
        context['active_ncrs'] = NonConformanceReport.objects.filter(tenant=tenant, resolved_at__isnull=True).count()
        
        # Quality Metrics
        context['total_inspections'] = total_logs
        context['fpy'] = context['passed_rate'] # First-Pass Yield
        context['defect_rate'] = (logs.filter(status='fail').count() / total_logs * 100) if total_logs > 0 else 0
        
        context['recent_logs'] = logs.order_by('-created_at')[:10]
        context['rules'] = InspectionRule.objects.filter(tenant=tenant)
        return context

class ControlChartDataAPI(TenantAwareViewMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        rule_id = request.GET.get('rule_id')
        if not rule_id:
            return JsonResponse({'error': 'rule_id is required'}, status=400)
        
        tenant = request.user.tenant
        logs = InspectionLog.objects.filter(tenant=tenant, rule_id=rule_id, status__in=['pass', 'fail']).order_by('created_at')
        
        data_points = []
        for log in logs:
            # Try to find a numerical value in results_data
            # For simplicity, we assume the first numerical value found is what we plot
            if log.results_data:
                for key, val in log.results_data.items():
                    if isinstance(val, (int, float)):
                        data_points.append({
                            'date': log.created_at.strftime('%Y-%m-%d %H:%M'),
                            'value': val
                        })
                        break
        
        if not data_points:
            return JsonResponse({'data': [], 'stats': {}})

        values = [p['value'] for p in data_points]
        import statistics
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        return JsonResponse({
            'data': data_points,
            'stats': {
                'mean': mean,
                'ucl': mean + (3 * stdev), # Upper Control Limit
                'lcl': mean - (3 * stdev), # Lower Control Limit
            }
        })

class InspectionRuleListView(SalesCompassListView):
    model = InspectionRule
    template_name = 'quality_control/rule_list.html'
    context_object_name = 'rules'

class InspectionRuleCreateView(SalesCompassCreateView):
    model = InspectionRule
    form_class = InspectionRuleForm
    template_name = 'quality_control/rule_form.html'
    success_url = reverse_lazy('quality_control:rule_list')

class InspectionRuleUpdateView(SalesCompassUpdateView):
    model = InspectionRule
    form_class = InspectionRuleForm
    template_name = 'quality_control/rule_form.html'
    success_url = reverse_lazy('quality_control:rule_list')

class InspectionLogListView(SalesCompassListView):
    model = InspectionLog
    template_name = 'quality_control/log_list.html'
    context_object_name = 'logs'

class InspectionLogCreateView(SalesCompassCreateView):
    model = InspectionLog
    form_class = InspectionLogForm
    template_name = 'quality_control/log_form.html'
    success_url = reverse_lazy('quality_control:log_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle attachments
        if self.request.FILES:
            for key, file in self.request.FILES.items():
                if key.startswith('attachment_'):
                    # key format expected: attachment_{item_id} OR just attachment for general?
                    # Let's assume the JS sends keys like 'attachment_123' where 123 is the item ID
                    item_id = key.split('_')[1] if '_' in key else ''
                    InspectionAttachment.objects.create(
                        tenant=self.object.tenant,
                        inspection_log=self.object,
                        file=file,
                        item_id=item_id,
                        caption=file.name
                    )
        return response

class NCRListView(SalesCompassListView):
    model = NonConformanceReport
    template_name = 'quality_control/ncr_list.html'
    context_object_name = 'ncrs'

class NCRUpdateView(SalesCompassUpdateView):
    model = NonConformanceReport
    form_class = NCRManagementForm
    template_name = 'quality_control/ncr_form.html'
    success_url = reverse_lazy('quality_control:ncr_list')

@login_required
def rule_detail_api(request, pk):
    rule = get_object_or_404(InspectionRule, pk=pk, tenant=request.user.tenant)
    return JsonResponse({
        'id': rule.pk,
        'name': rule.name,
        'check_list': rule.check_list,
        'sampling_type': rule.sampling_type,
        'aql_level': rule.aql_level,
        'inspection_level': rule.inspection_level
    })

@login_required
def calculate_sample_api(request):
    from .sampling import get_sample_size
    lot_size = int(request.GET.get('lot_size', 0))
    aql = float(request.GET.get('aql', 1.0))
    level = request.GET.get('level', 'II')
    
    size, ac, re = get_sample_size(lot_size, level, aql)
    return JsonResponse({
        'sample_size': size,
        'acceptance_number': ac,
        'rejection_number': re
    })

class CAPAListView(SalesCompassListView):
    model = CAPA
    template_name = 'quality_control/capa_list.html'
    context_object_name = 'capas'

class CAPACreateView(SalesCompassCreateView):
    model = CAPA
    form_class = CAPAForm
    template_name = 'quality_control/capa_form.html'
    success_url = reverse_lazy('quality_control:capa_list')

class CAPAUpdateView(SalesCompassUpdateView):
    model = CAPA
    form_class = CAPAForm
    template_name = 'quality_control/capa_form.html'
    success_url = reverse_lazy('quality_control:capa_list')

class QualityCheckLibraryListView(SalesCompassListView):
    model = QualityCheckLibrary
    template_name = 'quality_control/library_list.html'
    context_object_name = 'items'

class QualityCheckLibraryCreateView(SalesCompassCreateView):
    model = QualityCheckLibrary
    form_class = QualityCheckLibraryForm
    template_name = 'quality_control/library_form.html'
    success_url = reverse_lazy('quality_control:library_list')

class QualityCheckLibraryUpdateView(SalesCompassUpdateView):
    model = QualityCheckLibrary
    form_class = QualityCheckLibraryForm
    template_name = 'quality_control/library_form.html'
    success_url = reverse_lazy('quality_control:library_list')

@login_required
def library_list_api(request):
    tenant = request.user.tenant
    items = QualityCheckLibrary.objects.filter(tenant=tenant, is_active=True)
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'label': item.label,
            'type': item.check_type,
            'category': item.category,
            'description': item.description,
        })
    return JsonResponse({'items': data})

