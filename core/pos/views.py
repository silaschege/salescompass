from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, TemplateView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncHour
import json

from tenants.views import TenantAwareViewMixin
from core.views import (
    SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView
)
from .models import (
    POSTerminal, POSSession, POSTransaction, POSTransactionLine,
    POSPayment, POSReceipt, POSCashDrawer, POSRefund
)
from .forms import (
    TerminalForm, SessionOpenForm, SessionCloseForm, PaymentForm,
    VoidTransactionForm, RefundForm, CashMovementForm
)
from .services import POSService
from products.models import ProductCategory

from .hardware import (
    ReceiptPrinter, CashDrawer, CustomerDisplay
)


# =============================================================================
# DASHBOARD
# =============================================================================

class POSDashboardView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """POS dashboard with overview statistics."""
    template_name = 'pos/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        today = timezone.now().date()
        
        # Today's stats
        today_transactions = POSTransaction.objects.filter(
            tenant=tenant,
            status='completed',
            completed_at__date=today
        )
        context['today_sales'] = today_transactions.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        context['today_transactions'] = today_transactions.count()
        
        # Active sessions
        context['active_sessions'] = POSSession.objects.filter(
            tenant=tenant, status='active'
        ).select_related('terminal', 'cashier')
        
        # Terminals
        context['terminals'] = POSTerminal.objects.filter(
            tenant=tenant, is_active=True
        )
        
        # Recent transactions
        context['recent_transactions'] = POSTransaction.objects.filter(
            tenant=tenant
        ).order_by('-created_at')[:10]
        
        # Check if user has active session
        context['user_session'] = POSSession.objects.filter(
            cashier=self.request.user, status='active'
        ).first()
        
        return context


# =============================================================================
# POS TERMINAL INTERFACE
# =============================================================================

class POSTerminalView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Main POS terminal interface for sales."""
    template_name = 'pos/terminal.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get user's active session
        session = POSSession.objects.filter(
            cashier=self.request.user,
            status='active'
        ).select_related('terminal').first()
        
        if not session:
            context['no_session'] = True
            context['terminals'] = POSTerminal.objects.filter(
                tenant=tenant, is_active=True
            )
            return context
        
        context['session'] = session
        context['terminal'] = session.terminal
        
        # Get current draft transaction or create new one
        draft = POSTransaction.objects.filter(
            session=session,
            status='draft'
        ).first()
        
        if not draft:
            draft = POSService.create_transaction(
                session=session,
                cashier=self.request.user
            )
        
        context['transaction'] = draft
        context['lines'] = draft.lines.select_related('product')
        
        # Enhanced features context
        context['enable_quick_actions'] = True
        context['enable_customer_search'] = True
        context['enable_discounts'] = True
        
        return context


# =============================================================================
# TERMINAL MANAGEMENT
# =============================================================================

class TerminalListView(SalesCompassListView):
    """List all POS terminals."""
    model = POSTerminal
    template_name = 'pos/terminal_list.html'
    context_object_name = 'terminals'
    
    def get_queryset(self):
        return POSTerminal.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('warehouse')


class TerminalCreateView(SalesCompassCreateView):
    """Create a new POS terminal."""
    model = POSTerminal
    form_class = TerminalForm
    template_name = 'pos/terminal_form.html'
    success_url = reverse_lazy('pos:terminal_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, 'Terminal created successfully.')
        return super().form_valid(form)


class TerminalUpdateView(SalesCompassUpdateView):
    """Update a POS terminal."""
    model = POSTerminal
    form_class = TerminalForm
    template_name = 'pos/terminal_form.html'
    success_url = reverse_lazy('pos:terminal_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Terminal updated successfully.')
        return super().form_valid(form)


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

class SessionListView(SalesCompassListView):
    """List all POS sessions."""
    model = POSSession
    template_name = 'pos/session_list.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        return POSSession.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('terminal', 'cashier').order_by('-opened_at')


class SessionDetailView(SalesCompassDetailView):
    """Session detail with summary."""
    model = POSSession
    template_name = 'pos/session_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = POSTransaction.objects.filter(
            session=self.object
        ).order_by('-created_at')
        return context


class SessionOpenView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Open a new POS session."""
    template_name = 'pos/session_open.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SessionOpenForm(tenant=self.request.user.tenant)
        
        # Check for existing active session
        active = POSSession.objects.filter(
            cashier=self.request.user, status='active'
        ).first()
        if active:
            context['existing_session'] = active
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = SessionOpenForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            try:
                session = POSService.open_session(
                    terminal=form.cleaned_data['terminal'],
                    cashier=request.user,
                    opening_cash=form.cleaned_data['opening_cash'],
                    notes=form.cleaned_data.get('notes', '')
                )
                messages.success(request, f'Session {session.session_number} opened.')
                return redirect('pos:terminal')
            except ValueError as e:
                messages.error(request, str(e))
        
        return self.render_to_response({'form': form})


