from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from core.views import SalesCompassListView, SalesCompassCreateView, SalesCompassUpdateView, SalesCompassDetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import PurchaseOrder, SupplierInvoice, GoodsReceipt, GoodsReceiptLine, SupplierPayment, PurchaseOrderLine, PurchaseRequisition, PurchaseRequisitionLine
from .forms import PurchaseOrderForm, SupplierInvoiceForm, PurchaseOrderLineFormSet, PurchaseRequisitionForm, PurchaseRequisitionLineFormSet, SupplierPaymentForm
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = PurchaseOrderLineFormSet(self.request.POST, form_kwargs={'tenant': self.request.user.tenant})
        else:
            context['lines'] = PurchaseOrderLineFormSet(form_kwargs={'tenant': self.request.user.tenant})
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            with transaction.atomic():
                form.instance.tenant = self.request.user.tenant
                form.instance.requested_by = self.request.user
                self.object = form.save()
                
                # Assign tenant to lines before saving
                lines.instance = self.object
                po_lines = lines.save(commit=False)
                for line in po_lines:
                    line.tenant = self.request.user.tenant
                    line.save()
                lines.save_m2m()
                
                # Calculate and update total amount (includes per-line tax)
                self.object.recalculate_totals()
                
            messages.success(self.request, self.success_message)
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

class PurchaseOrderUpdateView(SalesCompassUpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchasing/po_form.html'
    success_url = reverse_lazy('purchasing:po_list')
    success_message = "Purchase Order updated successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = PurchaseOrderLineFormSet(self.request.POST, instance=self.object, form_kwargs={'tenant': self.request.user.tenant})
        else:
            context['lines'] = PurchaseOrderLineFormSet(instance=self.object, form_kwargs={'tenant': self.request.user.tenant})
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            with transaction.atomic():
                self.object = form.save()
                
                # Assign tenant to lines before saving
                lines.instance = self.object
                po_lines = lines.save(commit=False)
                for line in po_lines:
                    line.tenant = self.request.user.tenant
                    line.save()
                lines.save_m2m()
                
                # Calculate and update total amount (includes per-line tax)
                self.object.recalculate_totals()
                
            messages.success(self.request, self.success_message)
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

class PurchaseOrderDetailView(SalesCompassDetailView):
    model = PurchaseOrder
    template_name = 'purchasing/po_detail.html'
    context_object_name = 'order'
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve' and order.status in ['draft', 'pending_approval']:
            from .services import ProcurementService
            try:
                ProcurementService.approve_purchase_order(order, request.user)
                messages.success(request, f"Purchase Order {order.po_number} has been approved/processed.")
            except Exception as e:
                messages.error(request, f"Error approving order: {str(e)}")
        
        elif action == 'reject' and order.status in ['draft', 'pending_approval']:
            from .services import ProcurementService
            try:
                ProcurementService.approve_purchase_order(order, request.user, rejection_reason=request.POST.get('rejection_reason'))
                messages.warning(request, f"Purchase Order {order.po_number} has been rejected.")
            except Exception as e:
                messages.error(request, f"Error rejecting order: {str(e)}")
                
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .services import ProcurementService
        is_match, message = ProcurementService.check_three_way_match(self.object)
        context['match_status'] = {
            'is_match': is_match,
            'message': message
        }
        # Payment status
        amount_paid = sum(p.amount for p in self.object.payments.all())
        context['amount_paid'] = amount_paid
        context['outstanding'] = self.object.total_amount - amount_paid
        return context

    def post(self, request, *args, **kwargs):
        invoice = self.get_object()
        action = request.POST.get('action')
        
        if action == 'post' and invoice.status == 'draft':
            from .services import ProcurementService
            force = request.POST.get('force') == 'true'
            try:
                ProcurementService.post_supplier_invoice(invoice, request.user, force=force)
                messages.success(request, f"Invoice {invoice.invoice_number} has been posted to ledger.")
            except Exception as e:
                messages.error(request, f"Error posting invoice: {str(e)}")
                
        return redirect('purchasing:invoice_detail', pk=invoice.pk)


# --- GRNs ---

class GRNListView(SalesCompassListView):
    model = GoodsReceipt
    template_name = 'purchasing/grn_list.html'
    context_object_name = 'receipts'


class GRNDetailView(SalesCompassDetailView):
    model = GoodsReceipt
    template_name = 'purchasing/grn_detail.html'
    context_object_name = 'receipt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grn = self.object
        # Calculate total receipt value
        from decimal import Decimal
        total_value = Decimal('0')
        for line in grn.lines.select_related('po_line', 'po_line__product').all():
            total_value += line.quantity_received * line.po_line.unit_cost
        context['total_value'] = total_value
        return context

    def post(self, request, *args, **kwargs):
        grn = self.get_object()
        action = request.POST.get('action')

        if action == 'confirm' and grn.status == 'draft':
            from .services import ProcurementService
            try:
                ProcurementService.confirm_goods_receipt(grn, request.user)
                messages.success(request, f"GRN {grn.grn_number} confirmed. Journal entry posted to ledger.")
            except Exception as e:
                messages.error(request, f"Error confirming GRN: {str(e)}")

        return redirect('purchasing:grn_detail', pk=grn.pk)


# --- Supplier Payments ---

class SupplierPaymentListView(SalesCompassListView):
    model = SupplierPayment
    template_name = 'purchasing/supplier_payment_list.html'
    context_object_name = 'payments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        unsettled = SupplierInvoice.objects.filter(
            tenant=tenant, status__in=['posted', 'overdue']
        ).select_related('supplier', 'purchase_order')
        context['unsettled_invoices'] = unsettled
        return context

