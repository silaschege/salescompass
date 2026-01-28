from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, TemplateView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum, Count
from django.http import JsonResponse

from tenants.views import TenantAwareViewMixin
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView
)
from .models import (
    Warehouse, StockLocation, StockLevel, StockMovement,
    StockAdjustment, ReorderRule, StockAlert
)
from .forms import (
    WarehouseForm, StockAddForm, StockRemoveForm, StockTransferForm,
    StockAdjustmentForm, ReorderRuleForm,
    TransferCreateForm, TransferLineFormSet
)
from .services import InventoryService, TransferService
from .models import InterStoreTransfer



# Dashboard
class InventoryDashboardView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Inventory dashboard with summary statistics."""
    template_name = 'inventory/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get summary stats
        context['total_warehouses'] = Warehouse.objects.filter(tenant=tenant, is_active=True).count()
        context['total_products_in_stock'] = StockLevel.objects.filter(
            tenant=tenant, quantity__gt=0
        ).values('product').distinct().count()
        context['total_stock_value'] = StockLevel.objects.filter(
            tenant=tenant
        ).aggregate(
            value=Sum('quantity') * Sum('cost_price')
        )['value'] or 0
        
        # Recent movements
        context['recent_movements'] = StockMovement.objects.filter(
            tenant=tenant
        ).select_related('product', 'from_warehouse', 'to_warehouse')[:10]
        
        # Active alerts
        context['active_alerts'] = StockAlert.objects.filter(
            tenant=tenant, status__in=['new', 'acknowledged']
        ).select_related('product', 'warehouse')[:10]
        
        # Low stock count
        context['low_stock_count'] = StockAlert.objects.filter(
            tenant=tenant, 
            alert_type__in=['low_stock', 'out_of_stock'],
            status__in=['new', 'acknowledged']
        ).count()
        
        return context


# Warehouse Views
class WarehouseListView(SalesCompassListView):
    """List all warehouses."""
    model = Warehouse
    template_name = 'inventory/warehouse_list.html'
    context_object_name = 'warehouses'
    
    def get_queryset(self):
        return Warehouse.objects.filter(tenant=self.request.user.tenant)


class WarehouseDetailView(SalesCompassDetailView):
    """Warehouse detail with stock levels."""
    model = Warehouse
    template_name = 'inventory/warehouse_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_levels'] = StockLevel.objects.filter(
            warehouse=self.object
        ).select_related('product', 'location')
        context['recent_movements'] = StockMovement.objects.filter(
            from_warehouse=self.object
        ) | StockMovement.objects.filter(to_warehouse=self.object)
        context['recent_movements'] = context['recent_movements'].order_by('-created_at')[:20]
        return context


class WarehouseCreateView(SalesCompassCreateView):
    """Create a new warehouse."""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse_form.html'
    success_url = reverse_lazy('inventory:warehouse_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, 'Warehouse created successfully.')
        return super().form_valid(form)


class WarehouseUpdateView(SalesCompassUpdateView):
    """Update an existing warehouse."""
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse_form.html'
    success_url = reverse_lazy('inventory:warehouse_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Warehouse updated successfully.')
        return super().form_valid(form)


# Stock Level Views
class StockLevelListView(SalesCompassListView):
    """List all stock levels."""
    model = StockLevel
    template_name = 'inventory/stock_list.html'
    context_object_name = 'stock_levels'
    
    def get_queryset(self):
        qs = StockLevel.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('product', 'warehouse', 'location')
        
        # Filter by warehouse
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        
        # Filter by low stock
        if self.request.GET.get('low_stock'):
            qs = qs.filter(quantity__lte=10)  # Simple threshold for now
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(
            tenant=self.request.user.tenant, is_active=True
        )
        return context


class StockLevelDetailView(SalesCompassDetailView):
    """Stock level detail with movement history."""
    model = StockLevel
    template_name = 'inventory/stock_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movements'] = StockMovement.objects.filter(
            product=self.object.product,
            tenant=self.request.user.tenant
        ).order_by('-created_at')[:50]
        return context


# Stock Movement Views
class StockMovementListView(SalesCompassListView):
    """List all stock movements."""
    model = StockMovement
    template_name = 'inventory/movement_list.html'
    context_object_name = 'movements'
    
    def get_queryset(self):
        return StockMovement.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('product', 'from_warehouse', 'to_warehouse', 'performed_by')


class StockAddView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """View for adding stock."""
    template_name = 'inventory/stock_add.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = StockAddForm(tenant=self.request.user.tenant)
        return context
    
    def post(self, request, *args, **kwargs):
        form = StockAddForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            try:
                InventoryService.add_stock(
                    product=form.cleaned_data['product'],
                    warehouse=form.cleaned_data['warehouse'],
                    quantity=form.cleaned_data['quantity'],
                    user=request.user,
                    location=form.cleaned_data.get('location'),
                    unit_cost=form.cleaned_data.get('unit_cost'),
                    notes=form.cleaned_data.get('notes', ''),
                    tenant=request.user.tenant
                )
                messages.success(request, 'Stock added successfully.')
                return redirect('inventory:stock_list')
            except Exception as e:
                messages.error(request, str(e))
        
        return self.render_to_response({'form': form})


class StockRemoveView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """View for removing stock."""
    template_name = 'inventory/stock_remove.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = StockRemoveForm(tenant=self.request.user.tenant)
        return context
    
    def post(self, request, *args, **kwargs):
        form = StockRemoveForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            try:
                InventoryService.remove_stock(
                    product=form.cleaned_data['product'],
                    warehouse=form.cleaned_data['warehouse'],
                    quantity=form.cleaned_data['quantity'],
                    user=request.user,
                    location=form.cleaned_data.get('location'),
                    notes=form.cleaned_data.get('notes', ''),
                    movement_type=form.cleaned_data['reason'],
                    tenant=request.user.tenant
                )
                messages.success(request, 'Stock removed successfully.')
                return redirect('inventory:stock_list')
            except ValueError as e:
                messages.error(request, str(e))
        
        return self.render_to_response({'form': form})


class StockTransferView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """View for transferring stock between warehouses."""
    template_name = 'inventory/stock_transfer.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = StockTransferForm(tenant=self.request.user.tenant)
        return context
    
    def post(self, request, *args, **kwargs):
        form = StockTransferForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            try:
                InventoryService.transfer_stock(
                    product=form.cleaned_data['product'],
                    from_warehouse=form.cleaned_data['from_warehouse'],
                    to_warehouse=form.cleaned_data['to_warehouse'],
                    quantity=form.cleaned_data['quantity'],
                    user=request.user,
                    from_location=form.cleaned_data.get('from_location'),
                    to_location=form.cleaned_data.get('to_location'),
                    notes=form.cleaned_data.get('notes', ''),
                    tenant=request.user.tenant
                )
                messages.success(request, 'Stock transferred successfully.')
                return redirect('inventory:stock_list')
            except ValueError as e:
                messages.error(request, str(e))
        
        return self.render_to_response({'form': form})


# Stock Adjustment Views
class StockAdjustmentListView(SalesCompassListView):
    """List all stock adjustments."""
    model = StockAdjustment
    template_name = 'inventory/adjustment_list.html'
    context_object_name = 'adjustments'
    
    def get_queryset(self):
        return StockAdjustment.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('warehouse', 'created_by')


class StockAdjustmentDetailView(SalesCompassDetailView):
    """Stock adjustment detail."""
    model = StockAdjustment
    template_name = 'inventory/adjustment_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.select_related('product', 'location')
        return context


class StockAdjustmentCreateView(SalesCompassCreateView):
    """Create a new stock adjustment."""
    model = StockAdjustment
    form_class = StockAdjustmentForm
    template_name = 'inventory/adjustment_form.html'
    success_url = reverse_lazy('inventory:adjustment_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.created_by = self.request.user
        # Generate adjustment number
        import uuid
        form.instance.adjustment_number = f"ADJ-{uuid.uuid4().hex[:8].upper()}"
        messages.success(self.request, 'Adjustment created successfully.')
        return super().form_valid(form)


# Stock Alert Views
class StockAlertListView(SalesCompassListView):
    """List all stock alerts."""
    model = StockAlert
    template_name = 'inventory/alert_list.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        qs = StockAlert.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('product', 'warehouse')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        else:
            qs = qs.filter(status__in=['new', 'acknowledged'])
        
        return qs


class AcknowledgeAlertView(LoginRequiredMixin, View):
    """Acknowledge a stock alert."""
    
    def post(self, request, pk):
        alert = get_object_or_404(
            StockAlert, pk=pk, tenant=request.user.tenant
        )
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        from django.utils import timezone
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Alert acknowledged.')
        return redirect('inventory:alert_list')


# Reorder Rule Views
class ReorderRuleListView(SalesCompassListView):
    """List all reorder rules."""
    model = ReorderRule
    template_name = 'inventory/reorder_list.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        return ReorderRule.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('product', 'warehouse')


class ReorderRuleCreateView(SalesCompassCreateView):
    """Create a new reorder rule."""
    model = ReorderRule
    form_class = ReorderRuleForm
    template_name = 'inventory/reorder_form.html'
    success_url = reverse_lazy('inventory:reorder_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, 'Reorder rule created successfully.')
        return super().form_valid(form)


class ReorderRuleUpdateView(SalesCompassUpdateView):
    """Update an existing reorder rule."""
    model = ReorderRule
    form_class = ReorderRuleForm
    template_name = 'inventory/reorder_form.html'
    success_url = reverse_lazy('inventory:reorder_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Reorder rule updated successfully.')
        return super().form_valid(form)


# Transfer Views
class TransferListView(SalesCompassListView):
    """List all transfers."""
    model = InterStoreTransfer
    template_name = 'inventory/transfer_list.html'
    context_object_name = 'transfers'
    
    def get_queryset(self):
        qs = InterStoreTransfer.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('source_warehouse', 'destination_warehouse', 'requested_by')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class TransferCreateView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Create a new transfer with lines."""
    template_name = 'inventory/transfer_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = TransferCreateForm(tenant=self.request.user.tenant)
        if 'formset' not in context:
            context['formset'] = TransferLineFormSet(form_kwargs={'tenant': self.request.user.tenant})
        return context
    
    def post(self, request, *args, **kwargs):
        form = TransferCreateForm(data=request.POST, tenant=request.user.tenant)
        formset = TransferLineFormSet(data=request.POST, form_kwargs={'tenant': request.user.tenant})
        
        if form.is_valid() and formset.is_valid():
            try:
                lines = []
                for line_form in formset:
                    if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE', False):
                        product = line_form.cleaned_data['product']
                        quantity = line_form.cleaned_data['quantity']
                        if quantity > 0:
                            lines.append({'product': product, 'quantity': quantity})
                
                if not lines:
                    messages.error(request, "At least one product line is required.")
                    return self.render_to_response({'form': form, 'formset': formset})

                transfer = TransferService.create_transfer(
                    source=form.cleaned_data['source_warehouse'],
                    destination=form.cleaned_data['destination_warehouse'],
                    lines=lines,
                    user=request.user,
                    notes=form.cleaned_data['notes'],
                    tenant=request.user.tenant
                )
                messages.success(request, f'Transfer {transfer.transfer_number} created successfully.')
                return redirect('inventory:transfer_detail', pk=transfer.pk)
            except Exception as e:
                messages.error(request, str(e))
        
        return self.render_to_response({'form': form, 'formset': formset})