class SessionCloseView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Close a POS session."""
    template_name = 'pos/session_close.html'
    
    def get_session(self):
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            POSSession, pk=pk, tenant=self.request.user.tenant
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = self.get_session()
        context['form'] = SessionCloseForm()
        
        # Calculate expected cash
        session = context['session']
        cash_payments = POSPayment.objects.filter(
            transaction__session=session,
            payment_method='cash',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['expected_cash'] = session.opening_cash + cash_payments
        
        return context
    
    def post(self, request, *args, **kwargs):
        session = self.get_session()
        form = SessionCloseForm(request.POST)
        
        if form.is_valid():
            try:
                POSService.close_session(
                    session=session,
                    closing_cash=form.cleaned_data['closing_cash'],
                    cashier=request.user,
                    notes=form.cleaned_data.get('notes', '')
                )
                messages.success(request, f'Session {session.session_number} closed.')
                return redirect('pos:session_detail', pk=session.pk)
            except ValueError as e:
                messages.error(request, str(e))
        
        return self.render_to_response({
            'session': session,
            'form': form
        })


# =============================================================================
# TRANSACTIONS
# =============================================================================

class TransactionListView(SalesCompassListView):
    """List all transactions."""
    model = POSTransaction
    template_name = 'pos/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        qs = POSTransaction.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('terminal', 'cashier', 'customer')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        # Filter by date
        date = self.request.GET.get('date')
        if date:
            qs = qs.filter(created_at__date=date)
        
        return qs.order_by('-created_at')


class TransactionDetailView(SalesCompassDetailView):
    """Transaction detail with line items and payments."""
    model = POSTransaction
    template_name = 'pos/transaction_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.select_related('product')
        context['payments'] = self.object.payments.all()
        context['receipts'] = self.object.receipts.all()
        return context


class TransactionVoidView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Void a transaction."""
    template_name = 'pos/transaction_void.html'
    
    def get_transaction(self):
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            POSTransaction, pk=pk, tenant=self.request.user.tenant
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.get_transaction()
        context['form'] = VoidTransactionForm()
        return context
    
    def post(self, request, *args, **kwargs):
        transaction = self.get_transaction()
        form = VoidTransactionForm(request.POST)
        
        if form.is_valid():
            try:
                POSService.void_transaction(
                    transaction=transaction,
                    reason=form.cleaned_data['reason'],
                    user=request.user
                )
                messages.success(request, 'Transaction voided successfully.')
                return redirect('pos:transaction_detail', pk=transaction.pk)
            except ValueError as e:
                messages.error(request, str(e))
        
        return self.render_to_response({
            'transaction': transaction,
            'form': form
        })


# =============================================================================
# RECEIPTS
# =============================================================================

class ReceiptView(SalesCompassDetailView):
    """View a receipt."""
    model = POSReceipt
    template_name = 'pos/receipt.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.object.transaction
        context['lines'] = self.object.transaction.lines.all()
        context['payments'] = self.object.transaction.payments.all()
        return context


class ReceiptPrintView(LoginRequiredMixin, View):
    """Print view for receipt (thermal printer format)."""
    
    def get(self, request, pk):
        receipt = get_object_or_404(
            POSReceipt, pk=pk, tenant=request.user.tenant
        )
        receipt.printed_count += 1
        receipt.last_printed_at = timezone.now()
        receipt.is_printed = True
        receipt.save()
        
        # Return printable HTML or redirect to print view
        return redirect('pos:receipt_view', pk=pk)


# =============================================================================
# REFUNDS
# =============================================================================

class RefundListView(SalesCompassListView):
    """List all refunds."""
    model = POSRefund
    template_name = 'pos/refund_list.html'
    context_object_name = 'refunds'
    
    def get_queryset(self):
        return POSRefund.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('original_transaction').order_by('-created_at')


class RefundDetailView(SalesCompassDetailView):
    """Refund detail."""
    model = POSRefund
    template_name = 'pos/refund_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.select_related('original_line__product')
        return context


