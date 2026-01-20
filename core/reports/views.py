from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import TemplateView
from django.views import View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from core.views import (
    TenantAwareViewMixin, SalesCompassListView, SalesCompassDetailView,
    SalesCompassCreateView, SalesCompassUpdateView, SalesCompassDeleteView
)
from .models import Report, ReportSchedule, ReportExport, EXPORT_FORMATS, WIDGET_TYPES, ReportSnapshot, ReportSubscription
from dashboard.models import DashboardWidget
from dashboard.forms import DashboardWidgetForm
from .forms import ReportForm, ReportScheduleForm
from .utils import generate_report, get_report_data
from services.business_metrics_service import BusinessMetricsService
import csv
import json
from datetime import datetime, timedelta
from sales.services import calculate_sales_metrics
from sales.models import SalesPerformanceMetric

 
def export_report(request, report_id):
    """
    Export a report in the specified format.
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:list')

    export_format = request.GET.get('format', 'csv')
    # Fix: Check if the export_format is in the list of available format keys
    if export_format not in [fmt[0] for fmt in EXPORT_FORMATS]:
        messages.error(request, "Invalid export format.")
        return redirect('reports:detail', pk=report_id)




class ReportListView(SalesCompassListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by report type
        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(report_name__icontains=search)

        return queryset.order_by('-report_created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_types'] = Report._meta.get_field('report_type').choices
        context['search_term'] = self.request.GET.get('search', '')
        return context


class ReportDetailView(SalesCompassDetailView):
    model = Report
    template_name = 'reports/detail.html'
    context_object_name = 'report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent exports for this report
        context['recent_exports'] = ReportExport.objects.filter(
            report=self.object
        ).order_by('-export_created_at')[:5]

        # Get active schedules for this report
        context['active_schedules'] = ReportSchedule.objects.filter(
            report=self.object,
            schedule_is_active=True
        )

        # Get available export formats
        context['export_formats'] = EXPORT_FORMATS

        # Get snapshots
        context['snapshots'] = ReportSnapshot.objects.filter(report=self.object).order_by('-snapshot_date')

        return context


class PublicReportView(SalesCompassDetailView):
    """
    View a report via a public token without login.
    """
    model = Report
    template_name = 'reports/public_report.html'
    context_object_name = 'report'
    slug_field = 'public_token'
    slug_url_kwarg = 'token'

    def get_queryset(self):
        return Report.objects.filter(is_public=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Generate data for the public view
        context['report_data'] = get_report_data(self.object.query_config)
        return context


class ReportSnapshotListView(SalesCompassListView):
    model = ReportSnapshot
    template_name = 'reports/snapshot_list.html'
    context_object_name = 'snapshots'

    def get_queryset(self):
        return super().get_queryset().filter(
            report_id=self.kwargs['report_id']
        ).select_related('report', 'created_by').order_by('-snapshot_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = get_object_or_404(Report, id=self.kwargs['report_id'], tenant_id=getattr(self.request.user, 'tenant_id', None))
        context['report'] = report
        
        # Handle single snapshot view
        snapshot_id = self.request.GET.get('snapshot')
        if snapshot_id:
            context['current_snapshot'] = get_object_or_404(ReportSnapshot, id=snapshot_id, report=report)
        
        # Handle comparison
        snap_a_id = self.request.GET.get('snap_a')
        snap_b_id = self.request.GET.get('snap_b')
        if snap_a_id and snap_b_id:
            snap_a = get_object_or_404(ReportSnapshot, id=snap_a_id, report=report)
            snap_b = get_object_or_404(ReportSnapshot, id=snap_b_id, report=report)
            context['is_comparison'] = True
            context['data_a'] = snap_a.snapshot_data
            context['data_b'] = snap_b.snapshot_data
            context['date_a'] = snap_a.snapshot_date.strftime('%Y-%m-%d %H:%M')
            context['date_b'] = snap_b.snapshot_date.strftime('%Y-%m-%d %H:%M')
        
        return context


class ReportSnapshotCreateView(LoginRequiredMixin, TenantAwareViewMixin, View):

    def post(self, request, report_id):
        report = get_object_or_404(Report, id=report_id, tenant_id=request.user.tenant_id)
        data = get_report_data(report.query_config)
        
        ReportSnapshot.objects.create(
            report=report,
            snapshot_data=data,
            created_by=request.user,
            tenant_id=report.tenant_id
        )
        messages.success(request, "Snapshot created successfully.")
        return redirect('reports:detail', pk=report_id)


class SubscriptionToggleView(LoginRequiredMixin, View):
    def post(self, request, report_id):
        report = get_object_or_404(Report, id=report_id, tenant_id=getattr(request.user, 'tenant_id', None))
        sub, created = ReportSubscription.objects.get_or_create(
            report=report,
            user=request.user,
            tenant_id=report.tenant_id
        )
        if not created:
            sub.is_active = not sub.is_active
            sub.save()
        
        status = "subscribed" if sub.is_active else "unsubscribed"
        messages.success(request, f"Successfully {status} from report.")
        return redirect('reports:detail', pk=report_id)


class ReportBuilderView(SalesCompassCreateView):
    model = Report
    form_class = ReportForm
    template_name = 'reports/builder.html'
    success_url = reverse_lazy('reports:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Report '{form.instance.report_name}' created successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Provide entity and field options for the builder
        context['entity_options'] = [
            {
                'value': 'account',
                'label': 'Accounts',
                'fields': ['name', 'industry', 'tier', 'health_score', 'esg_engagement', 'renewal_date']
            },
            {
                'value': 'opportunity',
                'label': 'Opportunities',
                'fields': ['name', 'amount', 'stage', 'weighted_value', 'esg_tagged', 'close_date']
            },
            {
                'value': 'lead',
                'label': 'Leads',
                'fields': ['first_name', 'last_name', 'company', 'lead_score', 'source', 'created_at']
            },
            {
                'value': 'case',
                'label': 'Cases',
                'fields': ['subject', 'priority', 'status', 'csat_score', 'created_at', 'resolved_at']
            },
        ]
        context['filter_options'] = {
            'account': ['industry', 'tier', 'health_score__gte', 'esg_engagement', 'renewal_date__gte'],
            'opportunity': ['stage', 'amount__gte', 'esg_tagged', 'close_date__gte'],
            'lead': ['source', 'lead_score__gte', 'created_at__gte'],
            'case': ['priority', 'status', 'csat_score__gte', 'created_at__gte'],
        }
        return context


class DashboardView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get active dashboard widgets for current tenant
        widgets = DashboardWidget.objects.filter(
            widget_is_active=True,
            tenant_id=user.tenant_id
        ).select_related('report').order_by('position', 'order')

        # Group widgets by position and fetch data
        widget_groups = {
            'main': [],
            'sidebar': [],
            'footer': []
        }

        for widget in widgets:
            if widget.widget_type in ['chart', 'table', 'trend']:
                try:
                    widget.report_data = get_report_data(widget.report.query_config)
                except Exception as e:
                    widget.report_data = {'error': str(e)}
            
            if widget.position not in widget_groups:
                widget_groups[widget.position] = []
            widget_groups[widget.position].append(widget)

        context['widget_groups'] = widget_groups
        context['widgets'] = widgets
        context['widget_types'] = WIDGET_TYPES
        return context


class DashboardWidgetUpdateView(SalesCompassUpdateView):
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'reports/widget_form.html'
    success_url = reverse_lazy('reports:dashboard')

    def form_valid(self, form):
        messages.success(self.request, f"Widget '{form.instance.widget_name}' updated successfully!")
        return super().form_valid(form)

    def get_queryset(self):
        # Ensure user can only edit widgets in their tenant
        return DashboardWidget.objects.filter(
            report__tenant_id=getattr(self.request.user, 'tenant_id', None)
        )


class DashboardWidgetCreateView(SalesCompassCreateView):
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'reports/widget_form.html'
    success_url = reverse_lazy('reports:dashboard')

    def form_valid(self, form):
        messages.success(self.request, f"Widget '{form.instance.widget_name}' created successfully!")
        return super().form_valid(form)


class DashboardWidgetDeleteView(SalesCompassDeleteView):
    model = DashboardWidget
    template_name = 'reports/widget_confirm_delete.html'
    success_url = reverse_lazy('reports:dashboard')

    def delete(self, request, *args, **kwargs):
        widget = self.get_object()
        messages.success(request, f"Widget '{widget.widget_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset()


class ReportScheduleCreateView(SalesCompassCreateView):
    model = ReportSchedule
    form_class = ReportScheduleForm
    template_name = 'reports/schedule_form.html'
    success_url = reverse_lazy('reports:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Set the next_run date based on frequency
        from datetime import timedelta
        now = timezone.now()
        frequency = form.cleaned_data['frequency']

        if frequency == 'daily':
            form.instance.next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            form.instance.next_run = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            form.instance.next_run = now + timedelta(days=30)  # Approximate
        elif frequency == 'quarterly':
            form.instance.next_run = now + timedelta(days=90)  # Approximate
        elif frequency == 'yearly':
            form.instance.next_run = now + timedelta(days=365)  # Approximate

        messages.success(self.request, f"Report schedule '{form.instance.schedule_name}' created successfully!")
        return super().form_valid(form)


class ReportScheduleUpdateView(SalesCompassUpdateView):
    model = ReportSchedule
    form_class = ReportScheduleForm
    template_name = 'reports/schedule_form.html'
    success_url = reverse_lazy('reports:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Update the next_run date based on the new frequency
        from datetime import timedelta
        now = timezone.now()
        frequency = form.cleaned_data['frequency']

        if frequency == 'daily':
            form.instance.next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            form.instance.next_run = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            form.instance.next_run = now + timedelta(days=30)  # Approximate
        elif frequency == 'quarterly':
            form.instance.next_run = now + timedelta(days=90)  # Approximate
        elif frequency == 'yearly':
            form.instance.next_run = now + timedelta(days=365)  # Approximate

        messages.success(self.request, f"Report schedule '{form.instance.schedule_name}' updated successfully!")
        return super().form_valid(form)

    def get_queryset(self):
        return super().get_queryset()


class ReportScheduleDeleteView(SalesCompassDeleteView):
    model = ReportSchedule
    template_name = 'reports/schedule_confirm_delete.html'
    success_url = reverse_lazy('reports:list')

    def delete(self, request, *args, **kwargs):
        schedule = self.get_object()
        messages.success(request, f"Report schedule '{schedule.schedule_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset()


class ReportUpdateView(SalesCompassUpdateView):
    model = Report
    form_class = ReportForm
    template_name = 'reports/edit.html'
    success_url = reverse_lazy('reports:list')

    def form_valid(self, form):
        messages.success(self.request, f"Report '{form.instance.report_name}' updated successfully!")
        return super().form_valid(form)

    def get_queryset(self):
        return super().get_queryset()


class ReportDeleteView(SalesCompassDeleteView):
    model = Report
    template_name = 'reports/report_confirm_delete.html'
    success_url = reverse_lazy('reports:list')

    def delete(self, request, *args, **kwargs):
        report = self.get_object()
        messages.success(request, f"Report '{report.report_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


def export_report(request, report_id):
    """
    Export a report in the specified format.
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:list')

    export_format = request.GET.get('format', 'csv')
    if export_format not in [fmt[0] for fmt in EXPORT_FORMATS]:
        messages.error(request, "Invalid export format.")
        return redirect('reports:detail', pk=report_id)

    try:
        report = get_object_or_404(Report, id=report_id)

        # Check if user has access to this report
        if report.tenant_id != getattr(request.user, 'tenant_id', None):
            messages.error(request, "Permission denied.")
            return redirect('reports:list')

        # Generate the report
        response = generate_report(report_id, export_format, request.user)

        # Create export record
        ReportExport.objects.create(
            report=report,
            export_format=export_format,
            created_by=request.user,
            tenant_id=getattr(request.user, 'tenant_id', None),
            status='completed'
        )

        return response

    except Exception as e:
        messages.error(request, f"Error exporting report: {str(e)}")
        return redirect('reports:detail', pk=report_id)


