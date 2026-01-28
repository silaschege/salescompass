from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from core.views import SalesCompassListView, SalesCompassCreateView, SalesCompassUpdateView, SalesCompassDetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import PurchaseOrder, SupplierInvoice, GoodsReceipt, GoodsReceiptLine, SupplierPayment
from .forms import PurchaseOrderForm, SupplierInvoiceForm
from inventory.models import StockLevel, StockMovement, Warehouse

class PurchasingDashboardView(TemplateView):
    template_name = 'purchasing/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Procurement KPIs
        context['open_po_count'] = PurchaseOrder.objects.filter(tenant=tenant, status__in=['draft', 'sent', 'partial']).count()
        context['unbilled_grn_count'] = GoodsReceipt.objects.filter(tenant=tenant, purchase_order__status='received').count() # Simplified
        
        # Spend (MTD)
        from django.db.models import Sum
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        context['monthly_spend'] = SupplierInvoice.objects.filter(
            tenant=tenant, invoice_date__gte=month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        return context

# --- Purchase Orders ---

class PurchaseOrderListView(SalesCompassListView):
    model = PurchaseOrder
    template_name = 'purchasing/po_list.html'
    context_object_name = 'orders'

class PurchaseOrderCreateView(SalesCompassCreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchasing/po_form.html'
    success_url = reverse_lazy('purchasing:po_list')
    success_message = "Purchase Order created successfully."

class PurchaseOrderUpdateView(SalesCompassUpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchasing/po_form.html'
    success_url = reverse_lazy('purchasing:po_list')
    success_message = "Purchase Order updated successfully."

class PurchaseOrderDetailView(SalesCompassDetailView):
    model = PurchaseOrder
    template_name = 'purchasing/po_detail.html'
    context_object_name = 'order'
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve' and order.status == 'draft':
            from .services import ProcurementService
            try:
                ProcurementService.approve_purchase_order(order, request.user)
                messages.success(request, f"Purchase Order {order.po_number} has been approved.")
            except Exception as e:
                messages.error(request, f"Error approving order: {str(e)}")
                
        return redirect('purchasing:po_detail', pk=order.pk)

class PurchaseOrderReceiveView(SalesCompassDetailView):
    model = PurchaseOrder
    template_name = 'purchasing/po_receive.html'
    context_object_name = 'order'

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        
        if order.status in ['received', 'closed', 'cancelled']:
            messages.warning(request, "This order has already been processed.")
            return redirect('purchasing:po_detail', pk=order.pk)

        try:
            from .services import ProcurementService
            receipt_data = []
            for line in order.lines.all():
                qty = line.quantity_ordered - line.quantity_received
                if qty > 0:
                    receipt_data.append({'po_line_id': line.id, 'qty': qty})

            if not receipt_data:
                messages.info(request, "No items to receive.")
                return redirect('purchasing:po_detail', pk=order.pk)

            ProcurementService.process_goods_receipt(order, receipt_data, request.user)
            messages.success(request, f"Goods received for PO {order.po_number}. Inventory and Ledger updated.")
            
        except Exception as e:
            messages.error(request, f"Error processing receipt: {str(e)}")
            
        return redirect('purchasing:po_detail', pk=order.pk)

# --- Supplier Invoices ---

class SupplierInvoiceListView(SalesCompassListView):
    model = SupplierInvoice
    template_name = 'purchasing/invoice_list.html'
    context_object_name = 'invoices'

class SupplierInvoiceCreateView(SalesCompassCreateView):
    model = SupplierInvoice
    form_class = SupplierInvoiceForm
    template_name = 'purchasing/invoice_form.html'
    success_url = reverse_lazy('purchasing:invoice_list')
    success_message = "Supplier Invoice created successfully."

class SupplierInvoiceDetailView(SalesCompassDetailView):
    model = SupplierInvoice
    template_name = 'purchasing/invoice_detail.html'
    context_object_name = 'invoice'
    
    def post(self, request, *args, **kwargs):
        invoice = self.get_object()
        action = request.POST.get('action')
        
        if action == 'post' and invoice.status == 'draft':
            from .services import ProcurementService
            try:
                ProcurementService.post_supplier_invoice(invoice, request.user)
                messages.success(request, f"Invoice {invoice.invoice_number} has been posted to ledger.")
            except Exception as e:
                messages.error(request, f"Error posting invoice: {str(e)}")
                
        return redirect('purchasing:invoice_detail', pk=invoice.pk)


# --- Supplier Payments ---

class SupplierPaymentListView(SalesCompassListView):
    model = SupplierPayment
    template_name = 'purchasing/supplier_payment_list.html'
    context_object_name = 'payments'

class SupplierPaymentCreateView(SalesCompassCreateView):
    model = SupplierPayment
    fields = ['supplier', 'payment_date', 'amount', 'method', 'reference', 'invoices']
    template_name = 'purchasing/supplier_payment_form.html'
    success_url = reverse_lazy('purchasing:payment_list')
    success_message = "Supplier Payment recorded successfully."
    
    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            from .services import ProcurementService
            ProcurementService.process_supplier_payment(self.object, self.request.user)
            return response

# --- GRNs ---

class GRNListView(SalesCompassListView):
    model = GoodsReceipt
    template_name = 'purchasing/grn_list.html'
    context_object_name = 'receipts'