class RefundCreateView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Create a refund for a transaction."""
    template_name = 'pos/refund_create.html'
    
    def get_transaction(self):
        pk = self.kwargs.get('transaction_id')
        return get_object_or_404(
            POSTransaction, pk=pk, tenant=self.request.user.tenant
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction'] = self.get_transaction()
        context['lines'] = context['transaction'].lines.all()
        context['form'] = RefundForm()
        return context
    
    def post(self, request, *args, **kwargs):
        transaction = self.get_transaction()
        form = RefundForm(request.POST)
        
        if form.is_valid():
            # Get selected lines from POST data
            lines_to_refund = []
            for line in transaction.lines.all():
                qty_key = f'refund_qty_{line.id}'
                if qty_key in request.POST and request.POST[qty_key]:
                    lines_to_refund.append({
                        'line_id': line.id,
                        'quantity': request.POST[qty_key],
                        'restock': request.POST.get(f'restock_{line.id}', False) == 'on'
                    })
            
            if not lines_to_refund:
                messages.error(request, 'Please select items to refund.')
            else:
                try:
                    refund = POSService.create_refund(
                        original_transaction=transaction,
                        lines_to_refund=lines_to_refund,
                        reason=form.cleaned_data['reason'],
                        refund_method=form.cleaned_data['refund_method'],
                        user=request.user,
                        requires_approval=form.cleaned_data.get('requires_approval', True)
                    )
                    messages.success(request, f'Refund {refund.refund_number} created.')
                    return redirect('pos:refund_detail', pk=refund.pk)
                except ValueError as e:
                    messages.error(request, str(e))
        
        return self.render_to_response({
            'transaction': transaction,
            'lines': transaction.lines.all(),
            'form': form
        })


class RefundApproveView(LoginRequiredMixin, View):
    """Approve a pending refund."""
    
    def post(self, request, pk):
        refund = get_object_or_404(
            POSRefund, pk=pk, tenant=request.user.tenant
        )
        
        try:
            refund.approved_by = request.user
            refund.approved_at = timezone.now()
            refund.status = 'approved'
            refund.save()
            
            POSService.process_refund(refund, request.user)
            messages.success(request, 'Refund approved and processed.')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('pos:refund_detail', pk=pk)


# =============================================================================
# CASH DRAWER
# =============================================================================

class CashDrawerView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Cash drawer status and operations."""
    template_name = 'pos/cash_drawer.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        session = POSSession.objects.filter(
            cashier=self.request.user, status='active'
        ).first()
        
        if session:
            context['session'] = session
            context['drawer'] = POSCashDrawer.objects.filter(
                terminal=session.terminal
            ).first()
            context['movements'] = context['drawer'].movements.order_by('-created_at')[:20] if context['drawer'] else []
        
        return context


class CashPayInView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Add cash to drawer."""
    template_name = 'pos/cash_pay_in.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CashMovementForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = CashMovementForm(request.POST)
        
        session = POSSession.objects.filter(
            cashier=request.user, status='active'
        ).first()
        
        if not session:
            messages.error(request, 'No active session.')
            return redirect('pos:cash_drawer')
        
        if form.is_valid():
            try:
                POSService.pay_in(
                    session=session,
                    amount=form.cleaned_data['amount'],
                    user=request.user,
                    notes=form.cleaned_data['notes']
                )
                messages.success(request, 'Cash added to drawer.')
                return redirect('pos:cash_drawer')
            except ValueError as e:
                messages.error(request, str(e))
        
        return self.render_to_response({'form': form})


class CashPayOutView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Remove cash from drawer."""
    template_name = 'pos/cash_pay_out.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CashMovementForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = CashMovementForm(request.POST)
        
        session = POSSession.objects.filter(
            cashier=request.user, status='active'
        ).first()
        
        if not session:
            messages.error(request, 'No active session.')
            return redirect('pos:cash_drawer')
        
        if form.is_valid():
            try:
                POSService.pay_out(
                    session=session,
                    amount=form.cleaned_data['amount'],
                    user=request.user,
                    notes=form.cleaned_data['notes']
                )
                messages.success(request, 'Cash removed from drawer.')
                return redirect('pos:cash_drawer')
            except ValueError as e:
                messages.error(request, str(e))
        
        return self.render_to_response({'form': form})


# =============================================================================
# API ENDPOINTS
# =============================================================================

class ProductSearchAPI(LoginRequiredMixin, View):
    """API for product search."""
    
    def get(self, request):
        query = request.GET.get('q', '')
        category_id = request.GET.get('category')
        
        # If query is too short and no category, return empty
        if len(query) < 2 and not category_id:
            return JsonResponse({'products': []})
        
        products = POSService.search_products(
            query=query, 
            tenant=request.user.tenant,
            category_id=category_id
        )
        
        product_list = []
        for p in products:
            try:
                image_url = p.thumbnail.url if hasattr(p, 'thumbnail') and p.thumbnail else None
            except:
                image_url = None
                
            product_list.append({
                'id': p.id,
                'name': p.product_name,
                'sku': p.sku,
                'price': str(p.base_price),
                'image': image_url,
                'in_stock': True  # TODO: Check actual stock
            })
        
        return JsonResponse({
            'products': product_list
        })




    



class CategoryListAPI(LoginRequiredMixin, View):
    """API to get product categories."""
    
    def get_categories_recursive(self, parent=None, tenant=None):
        categories = ProductCategory.objects.filter(
            tenant=tenant, 
            parent=parent, 
            is_active=True
        ).order_by('display_order', 'name')
        
        result = []
        for cat in categories:
            data = {
                'id': cat.id,
                'name': cat.name,
                'image': cat.image.url if cat.image else None,
                'children': self.get_categories_recursive(cat, tenant)
            }
            result.append(data)
        return result

    def get(self, request):
        categories = self.get_categories_recursive(None, request.user.tenant)
        return JsonResponse(categories, safe=False)