class ReportExportListView(SalesCompassListView):
    model = ReportExport
    template_name = 'reports/export_list.html'
    context_object_name = 'exports'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('report', 'created_by').order_by('-export_created_at')


class ScheduledReportsView(SalesCompassListView):
    model = ReportSchedule
    template_name = 'reports/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('report').order_by('-schedule_created_at')


class GenerateReportView(LoginRequiredMixin, TenantAwareViewMixin, View):

    def post(self, request, *args, **kwargs):
        import json
        from .utils import get_report_data

        try:
            data = json.loads(request.body)
            # Add tenant_id to config for filtering
            data['tenant_id'] = getattr(request.user, 'tenant_id', None)
            
            result = get_report_data(data)
            
            if 'error' in result:
                return JsonResponse({'error': result['error']}, status=400)
                
            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Business Metrics Export Functions
def export_clv_metrics(request):
    """
    Export CLV metrics to CSV
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_clv_metrics(tenant_id=tenant_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="clv_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Average CLV', metrics['avg_clv']])
    writer.writerow(['Total CLV', metrics['total_clv']])
    writer.writerow(['Average Order Value', metrics['avg_order_value']])
    writer.writerow(['Average Purchase Frequency', metrics['avg_purchase_frequency']])
    
    return response


def export_cac_metrics(request):
    """
    Export CAC metrics to CSV
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_cac_metrics(tenant_id=tenant_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cac_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Average CAC', metrics['avg_cac']])
    writer.writerow(['Total Spend', metrics['total_spend']])
    writer.writerow(['New Customers Count', metrics['new_customers_count']])
    writer.writerow(['Conversion Rate', f"{metrics['conversion_rate']:.2f}%"])
    
    return response


def export_sales_velocity_metrics(request):
    """
    Export sales velocity metrics to CSV
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_sales_velocity_metrics(tenant_id=tenant_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_velocity_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Average Sales Velocity', metrics['avg_sales_velocity']])
    writer.writerow(['Conversion Rate', f"{metrics['conversion_rate']:.2f}%"])
    writer.writerow(['Average Sales Cycle', metrics['avg_sales_cycle']])
    
    return response


def export_roi_metrics(request):
    """
    Export ROI metrics to CSV
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_roi_metrics(tenant_id=tenant_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="roi_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total CLV', metrics['total_clv']])
    writer.writerow(['Total CAC', metrics['total_cac']])
    writer.writerow(['ROI', f"{metrics['roi']:.2f}"])
    
    return response


def export_conversion_funnel_metrics(request):
    """
    Export conversion funnel metrics to CSV
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    tenant_id = getattr(request.user, 'tenant_id', None)
    metrics = BusinessMetricsService.calculate_conversion_funnel_metrics(tenant_id=tenant_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="conversion_funnel_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Leads', metrics['total_leads']])
    writer.writerow(['Qualified Leads', metrics['qualified_leads']])
    writer.writerow(['Converted Leads', metrics['converted_leads']])
    writer.writerow(['Total Opportunities', metrics['total_opportunities']])
    writer.writerow(['Won Opportunities', metrics['won_opportunities']])
    writer.writerow(['Lead to Qualified Rate', f"{metrics['lead_to_qualified_rate']:.2f}%"])
    writer.writerow(['Lead to Customer Rate', f"{metrics['lead_to_customer_rate']:.2f}%"])
    writer.writerow(['Opportunity to Won Rate', f"{metrics['opp_to_won_rate']:.2f}%"])
    
    return response


def export_all_metrics(request):
    """
    Export all business metrics to JSON
    """
    if not request.user.has_perm('reports:read'):
        messages.error(request, "Permission denied.")
        return redirect('reports:dashboard')

    tenant_id = getattr(request.user, 'tenant_id', None)
    
    clv_metrics = BusinessMetricsService.calculate_clv_metrics(tenant_id=tenant_id)
    cac_metrics = BusinessMetricsService.calculate_cac_metrics(tenant_id=tenant_id)
    sales_velocity_metrics = BusinessMetricsService.calculate_sales_velocity_metrics(tenant_id=tenant_id)
    roi_metrics = BusinessMetricsService.calculate_roi_metrics(tenant_id=tenant_id)
    funnel_metrics = BusinessMetricsService.calculate_conversion_funnel_metrics(tenant_id=tenant_id)
    
    all_metrics = {
        'clv_metrics': clv_metrics,
        'cac_metrics': cac_metrics,
        'sales_velocity_metrics': sales_velocity_metrics,
        'roi_metrics': roi_metrics,
        'funnel_metrics': funnel_metrics,
        'exported_at': datetime.now().isoformat()
    }
    
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="all_business_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    json.dump(all_metrics, response, indent=2)
    
    return response


class SalesAnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/sales_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Current Metrics
        metrics = calculate_sales_metrics(start_date, end_date)
        context['metrics'] = metrics
        
        # Historical Trend (Last 6 months simplified)
        trend_labels = []
        revenue_data = []
        win_rate_data = []
        
        for i in range(5, -1, -1):
            date_point = end_date - timedelta(days=i*30)
            # Find closest snapshot
            snapshot_rev = SalesPerformanceMetric.objects.filter(
                metric_name='revenue', 
                dimension='organization',
                date__lte=date_point
            ).order_by('-date').first()
            
            snapshot_win = SalesPerformanceMetric.objects.filter(
                metric_name='win_rate', 
                dimension='organization',
                date__lte=date_point
            ).order_by('-date').first()
            
            trend_labels.append(date_point.strftime('%b %Y'))
            revenue_data.append(float(snapshot_rev.value) if snapshot_rev else 0)
            win_rate_data.append(float(snapshot_win.value) if snapshot_win else 0)
            
        context['trend_labels'] = trend_labels
        context['revenue_trend'] = revenue_data
        context['win_rate_trend'] = win_rate_data
        
        return context
