from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Count
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView,
    TenantAwareViewMixin
)
from .models import Carrier, Shipment

class LogisticsDashboardView(TenantAwareViewMixin, TemplateView):
    template_name = 'logistics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        context['pending_shipments'] = Shipment.objects.filter(tenant=tenant, status='pending').count()
        context['in_transit_shipments'] = Shipment.objects.filter(tenant=tenant, status='in_transit').count()
        context['total_carriers'] = Carrier.objects.filter(tenant=tenant, is_active=True).count()
        
        context['recent_shipments'] = Shipment.objects.filter(tenant=tenant).order_by('-created_at')[:10]
        return context

class ShipmentListView(SalesCompassListView):
    model = Shipment
    template_name = 'logistics/shipment_list.html'
    context_object_name = 'shipments'

class ShipmentDetailView(SalesCompassDetailView):
    model = Shipment
    template_name = 'logistics/shipment_detail.html'
    context_object_name = 'shipment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['updates'] = self.object.updates.all().order_by('-timestamp')
        return context

class CarrierListView(SalesCompassListView):
    model = Carrier
    template_name = 'logistics/carrier_list.html'
    context_object_name = 'carriers'
