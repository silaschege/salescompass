from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum

from tenants.views import TenantAwareViewMixin
from core.views import SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView, SalesCompassUpdateView

from .models import Supplier, SupplierCategory, SupplierContact, SupplierDocument, SupplierPerformanceReview
from .forms import SupplierForm, SupplierCategoryForm, SupplierContactForm, SupplierDocumentForm, SupplierPerformanceReviewForm


# =============================================================================
# SUPPLIER VIEWS
# =============================================================================

class SupplierListView(SalesCompassListView):
    """List all suppliers with search and filter."""
    model = Supplier
    template_name = 'suppliers/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 25
    
    def get_queryset(self):
        qs = Supplier.objects.filter(tenant=self.request.user.tenant)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(supplier_name__icontains=search)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        
        return qs.select_related('category').order_by('supplier_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SupplierCategory.objects.filter(tenant=self.request.user.tenant)
        context['status_choices'] = Supplier.STATUS_CHOICES
        return context


class SupplierDetailView(SalesCompassDetailView):
    """Supplier detail with contacts, documents, and stats."""
    model = Supplier
    template_name = 'suppliers/supplier_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contacts'] = self.object.contacts.all()
        context['documents'] = self.object.documents.all()[:10]
        context['reviews'] = self.object.performance_reviews.all()[:5]
        
        # Get PO stats if purchasing module exists
        try:
            from purchasing.models import PurchaseOrder
            context['po_count'] = PurchaseOrder.objects.filter(
                supplier=self.object, tenant=self.request.user.tenant
            ).count()
            context['po_total'] = PurchaseOrder.objects.filter(
                supplier=self.object, tenant=self.request.user.tenant
            ).aggregate(total=Sum('total_amount'))['total'] or 0
        except ImportError:
            pass
        
        return context


class SupplierCreateView(SalesCompassCreateView):
    """Create a new supplier."""
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('suppliers:supplier_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Supplier created successfully.')
        return super().form_valid(form)


class SupplierUpdateView(SalesCompassUpdateView):
    """Update a supplier."""
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Supplier updated successfully.')
        return super().form_valid(form)


class SupplierDeleteView(LoginRequiredMixin, TenantAwareViewMixin, DeleteView):
    """Delete a supplier."""
    model = Supplier
    template_name = 'suppliers/supplier_confirm_delete.html'
    success_url = reverse_lazy('suppliers:supplier_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Supplier deleted successfully.')
        return super().delete(request, *args, **kwargs)


# =============================================================================
# CATEGORY VIEWS
# =============================================================================

class CategoryListView(SalesCompassListView):
    """List supplier categories."""
    model = SupplierCategory
    template_name = 'suppliers/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(SalesCompassCreateView):
    """Create a supplier category."""
    model = SupplierCategory
    form_class = SupplierCategoryForm
    template_name = 'suppliers/category_form.html'
    success_url = reverse_lazy('suppliers:category_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)


class CategoryUpdateView(SalesCompassUpdateView):
    """Update a supplier category."""
    model = SupplierCategory
    form_class = SupplierCategoryForm
    template_name = 'suppliers/category_form.html'
    success_url = reverse_lazy('suppliers:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully.')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, TenantAwareViewMixin, DeleteView):
    """Delete a supplier category."""
    model = SupplierCategory
    template_name = 'suppliers/category_confirm_delete.html'
    success_url = reverse_lazy('suppliers:category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Category deleted successfully.')
        return super().delete(request, *args, **kwargs)


# =============================================================================
# CONTACT VIEWS
# =============================================================================

class ContactCreateView(LoginRequiredMixin, TenantAwareViewMixin, CreateView):
    """Add a contact to a supplier."""
    model = SupplierContact
    form_class = SupplierContactForm
    template_name = 'suppliers/contact_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.supplier = get_object_or_404(Supplier, pk=kwargs['supplier_pk'], tenant=request.user.tenant)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        return context
    
    def form_valid(self, form):
        form.instance.supplier = self.supplier
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, 'Contact added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_detail', kwargs={'pk': self.supplier.pk})


class ContactUpdateView(LoginRequiredMixin, TenantAwareViewMixin, UpdateView):
    """Edit a supplier contact."""
    model = SupplierContact
    form_class = SupplierContactForm
    template_name = 'suppliers/contact_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.supplier = get_object_or_404(Supplier, pk=kwargs['supplier_pk'], tenant=request.user.tenant)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Contact updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_detail', kwargs={'pk': self.supplier.pk})


class ContactDeleteView(LoginRequiredMixin, TenantAwareViewMixin, DeleteView):
    """Delete a supplier contact."""
    model = SupplierContact
    template_name = 'suppliers/contact_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.supplier = get_object_or_404(Supplier, pk=kwargs['supplier_pk'], tenant=request.user.tenant)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        return context

    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_detail', kwargs={'pk': self.supplier.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Contact deleted successfully.')
        return super().delete(request, *args, **kwargs)


# =============================================================================
# DOCUMENT VIEWS
# =============================================================================

class DocumentCreateView(LoginRequiredMixin, TenantAwareViewMixin, CreateView):
    """Upload a document to a supplier."""
    model = SupplierDocument
    form_class = SupplierDocumentForm
    template_name = 'suppliers/document_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.supplier = get_object_or_404(Supplier, pk=kwargs['supplier_pk'], tenant=request.user.tenant)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        return context
    
    def form_valid(self, form):
        form.instance.supplier = self.supplier
        form.instance.tenant = self.request.user.tenant
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Document uploaded successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_detail', kwargs={'pk': self.supplier.pk})


# =============================================================================
# API VIEWS
# =============================================================================

class SupplierSearchAPI(LoginRequiredMixin, ListView):
    """API for supplier search (used by product forms, POs, etc.)"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        suppliers = Supplier.objects.filter(
            tenant=request.user.tenant,
            is_active=True,
            supplier_name__icontains=query
        )[:20]
        
        data = [{
            'id': s.id,
            'name': s.supplier_name,
            'code': s.supplier_code,
            'email': s.email
        } for s in suppliers]
        
        return JsonResponse({'suppliers': data})


class PerformanceReviewCreateView(LoginRequiredMixin, TenantAwareViewMixin, CreateView):
    """Add a performance review for a supplier."""
    model = SupplierPerformanceReview
    form_class = SupplierPerformanceReviewForm
    template_name = 'suppliers/performance_review_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.supplier = get_object_or_404(Supplier, pk=kwargs['supplier_pk'], tenant=request.user.tenant)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        return context
    
    def form_valid(self, form):
        form.instance.supplier = self.supplier
        form.instance.tenant = self.request.user.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Performance review added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_detail', kwargs={'pk': self.supplier.pk})


class DocumentDeleteView(LoginRequiredMixin, TenantAwareViewMixin, DeleteView):
    """Delete a supplier document."""
    model = SupplierDocument
    template_name = 'suppliers/document_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_detail', kwargs={'pk': self.object.supplier.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Document deleted successfully.')
        return super().delete(request, *args, **kwargs)