class SupplierPaymentCreateView(SalesCompassCreateView):
    model = SupplierPayment
    form_class = SupplierPaymentForm
    template_name = 'purchasing/supplier_payment_form.html'
    success_url = reverse_lazy('purchasing:payment_list')
    success_message = "Supplier Payment recorded successfully."
    
    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            from .services import ProcurementService
            ProcurementService.process_supplier_payment(self.object, self.request.user)
            return response

# --- Purchase Requisitions ---

class PurchaseRequisitionListView(SalesCompassListView):
    model = PurchaseRequisition
    template_name = 'purchasing/requisition_list.html'
    context_object_name = 'requisitions'

class PurchaseRequisitionCreateView(SalesCompassCreateView):
    model = PurchaseRequisition
    form_class = PurchaseRequisitionForm
    template_name = 'purchasing/requisition_form.html'
    success_url = reverse_lazy('purchasing:requisition_list')
    success_message = "Purchase Requisition created successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = PurchaseRequisitionLineFormSet(self.request.POST, form_kwargs={'tenant': self.request.user.tenant})
        else:
            context['lines'] = PurchaseRequisitionLineFormSet(form_kwargs={'tenant': self.request.user.tenant})
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            with transaction.atomic():
                form.instance.tenant = self.request.user.tenant
                form.instance.requested_by = self.request.user
                self.object = form.save()
                
                # Assign tenant to lines
                lines.instance = self.object
                requisition_lines = lines.save(commit=False)
                for line in requisition_lines:
                    line.tenant = self.request.user.tenant
                    line.save()
                lines.save_m2m()
                
                # Update total amount
                self.object.total_amount = sum(line.line_total for line in self.object.lines.all())
                self.object.save()
                
            messages.success(self.request, self.success_message)
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

class PurchaseRequisitionUpdateView(SalesCompassUpdateView):
    model = PurchaseRequisition
    form_class = PurchaseRequisitionForm
    template_name = 'purchasing/requisition_form.html'
    success_url = reverse_lazy('purchasing:requisition_list')
    success_message = "Purchase Requisition updated successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = PurchaseRequisitionLineFormSet(self.request.POST, instance=self.object, form_kwargs={'tenant': self.request.user.tenant})
        else:
            context['lines'] = PurchaseRequisitionLineFormSet(instance=self.object, form_kwargs={'tenant': self.request.user.tenant})
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            with transaction.atomic():
                self.object = form.save()
                lines.instance = self.object
                lines.save()
                
                # Update total amount
                self.object.total_amount = sum(line.line_total for line in self.object.lines.all())
                self.object.save()
                
            messages.success(self.request, self.success_message)
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

