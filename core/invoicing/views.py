from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.db.models import Sum
from .models import Invoice, InvoiceLine, Payment, CreditNote, DebitNote
from .forms import InvoiceForm, InvoiceLineFormSet, PaymentForm, CreditNoteForm, DebitNoteForm

class TenantInvoiceMixin(LoginRequiredMixin):
    def get_queryset(self):
        # Ensure tenant isolation
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant'):
            queryset = queryset.filter(tenant=self.request.user.tenant)
        return queryset

class InvoiceListView(TenantInvoiceMixin, ListView):
    model = Invoice
    template_name = 'invoicing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(invoice_number__icontains=search) | \
                       queryset.filter(customer__account_name__icontains=search)
                       
        # Filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-issue_date')

class InvoiceDetailView(TenantInvoiceMixin, DetailView):
    model = Invoice
    template_name = 'invoicing/invoice_detail.html'
    context_object_name = 'invoice'

class InvoiceCreateView(TenantInvoiceMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'
    success_url = reverse_lazy('invoicing:invoice_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs
        
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['inlines'] = InvoiceLineFormSet(self.request.POST)
        else:
            data['inlines'] = InvoiceLineFormSet()
        return data
        
    def form_valid(self, form):
        context = self.get_context_data()
        inlines = context['inlines']
        
        if hasattr(self.request.user, 'tenant'):
            form.instance.tenant = self.request.user.tenant
            
        self.object = form.save()
        
        if inlines.is_valid():
            inlines.instance = self.object
            inlines.save()
            
            # Update totals after saving lines
            self.object.subtotal = self.object.lines.aggregate(Sum('amount'))['amount__sum'] or 0
            self.object.total_amount = self.object.subtotal + self.object.tax_amount
            self.object.save()
            
            messages.success(self.request, f'Invoice {self.object.invoice_number} created successfully.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

class InvoiceUpdateView(TenantInvoiceMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'
    success_url = reverse_lazy('invoicing:invoice_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs
        
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['inlines'] = InvoiceLineFormSet(self.request.POST, instance=self.object)
        else:
            data['inlines'] = InvoiceLineFormSet(instance=self.object)
        return data
        
    def form_valid(self, form):
        context = self.get_context_data()
        inlines = context['inlines']
        
        self.object = form.save()
        
        if inlines.is_valid():
            inlines.save()
            
            # Recalculate totals
            self.object.subtotal = self.object.lines.aggregate(Sum('amount'))['amount__sum'] or 0
            self.object.total_amount = self.object.subtotal + self.object.tax_amount
            self.object.save()
            
            messages.success(self.request, f'Invoice {self.object.invoice_number} updated.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

class InvoiceDeleteView(TenantInvoiceMixin, DeleteView):
    model = Invoice
    # Need a confirmation template or just use generic one
    template_name = 'invoicing/invoice_confirm_delete.html' 
    success_url = reverse_lazy('invoicing:invoice_list')
    
    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, 'tenant'):
             qs = qs.filter(tenant=self.request.user.tenant)
        return qs

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Invoice deleted successfully.')
        return super().delete(request, *args, **kwargs)
        

class InvoiceMarkPaidView(TenantInvoiceMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        if hasattr(request.user, 'tenant') and invoice.tenant != request.user.tenant:
             return redirect('invoicing:invoice_list')
             
        invoice.status = 'paid'
        invoice.amount_paid = invoice.total_amount
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} marked as paid.')
        return redirect('invoicing:invoice_detail', pk=pk)
        
    def get(self, request, pk):
         return self.post(request, pk)

class InvoiceSendView(TenantInvoiceMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        # Placeholder for sending email logic
        invoice.status = 'sent'
        invoice.save()
        messages.success(request, f'Invoice {invoice.invoice_number} sent to customer.')
        return redirect('invoicing:invoice_detail', pk=pk)

import io
from django.http import HttpResponse

class InvoicePDFView(TenantInvoiceMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        # Placeholder for PDF generation
        # In a real app, use WeasyPrint or ReportLab
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename="invoice_{invoice.invoice_number}.pdf"'
        
        # Simple text PDF for now
        from reportlab.pdfgen import canvas
        p = canvas.Canvas(response)
        p.drawString(100, 800, f"Invoice: {invoice.invoice_number}")
        p.drawString(100, 780, f"Customer: {invoice.customer}")
        p.drawString(100, 760, f"Total: ${invoice.total_amount}")
        p.showPage()
        p.save()
        
        return response

class DashboardView(TenantInvoiceMixin, ListView):
    model = Invoice
    template_name = 'invoicing/dashboard.html'
    context_object_name = 'recent_invoices'

    def get_queryset(self):
        return super().get_queryset().order_by('-created_at')[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Invoice.objects.filter(tenant=self.request.user.tenant) if hasattr(self.request.user, 'tenant') else Invoice.objects.all()
        context['total_sales'] = qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['overdue_count'] = qs.filter(status='overdue').count()
        context['draft_count'] = qs.filter(status='draft').count()
        return context

class PaymentListView(TenantInvoiceMixin, ListView):
    model = Payment
    template_name = 'invoicing/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

class PaymentCreateView(TenantInvoiceMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'invoicing/payment_form.html'
    success_url = reverse_lazy('invoicing:payment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant'):
            form.instance.tenant = self.request.user.tenant
        messages.success(self.request, "Payment recorded successfully.")
        return super().form_valid(form)

class CreditNoteListView(TenantInvoiceMixin, ListView):
    model = CreditNote
    template_name = 'invoicing/credit_note_list.html'
    context_object_name = 'credit_notes'

class CreditNoteCreateView(TenantInvoiceMixin, CreateView):
    model = CreditNote
    form_class = CreditNoteForm
    template_name = 'invoicing/credit_note_form.html'
    success_url = reverse_lazy('invoicing:credit_note_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs

class DebitNoteListView(TenantInvoiceMixin, ListView):
    model = DebitNote
    template_name = 'invoicing/debit_note_list.html'
    context_object_name = 'debit_notes'

class DebitNoteCreateView(TenantInvoiceMixin, CreateView):
    model = DebitNote
    form_class = DebitNoteForm
    template_name = 'invoicing/debit_note_form.html'
    success_url = reverse_lazy('invoicing:debit_note_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant'):
            kwargs['tenant'] = self.request.user.tenant
        return kwargs