class ProductBarcodeAPI(LoginRequiredMixin, View):
    """API for barcode lookup."""
    
    def get(self, request, barcode):
        product = POSService.get_product_by_barcode(barcode, request.user.tenant)
        
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)
        
        from inventory.models import StockLevel
        session = POSSession.objects.filter(cashier=request.user, status='active').first()
        warehouse = session.terminal.warehouse if session and session.terminal else None
        
        qty = 0
        if warehouse:
            stock = StockLevel.objects.filter(product=product, warehouse=warehouse).aggregate(total=Sum('quantity'))['total'] or 0
            reserved = StockLevel.objects.filter(product=product, warehouse=warehouse).aggregate(total=Sum('reserved_quantity'))['total'] or 0
            qty = float(stock - reserved)

        return JsonResponse({
            'id': product.id,
            'name': product.product_name,
            'sku': product.sku,
            'price': str(product.base_price),
            'in_stock': qty > 0,
            'stock_qty': qty
        })


class TransactionCreateAPI(LoginRequiredMixin, View):
    """API for creating transactions."""
    
    def post(self, request):
        session = POSSession.objects.filter(
            cashier=request.user, status='active'
        ).first()
        
        if not session:
            return JsonResponse({'error': 'No active session'}, status=400)
        
        transaction = POSService.create_transaction(
            session=session,
            cashier=request.user
        )
        
        return JsonResponse({
            'id': transaction.id,
            'number': transaction.transaction_number,
            'status': transaction.status,
            'subtotal': str(transaction.subtotal),
            'total_amount': str(transaction.total_amount),
            'created_at': transaction.created_at.isoformat()
        })


class TransactionLineAPI(LoginRequiredMixin, View):
    """API for managing transaction lines."""
    
    def post(self, request, pk):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        
        data = json.loads(request.body)
        from products.models import Product
        product = get_object_or_404(Product, pk=data['product_id'])
        
        try:
            line = POSService.add_line_item(
                transaction=transaction,
                product=product,
                quantity=data.get('quantity', 1),
                unit_price=data.get('unit_price'),
                discount_percent=data.get('discount_percent', 0)
            )
            
            return JsonResponse({
                'id': line.id,
                'product': line.product_name,
                'quantity': str(line.quantity),
                'line_total': str(line.line_total),
                'transaction_total': str(transaction.total_amount)
            })
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)


class TransactionPayAPI(LoginRequiredMixin, View):
    """API for processing payments, supports multiple payment methods."""
    
    def post(self, request, pk):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        
        data = json.loads(request.body)
        
        try:
            # Support for multiple payment methods
            payment_methods = data.get('payment_methods', [])
            
            if not payment_methods:
                # Fallback to single payment method if provided
                if 'payment_method' in data and 'amount' in data:
                    payment_methods = [{
                        'method': data['payment_method'],
                        'amount': data['amount'],
                        'reference_number': data.get('reference_number', ''),
                        'redeem_points': data.get('redeem_points', False)
                    }]
                else:
                    return JsonResponse({'error': 'No payment methods specified'}, status=400)
            
            total_paid = 0
            payments = []
            
            for method_data in payment_methods:
                payment = POSService.process_payment(
                    transaction=transaction,
                    payment_method=method_data['method'],
                    amount=method_data['amount'],
                    user=request.user,
                    reference_number=method_data.get('reference_number', ''),
                    redeem_points=method_data.get('redeem_points', False)
                )
                payments.append(payment)
                total_paid += payment.amount
            
            # Check if transaction is fully paid
            if transaction.status == 'completed':
                # Generate receipt
                receipt = POSService.generate_receipt(transaction)
                
                return JsonResponse({
                    'success': True,
                    'status': 'completed',
                    'receipt_id': receipt.id,
                    'change_due': str(transaction.change_due),
                    'payments': [p.id for p in payments]
                })
            else:
                return JsonResponse({
                    'success': True,
                    'status': 'partial',
                    'amount_paid': str(transaction.amount_paid),
                    'remaining': str(transaction.balance_due),
                    'payments': [p.id for p in payments]
                })
                
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Internal server error'}, status=500)



class ProductListAPI(LoginRequiredMixin, View):
    """API for listing all products."""
    
    def get(self, request):
        from products.models import Product
        category_id = request.GET.get('category')
        
        products = Product.objects.filter(
            tenant=request.user.tenant,
            product_is_active=True
        )
        
        if category_id:
            products = products.filter(category_id=category_id)
            
        products = products[:50]  # Limit to 50 products
        
        product_list = []
        for p in products:
            try:
                image_url = p.thumbnail.url if hasattr(p, 'thumbnail') and p.thumbnail else None
            except:
                image_url = None
                
            product_list.append({
                'id': p.id,
                'name': p.product_name,
                'sku': p.sku,
                'price': str(p.base_price),
                'image': image_url,
                'in_stock': True  # TODO: Check actual stock
            })
        
        return JsonResponse({
            'products': product_list
        })