class PurchaseRequisitionDetailView(SalesCompassDetailView):
    model = PurchaseRequisition
    template_name = 'purchasing/requisition_detail.html'
    context_object_name = 'requisition'
    
    def post(self, request, *args, **kwargs):
        requisition = self.get_object()
        action = request.POST.get('action')
        
        if action == 'submit' and requisition.status == 'draft':
            requisition.status = 'pending'
            requisition.save()
            messages.success(request, "Requisition submitted for approval.")
        
        elif action == 'approve' and requisition.status == 'pending':
            requisition.status = 'approved'
            requisition.approved_by = request.user
            requisition.approval_date = timezone.now()
            requisition.save()
            messages.success(request, "Requisition approved.")
            
        elif action == 'reject' and requisition.status == 'pending':
            requisition.status = 'rejected'
            requisition.rejection_reason = request.POST.get('rejection_reason', '')
            requisition.save()
            messages.warning(request, "Requisition rejected.")
            
        return redirect('purchasing:requisition_detail', pk=requisition.pk)

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

@login_required
@require_GET
def get_invoice_details_api(request):
    """API endpoint to get invoice details for the payment form."""
    invoice_ids = request.GET.getlist('ids[]')
    tenant = request.user.tenant
    
    invoices = SupplierInvoice.objects.filter(
        tenant=tenant,
        pk__in=invoice_ids
    ).select_related('supplier', 'purchase_order')
    
    invoice_data = []
    total_outstanding = 0
    
    for invoice in invoices:
        amount_paid = sum(
            payment.amount 
            for payment in invoice.payments.all()
        )
        outstanding = float(invoice.total_amount) - float(amount_paid)
        total_outstanding += outstanding
        
        invoice_data.append({
            'id': invoice.pk,
            'invoice_number': invoice.invoice_number,
            'supplier': invoice.supplier.supplier_name,
            'invoice_date': invoice.invoice_date.strftime('%b %d, %Y'),
            'due_date': invoice.due_date.strftime('%b %d, %Y'),
            'total_amount': float(invoice.total_amount),
            'amount_paid': float(amount_paid),
            'outstanding': outstanding,
            'status': invoice.get_status_display(),
            'po_number': invoice.purchase_order.po_number if invoice.purchase_order else None,
        })
    
    return JsonResponse({
        'invoices': invoice_data,
        'total_outstanding': total_outstanding,
        'count': len(invoice_data)
    })


class PurchaseRequisitionConvertToPOView(SalesCompassDetailView):
    model = PurchaseRequisition
    template_name = 'purchasing/requisition_convert_po.html'
    context_object_name = 'requisition'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from suppliers.models import Supplier
        from inventory.models import Warehouse
        context['suppliers'] = Supplier.objects.filter(tenant=self.request.user.tenant, is_active=True)
        context['warehouses'] = Warehouse.objects.filter(tenant=self.request.user.tenant)
        return context

    def post(self, request, *args, **kwargs):
        requisition = self.get_object()
        if requisition.status != 'approved':
            messages.error(request, "Only approved requisitions can be converted to PO.")
            return redirect('purchasing:requisition_detail', pk=requisition.pk)
        
        supplier_id = request.POST.get('supplier')
        warehouse_id = request.POST.get('warehouse')
        
        if not supplier_id or not warehouse_id:
            messages.error(request, "Supplier and Warehouse are required.")
            return redirect('purchasing:requisition_detail', pk=requisition.pk)
            
        try:
            with transaction.atomic():
                po = PurchaseOrder.objects.create(
                    tenant=request.user.tenant,
                    supplier_id=supplier_id,
                    warehouse_id=warehouse_id,
                    order_date=timezone.now().date(),
                    status='draft',
                    requested_by=requisition.requested_by,
                    requisition=requisition
                )
                
                for line in requisition.lines.all():
                    PurchaseOrderLine.objects.create(
                        tenant=request.user.tenant,
                        purchase_order=po,
                        product=line.product,
                        quantity_ordered=line.quantity,
                        unit_cost=line.estimated_unit_price or 0
                    )
                
                requisition.status = 'ordered'
                requisition.save()

                # Calculate PO totals from lines
                po.recalculate_totals()
                
                messages.success(request, f"Purchase Order {po.po_number} created from requisition.")
                return redirect('purchasing:po_detail', pk=po.pk)
                
        except Exception as e:
            messages.error(request, f"Error converting to PO: {str(e)}")
            return redirect('purchasing:requisition_detail', pk=requisition.pk)

