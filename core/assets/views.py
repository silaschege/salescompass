from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from core.views import SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView, SalesCompassUpdateView
from django.urls import reverse_lazy
from django.db.models import Sum
from django.contrib import messages
from .models import FixedAsset, AssetCategory, Depreciation, AssetImpairment, AssetRevaluation
from .forms import AssetForm, AssetCategoryForm, AssetImpairmentForm, AssetRevaluationForm

class AssetsDashboardView(TemplateView):
    template_name = 'assets/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        assets = FixedAsset.objects.filter(tenant=tenant, status='active')
        context['total_assets'] = assets.count()
        context['total_value'] = assets.aggregate(val=Sum('current_value'))['val'] or 0
        context['recent_assets'] = assets.select_related('category').order_by('-created_at')[:5]
        return context

class AssetListView(SalesCompassListView):
    model = FixedAsset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'

class AssetCreateView(SalesCompassCreateView):
    model = FixedAsset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('assets:asset_list')
    success_message = "Asset added successfully."

class AssetUpdateView(SalesCompassUpdateView):
    model = FixedAsset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('assets:asset_list')
    success_message = "Asset updated successfully."

class AssetDetailView(SalesCompassDetailView):
    model = FixedAsset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'

class AssetDepreciationScheduleView(SalesCompassDetailView):
    """
    View to show and calculate the depreciation schedule for an asset.
    """
    model = FixedAsset
    template_name = 'assets/depreciation_schedule.html'
    context_object_name = 'asset'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object
        
        # Calculate theoretical schedule
        schedule = []
        
        # Show past depreciations (actual)
        actuals = asset.depreciations.all().order_by('date')
        for dep in actuals:
            schedule.append({
                'date': dep.date,
                'type': 'Actual',
                'amount': dep.amount,
                'remaining': asset.purchase_cost - asset.depreciations.filter(date__lte=dep.date).aggregate(s=Sum('amount'))['s']
            })
            
        context['schedule'] = schedule
        return context

# --- Asset Categories ---

class CategoryListView(SalesCompassListView):
    model = AssetCategory
    template_name = 'assets/category_list.html'
    context_object_name = 'categories'

class CategoryCreateView(SalesCompassCreateView):
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/category_form.html'
    success_url = reverse_lazy('assets:category_list')
    success_message = "Asset category created."

class CategoryUpdateView(SalesCompassUpdateView):
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/category_form.html'
    success_url = reverse_lazy('assets:category_list')
    success_message = "Asset category updated."

class AssetRevaluationCreateView(SalesCompassCreateView):
    model = AssetRevaluation
    form_class = AssetRevaluationForm
    template_name = 'assets/revaluation_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        return context

    def form_valid(self, form):
        asset = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        form.instance.asset = asset
        form.instance.tenant = self.request.user.tenant
        # Calculate adjustment
        form.instance.adjustment_amount = form.cleaned_data['new_fair_value'] - asset.current_value
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('assets:asset_detail', kwargs={'pk': self.kwargs['asset_pk']})

class AssetImpairmentCreateView(SalesCompassCreateView):
    model = AssetImpairment
    form_class = AssetImpairmentForm
    template_name = 'assets/impairment_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        return context

    def form_valid(self, form):
        asset = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        form.instance.asset = asset
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('assets:asset_detail', kwargs={'pk': self.kwargs['asset_pk']})

class RunDepreciationActionView(View):
    """
    Triggers batch depreciation for the current month.
    """
    def post(self, request):
        from .services import AssetDepreciationService
        try:
            runs = AssetDepreciationService.process_monthly_depreciation(request.user.tenant, request.user)
            messages.success(request, f"Depreciation processed for {len(runs)} assets.")
        except Exception as e:
            messages.error(request, f"Depreciation run failed: {str(e)}")
        return redirect('assets:dashboard')