class TransactionDetailAPI(LoginRequiredMixin, View):
    """API for getting transaction details."""
    
    def get(self, request, pk):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        
        lines = [{
            'id': line.id,
            'product_id': line.product_id,
            'product_name': line.product_name,
            'quantity': str(line.quantity),
            'unit_price': str(line.unit_price),
            'discount_percent': str(line.discount_percent),
            'line_total': str(line.line_total)
        } for line in transaction.lines.all()]
        
        return JsonResponse({
            'id': transaction.id,
            'number': transaction.transaction_number,
            'status': transaction.status,
            'subtotal': str(transaction.subtotal),
            'discount_amount': str(transaction.discount_amount),
            'tax_amount': str(transaction.tax_amount),
            'total': str(transaction.total_amount),
            'lines': lines,
            'customer': {
                'id': transaction.customer_id,
                'name': transaction.customer.account_name if transaction.customer else transaction.customer_name
            } if transaction.customer or transaction.customer_name else None
        })


class TransactionLineUpdateAPI(LoginRequiredMixin, View):
    """API for updating or deleting transaction lines."""
    
    def patch(self, request, pk, line_id):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        line = get_object_or_404(
            POSTransactionLine, pk=line_id, transaction=transaction
        )
        
        data = json.loads(request.body)
        
        if 'quantity' in data:
            new_qty = int(data['quantity'])
            if new_qty < 1:
                return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
            line.quantity = new_qty
        
        if 'discount_percent' in data:
            line.discount_percent = data['discount_percent']
        
        line.save()
        transaction.refresh_from_db()
        
        return JsonResponse({
            'id': line.id,
            'quantity': str(line.quantity),
            'line_total': str(line.line_total),
            'transaction_total': str(transaction.total_amount)
        })
    
    def delete(self, request, pk, line_id):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        line = get_object_or_404(
            POSTransactionLine, pk=line_id, transaction=transaction
        )
        
        line.delete()
        transaction.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'transaction_total': str(transaction.total_amount)
        })


class TransactionClearAPI(LoginRequiredMixin, View):
    """API for clearing all items from a transaction."""
    
    def post(self, request, pk):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        
        if transaction.status != 'draft':
            return JsonResponse({'error': 'Can only clear draft transactions'}, status=400)
        
        transaction.lines.all().delete()
        transaction.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'transaction_total': str(transaction.total_amount)
        })


class TransactionHoldAPI(LoginRequiredMixin, View):
    """API for putting a transaction on hold."""
    
    def post(self, request, pk):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        
        if transaction.status != 'draft':
            return JsonResponse({'error': 'Can only hold draft transactions'}, status=400)
        
        transaction.status = 'on_hold'
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'status': transaction.status
        })

class HeldTransactionsAPI(LoginRequiredMixin, View):
    """API for listing held transactions."""
    def get(self, request):
        transactions = POSTransaction.objects.filter(
            tenant=request.user.tenant,
            status='on_hold'
        ).order_by('-updated_at')[:20]
        
        data = [{
            'id': t.id,
            'transaction_number': t.transaction_number,
            'customer_name': t.customer.account_name if t.customer else t.customer_name,
            'total': float(t.total_amount),
            'items_count': t.lines.count(),
            'held_at': t.updated_at.strftime('%Y-%m-%d %H:%M')
        } for t in transactions]
        
        return JsonResponse({'transactions': data})

class TransactionResumeAPI(LoginRequiredMixin, View):
    """API for resuming a held transaction."""
    def post(self, request, pk):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        
        if transaction.status != 'on_hold':
             return JsonResponse({'error': 'Can only resume held transactions'}, status=400)
        
        transaction.status = 'draft'
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'id': transaction.id,
            'transaction_number': transaction.transaction_number
        })


class TransactionCustomerAPI(LoginRequiredMixin, View):
    """API for setting customer on a transaction."""
    
    def post(self, request, pk):
        transaction = get_object_or_404(
            POSTransaction, pk=pk, tenant=request.user.tenant
        )
        
        data = json.loads(request.body)
        
        if 'customer_id' in data:
            from accounts.models import Account
            customer = get_object_or_404(
                Account, pk=data['customer_id'], tenant=request.user.tenant
            )
            transaction.customer = customer
            transaction.customer_name = customer.account_name
        else:
            # Walk-in customer info
            transaction.customer_name = data.get('customer_name', '')
            transaction.customer_phone = data.get('customer_phone', '')
            transaction.customer_email = data.get('customer_email', '')
        
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'customer_name': transaction.customer_name
        })


# =============================================================================
# REPORTS
# =============================================================================


class POSReportsView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """POS reports dashboard."""
    template_name = 'pos/reports.html'


class DailySalesReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Daily sales report."""
    template_name = 'pos/report_daily.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        date = self.request.GET.get('date', timezone.now().date())
        
        transactions = POSTransaction.objects.filter(
            tenant=tenant,
            status='completed',
            completed_at__date=date
        )
        
        context['date'] = date
        context['transactions'] = transactions
        context['total_sales'] = transactions.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        context['total_transactions'] = transactions.count()
        context['average_sale'] = transactions.aggregate(
            avg=Avg('total_amount')
        )['avg'] or 0
        
        # Payment method breakdown
        context['payment_breakdown'] = POSPayment.objects.filter(
            transaction__in=transactions
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        return context


class CashierReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Cashier performance report."""
    template_name = 'pos/report_cashier.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get all cashiers with transaction counts
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        context['cashiers'] = User.objects.filter(
            pos_transactions_processed__tenant=tenant
        ).annotate(
            transaction_count=Count('pos_transactions_processed'),
            total_sales=Sum('pos_transactions_processed__total_amount')
        ).order_by('-total_sales')
        
        return context
