from django.views.generic import TemplateView, ListView, CreateView
from django.urls import reverse_lazy
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView,
    TenantAwareViewMixin
)
from .models import InspectionRule, InspectionLog, NonConformanceReport

class QualityDashboardView(TenantAwareViewMixin, TemplateView):
    template_name = 'quality_control/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        context['pending_inspections'] = InspectionLog.objects.filter(tenant=tenant, status='pending').count()
        context['passed_rate'] = 0 # Calculate based on logs
        context['active_ncrs'] = NonConformanceReport.objects.filter(tenant=tenant, resolved_at__isnull=True).count()
        
        context['recent_logs'] = InspectionLog.objects.filter(tenant=tenant).order_by('-created_at')[:10]
        return context

class InspectionRuleListView(SalesCompassListView):
    model = InspectionRule
    template_name = 'quality_control/rule_list.html'
    context_object_name = 'rules'

class InspectionLogListView(SalesCompassListView):
    model = InspectionLog
    template_name = 'quality_control/log_list.html'
    context_object_name = 'logs'

class InspectionLogCreateView(SalesCompassCreateView):
    model = InspectionLog
    fields = ['rule', 'source_reference', 'status', 'results_data', 'comments']
    template_name = 'quality_control/log_form.html'
    success_url = reverse_lazy('quality_control:log_list')

class NCRListView(SalesCompassListView):
    model = NonConformanceReport
    template_name = 'quality_control/ncr_list.html'
    context_object_name = 'ncrs'