class TransferDetailView(SalesCompassDetailView):
    """Transfer detail view."""
    model = InterStoreTransfer
    template_name = 'inventory/transfer_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.select_related('product')
        return context


class TransferShipView(LoginRequiredMixin, View):
    """Ship a transfer."""
    def post(self, request, pk):
        transfer = get_object_or_404(InterStoreTransfer, pk=pk, tenant=request.user.tenant)
        try:
            TransferService.ship_transfer(transfer, request.user)
            messages.success(request, f'Transfer {transfer.transfer_number} shipped.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('inventory:transfer_detail', pk=pk)


class TransferReceiveView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Receive a transfer."""
    template_name = 'inventory/transfer_receive.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transfer = get_object_or_404(InterStoreTransfer, pk=kwargs['pk'], tenant=self.request.user.tenant)
        context['transfer'] = transfer
        context['lines'] = transfer.lines.select_related('product')
        return context
        
    def post(self, request, pk):
        transfer = get_object_or_404(InterStoreTransfer, pk=pk, tenant=request.user.tenant)
        received_data = {}
        
        for key, value in request.POST.items():
            if key.startswith('received_'):
                line_id = key.split('_')[1]
                received_data[line_id] = value
                
        try:
            TransferService.receive_transfer(transfer, received_data, request.user)
            messages.success(request, f'Transfer {transfer.transfer_number} received.')
            return redirect('inventory:transfer_detail', pk=pk)
        except Exception as e:
            messages.error(request, str(e))
            return self.get(request, pk=pk)