from django.db.models.functions import TruncHour

class XReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Mid-day summary report (non-resetting)."""
    template_name = 'pos/report_x.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get current active session for the user
        session = POSSession.objects.filter(
            cashier=self.request.user, 
            status='active'
        ).select_related('terminal').first()
        
        if not session:
            context['no_session'] = True
            return context
            
        context['session'] = session
        context['report_date'] = timezone.now()
        
        # Transactions in this session
        transactions = POSTransaction.objects.filter(
            session=session,
            status='completed'
        )
        
        # Summaries
        context['total_sales'] = transactions.aggregate(t=Sum('total_amount'))['t'] or 0
        context['transaction_count'] = transactions.count()
        context['total_tax'] = transactions.aggregate(t=Sum('tax_amount'))['t'] or 0
        context['total_discount'] = transactions.aggregate(t=Sum('discount_amount'))['t'] or 0
        
        # Breakdowns
        context['payment_methods'] = POSPayment.objects.filter(
            transaction__session=session,
            status='completed'
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Hourly breakdown
        context['hourly_sales'] = transactions.annotate(
            hour=TruncHour('completed_at')
        ).values('hour').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('hour')
        
        return context


class ZReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """End-of-day report (resets counters)."""
    template_name = 'pos/report_z.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # For Z-Report, we might look at the most recently CLOSED session 
        # OR the current active session if we are about to close it.
        # Let's show the current active session as a "Preview" or the last closed one.
        # Typically Z-Report is printed AT CLOSING.
        
        # Let's prefer the active session to show what will be closed.
        session = POSSession.objects.filter(
            cashier=self.request.user,
            status='active'
        ).select_related('terminal').first()
        
        if not session:
            # Fallback to last closed session for re-printing
            session = POSSession.objects.filter(
                cashier=self.request.user,
                status='closed'
            ).order_by('-closed_at').first()
            
        if not session:
             context['no_session'] = True
             return context

        context['session'] = session
        context['report_type'] = 'Z-Report'
        context['generated_at'] = timezone.now()
        
        transactions = POSTransaction.objects.filter(session=session)
        completed_txns = transactions.filter(status='completed')
        
        # Financials
        context['net_sales'] = completed_txns.aggregate(t=Sum('total_amount'))['t'] or 0 - (completed_txns.aggregate(t=Sum('tax_amount'))['t'] or 0)
        context['tax_collected'] = completed_txns.aggregate(t=Sum('tax_amount'))['t'] or 0
        context['gross_sales'] = completed_txns.aggregate(t=Sum('total_amount'))['t'] or 0
        
        # Returns/Voids
        context['voids_count'] = transactions.filter(status='voided').count()
        context['returns_count'] = POSRefund.objects.filter(original_transaction__session=session).count()
        context['total_returns'] = POSRefund.objects.filter(original_transaction__session=session).aggregate(t=Sum('refund_amount'))['t'] or 0
        
        # Payments
        context['payment_methods'] = POSPayment.objects.filter(
            transaction__session=session,
            status='completed'
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Cash Reconciliation (if closed)
        if session.status == 'closed':
            context['expected_cash'] = session.expected_cash
            context['actual_cash'] = session.closing_cash
            context['variance'] = session.cash_difference
            
        return context


class ReceiptPreviewView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """
    Web-based print preview for testing without hardware.
    Simulates character-based thermal printer output.
    """
    template_name = 'pos/receipt_preview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        transaction = get_object_or_404(POSTransaction, pk=pk, tenant=self.request.user.tenant)
        terminal = transaction.terminal
        width = terminal.printer_width if terminal else 48

        # Generate text representation
        lines = []
        tenant = self.request.user.tenant
        
        # Header
        lines.append(tenant.tenant_name.center(width))
        if tenant.address:
            lines.append(tenant.address.center(width))
        if tenant.phone:
            lines.append(f"Tel: {tenant.phone}".center(width))
        lines.append("-" * width)
        
        # Info
        lines.append(f"Receipt #: {transaction.transaction_number}")
        lines.append(f"Date: {transaction.completed_at.strftime('%Y-%m-%d %H:%M') if transaction.completed_at else 'DRAFT'}")
        lines.append(f"Cashier: {transaction.cashier.username}")
        if transaction.customer_name:
            lines.append(f"Customer: {transaction.customer_name}")
        lines.append("-" * width)
        
        # Items
        for item in transaction.lines.all():
            lines.append(item.product_name[:width])
            qty_price = f"{item.quantity} x {item.unit_price}"
            total = f"{item.line_total}"
            lines.append(qty_price + total.rjust(width - len(qty_price)))
        
        lines.append("-" * width)
        
        # Totals
        subtotal = f"Subtotal: {transaction.subtotal}"
        lines.append(subtotal.rjust(width))
        if transaction.tax_amount > 0:
            tax = f"Tax: {transaction.tax_amount}"
            lines.append(tax.rjust(width))
        if transaction.discount_amount > 0:
            discount = f"Discount: -{transaction.discount_amount}"
            lines.append(discount.rjust(width))
        
        total_str = f"TOTAL: {transaction.total_amount}"
        lines.append("=" * width)
        lines.append(total_str.rjust(width))
        lines.append("=" * width)
        
        # Footer
        if terminal and terminal.receipt_footer:
            lines.append("\n" + terminal.receipt_footer.center(width))
        
        lines.append("\n" + "THANK YOU FOR YOUR PURCHASE!".center(width))
        lines.append("\n\n\n") # Extra space for cutting
        
        context['receipt_text'] = "\n".join(lines)
        context['transaction'] = transaction
        context['terminal'] = terminal
        return context

class HardwareTestView(LoginRequiredMixin, TenantAwareViewMixin, DetailView):
    """View terminal hardware diagnostic page."""
    model = POSTerminal
    template_name = 'pos/hardware_test.html'
    context_object_name = 'terminal'

    def get_queryset(self):
        return POSTerminal.objects.filter(tenant=self.request.user.tenant)


class HardwareTestAPI(LoginRequiredMixin, View):

    def post(self, request, pk):
        terminal = get_object_or_404(POSTerminal, pk=pk, tenant=request.user.tenant)
        data = json.loads(request.body)
        action = data.get('action')
        
        results = {
            'timestamp': timezone.now().isoformat(),
            'terminal': terminal.terminal_name,
            'tests': [],
            'overall_status': 'unknown'
        }
        
        try:
            # Initialize printer driver
            printer = None
            if terminal.printer_type != 'disabled':
                printer = ReceiptPrinter(
                    connection_type=terminal.printer_type,
                    host=terminal.printer_ip,
                    path=terminal.printer_port,
                    width=terminal.printer_width
                )
            
            if action == 'full_diagnostic':
                # Run comprehensive diagnostic tests
                test_results = self.run_full_diagnostic(terminal, printer)
                results['tests'] = test_results
                
                # Determine overall status
                if all(test['status'] == 'pass' for test in test_results):
                    results['overall_status'] = 'pass'
                elif any(test['status'] == 'critical' for test in test_results):
                    results['overall_status'] = 'fail'
                else:
                    results['overall_status'] = 'warning'
                    
            elif action == 'print_test':
                # Print test page
                test_result = self.run_print_test(terminal, printer)
                results['tests'].append(test_result)
                results['overall_status'] = test_result['status']
                
            elif action == 'kick_drawer':
                # Test cash drawer
                test_result = self.run_drawer_test(terminal, printer)
                results['tests'].append(test_result)
                results['overall_status'] = test_result['status']
                
            elif action == 'cut_paper':
                # Test paper cutter
                test_result = self.run_cut_test(terminal, printer)
                results['tests'].append(test_result)
                results['overall_status'] = test_result['status']
                
            elif action == 'display_test':
                # Test customer display
                test_result = self.run_display_test(terminal)
                results['tests'].append(test_result)
                results['overall_status'] = test_result['status']
                
            return JsonResponse(results)
            
        except Exception as e:
            results['tests'].append({
                'name': 'System Error',
                'status': 'fail',
                'message': str(e)
            })
            results['overall_status'] = 'fail'
            return JsonResponse(results)

    def run_full_diagnostic(self, terminal, printer):
        """Run comprehensive diagnostic tests."""
        tests = []
        
        # Printer test
        printer_test = self.run_print_test(terminal, printer)
        tests.append(printer_test)
        
        # Drawer test
        drawer_test = self.run_drawer_test(terminal, printer)
        tests.append(drawer_test)
        
        # Display test
        display_test = self.run_display_test(terminal)
        tests.append(display_test)
        
        # Network connectivity test
        network_test = self.run_network_test(terminal)
        tests.append(network_test)
        
        return tests
    
    def run_print_test(self, terminal, printer):
        """Run printer test."""
        result = {
            'name': 'Printer Test',
            'status': 'fail',
            'message': '',
            'details': {}
        }
        
        try:
            if not printer:
                result['status'] = 'fail'
                result['message'] = 'Printer disabled'
                return result
                
            printer.connect()
            printer.text("HARDWARE TEST", align='center', bold=True, double_height=True)
            printer.line()
            printer.text(f"Terminal: {terminal.terminal_name}")
            printer.text(f"Code: {terminal.terminal_code}")
            printer.text(f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            printer.text("TEST COMPLETE", align='center')
            printer.cut()
            printer.close()
            
        except Exception as e:
            result['status'] = 'fail'
            result['message'] = str(e)
            
        return result

    def run_drawer_test(self, terminal, printer):
        """Run cash drawer kick test."""
        result = {'name': 'Cash Drawer Test', 'status': 'fail', 'message': ''}
        try:
            if not printer:
                result['message'] = 'Printer (required for drawer) disabled'
                return result
            printer.connect()
            printer.kick_drawer()
            printer.close()
            result['status'] = 'pass'
            result['message'] = 'Drawer kick command sent'
        except Exception as e:
            result['message'] = str(e)
        return result

    def run_cut_test(self, terminal, printer):
        """Run paper cutter test."""
        result = {'name': 'Paper Cutter Test', 'status': 'fail', 'message': ''}
        try:
            if not printer:
                result['message'] = 'Printer disabled'
                return result
            printer.connect()
            printer.cut()
            printer.close()
            result['status'] = 'pass'
            result['message'] = 'Paper cut command sent'
        except Exception as e:
            result['message'] = str(e)
        return result

    def run_display_test(self, terminal):
        """Run customer display test."""
        result = {'name': 'Customer Display Test', 'status': 'fail', 'message': ''}
        try:
            if terminal.customer_display_enabled:
                display = CustomerDisplay(port=terminal.customer_display_port)
                display.connect()
                display.clear()
                display.text("HARDWARE TEST", line=1)
                display.text("PASSED", line=2)
                display.close()
                result['status'] = 'pass'
                result['message'] = 'Display command sent'
            else:
                result['message'] = 'Customer display disabled'
        except Exception as e:
            result['message'] = str(e)
        return result

    def run_network_test(self, terminal):
        """Run network connectivity test."""
        result = {'name': 'Network Test', 'status': 'fail', 'message': ''}
        try:
            import socket
            if terminal.printer_type == 'network' and terminal.printer_ip:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((terminal.printer_ip, 9100)) # Standard RAW port
                s.close()
                result['status'] = 'pass'
                result['message'] = f"Successfully connected to {terminal.printer_ip}:9100"
            else:
                result['status'] = 'pass'
                result['message'] = 'No network hardware to test'
        except Exception as e:
            result['message'] = f"Failed to connect to {terminal.printer_ip}: {str(e)}"
        return result
        
class ProductStockAPI(LoginRequiredMixin, View):
    """Enhanced product stock polling with real-time updates and category filtering."""
    
    def get(self, request):
        product_ids = request.GET.getlist('ids[]')
        category_id = request.GET.get('category_id')
        
        from products.models import Product
        from inventory.models import StockLevel
        from django.db.models import Sum

        query = Product.objects.filter(tenant=request.user.tenant)
        
        if product_ids:
            query = query.filter(id__in=product_ids)
        elif category_id:
            query = query.filter(category_id=category_id)
        else:
            return JsonResponse([], safe=False)
            
        session = POSSession.objects.filter(cashier=request.user, status='active').first()
        warehouse = session.terminal.warehouse if session and session.terminal else None
        
        res = []
        for p in query:
            qty = 0
            if warehouse:
                try:
                    stock = StockLevel.objects.filter(product=p, warehouse=warehouse).aggregate(total=Sum('quantity'))['total'] or 0
                    reserved = StockLevel.objects.filter(product=p, warehouse=warehouse).aggregate(total=Sum('reserved_quantity'))['total'] or 0
                    qty = float(stock - reserved)
                except Exception:
                    qty = 0  
                    
            res.append({
                'id': p.id,
                'product_name': p.product_name,
                'sku': p.sku,
                'stock_quantity': qty,
                'last_updated': timezone.now().isoformat(),
                'low_stock_threshold': getattr(p, 'low_stock_threshold', 10)
            })
            
        return JsonResponse(res, safe=False)


class ProductSalesReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """Report on top selling products."""
    template_name = 'pos/report_products.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Top 10 products by quantity
        top_products = POSTransactionLine.objects.filter(
            transaction__tenant=tenant,
            transaction__status='completed'
        ).values(
            'product_name', 'product_sku'
        ).annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum('line_total')
        ).order_by('-total_qty')[:20]
        
        context['products'] = top_products
        return context


class SalesTrendsReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """View for sales trends report."""
    template_name = 'pos/report_trends.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        from django.db.models.functions import TruncDate
        
        # Last 30 days of sales
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=30)
        
        daily_sales = POSTransaction.objects.filter(
            tenant=tenant,
            status='completed',
            completed_at__date__range=[start_date, end_date]
        ).annotate(
            date=TruncDate('completed_at')
        ).values('date').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('date')
        
        context['daily_sales'] = daily_sales
        return context


class PaymentMethodsReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """View for payment methods report."""
    template_name = 'pos/report_payments.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Payment method breakdown
        payments = POSPayment.objects.filter(
            transaction__tenant=tenant,
            status='completed'
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        context['payments'] = payments
        return context


class RefundsVoidsReportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """View for refunds and voids report."""
    template_name = 'pos/report_refunds_voids.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        context['refunds'] = POSRefund.objects.filter(
            tenant=tenant
        ).select_related('original_transaction', 'processed_by').order_by('-created_at')[:50]
        
        context['voids'] = POSTransaction.objects.filter(
            tenant=tenant,
            status='voided'
        ).select_related('cashier').order_by('-updated_at')[:50]
        
        return context
