from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from django.contrib import messages
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView,
    TenantAwareViewMixin
)
from .models import ProductionLine, BillOfMaterials, WorkOrder

class ManufacturingDashboardView(TenantAwareViewMixin, TemplateView):
    template_name = 'manufacturing/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        context['pending_orders'] = WorkOrder.objects.filter(tenant=tenant, status='confirmed').count()
        context['in_progress_orders'] = WorkOrder.objects.filter(tenant=tenant, status='in_progress').count()
        context['total_production_lines'] = ProductionLine.objects.filter(tenant=tenant, is_active=True).count()
        
        # Recent Work Orders
        context['recent_work_orders'] = WorkOrder.objects.filter(tenant=tenant).order_by('-created_at')[:10]
        
        return context

class ProductionFloorView(TenantAwareViewMixin, TemplateView):
    """
    Real-time view of all production lines and active work orders.
    """
    template_name = 'manufacturing/production_floor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .services import ManufacturingService
        context['floor_status'] = ManufacturingService.get_floor_status(self.request.user.tenant)
        return context

class BOMListView(SalesCompassListView):
    model = BillOfMaterials
    template_name = 'manufacturing/bom_list.html'
    context_object_name = 'boms'

class BOMDetailView(SalesCompassDetailView):
    model = BillOfMaterials
    template_name = 'manufacturing/bom_detail.html'
    context_object_name = 'bom'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all().select_related('component')
        return context

class WorkOrderListView(SalesCompassListView):
    model = WorkOrder
    template_name = 'manufacturing/work_order_list.html'
    context_object_name = 'work_orders'

class WorkOrderCreateView(SalesCompassCreateView):
    model = WorkOrder
    fields = ['product', 'bom', 'quantity', 'production_line', 'planned_start_date', 'planned_end_date']
    template_name = 'manufacturing/work_order_form.html'
    success_url = reverse_lazy('manufacturing:work_order_list')
    success_message = "Work Order created successfully."

class WorkOrderDetailView(SalesCompassDetailView):
    model = WorkOrder
    template_name = 'manufacturing/work_order_detail.html'
    context_object_name = 'order'
