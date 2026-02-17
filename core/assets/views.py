from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, View
from core.views import SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView, SalesCompassUpdateView
from django.urls import reverse_lazy
from django.db.models import Sum
from django.contrib import messages
from .models import FixedAsset, AssetCategory, Depreciation, AssetImpairment, AssetRevaluation, AssetDisposal, AssetVerification, AssetMaintenance, MaintenanceSchedule
from .forms import AssetForm, AssetCategoryForm, AssetImpairmentForm, AssetRevaluationForm, AssetDisposalForm, AssetVerificationForm, AssetMaintenanceForm, MaintenanceScheduleForm
from .services import AssetAccountingService, AssetDepreciationService, AssetService, AssetReportService

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['verifications'] = self.object.verifications.all().order_by('-verification_date')[:5]
        context['maintenance_records'] = self.object.maintenance_records.all().order_by('-service_date')[:5]
        context['schedules'] = self.object.maintenance_schedules.all()
        return context

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

class AssetDisposalCreateView(SalesCompassCreateView):
    model = AssetDisposal
    form_class = AssetDisposalForm
    template_name = 'assets/disposal_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        return context

    def form_valid(self, form):
        asset = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        try:
            AssetAccountingService.record_disposal(
                asset=asset,
                disposal_date=form.cleaned_data['disposal_date'],
                disposal_type=form.cleaned_data['disposal_type'],
                proceeds=form.cleaned_data['disposal_proceeds'],
                notes=form.cleaned_data['notes'],
                user=self.request.user
            )
            messages.success(self.request, f"Asset {asset.name} has been disposed.")
            return redirect(self.get_success_url())
        except Exception as e:
            form.add_error(None, f"Disposal failed: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('assets:asset_detail', kwargs={'pk': self.kwargs['asset_pk']})

class AssetRegisterReportView(SalesCompassListView):
    model = FixedAsset
    template_name = 'assets/asset_register_report.html'
    context_object_name = 'assets'

    def get_queryset(self):
        return super().get_queryset().select_related('category').order_by('asset_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_date'] = timezone.now().date()
        return context

class AssetVerificationCreateView(SalesCompassCreateView):
    model = AssetVerification
    form_class = AssetVerificationForm
    template_name = 'assets/verification_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset'] = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        return context

    def form_valid(self, form):
        asset = get_object_or_404(FixedAsset, pk=self.kwargs['asset_pk'], tenant=self.request.user.tenant)
        form.instance.asset = asset
        form.instance.tenant = self.request.user.tenant
        form.instance.verified_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('assets:asset_detail', kwargs={'pk': self.kwargs['asset_pk']})

class AssetQRCodeView(View):
    """
    Returns an SVG QR code for the asset.
    """
    def get(self, request, pk):
        from django.http import HttpResponse
        asset = get_object_or_404(FixedAsset, pk=pk, tenant=request.user.tenant)
        svg_data = AssetService.generate_qr_code(asset)
        return HttpResponse(svg_data, content_type="image/svg+xml")

class AssetMaintenanceCreateView(SalesCompassCreateView):
    model = AssetMaintenance
    form_class = AssetMaintenanceForm
    template_name = 'assets/maintenance_form.html'

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

class MaintenanceScheduleCreateView(SalesCompassCreateView):
    model = MaintenanceSchedule
    form_class = MaintenanceScheduleForm
    template_name = 'assets/schedule_form.html'

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

class AssetDisclosureReportView(TemplateView):
    template_name = 'assets/ifrs_disclosure_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        # Default to current fiscal year (mocked or from request)
        start_date = timezone.now().date().replace(month=1, day=1)
        end_date = timezone.now().date()
        
        context['report_data'] = AssetReportService.get_movement_schedule(tenant, start_date, end_date)
        context['start_date'] = start_date
        context['end_date'] = end_date
        return context

class MobileAssetAuditView(SalesCompassDetailView):
    """
    Mobile-optimized view for scanning QR and confirming physical presence.
    """
    model = FixedAsset
    template_name = 'assets/mobile_audit.html'
    context_object_name = 'asset'

class RunDepreciationActionView(View):
    """
    Triggers batch depreciation for the current month.
    """
    def post(self, request):
        try:
            runs = AssetDepreciationService.process_monthly_depreciation(request.user.tenant, request.user)
            messages.success(request, f"Depreciation processed for {len(runs)} assets.")
        except Exception as e:
            messages.error(request, f"Depreciation run failed: {str(e)}")
        return redirect('assets:dashboard')

