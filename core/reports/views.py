from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.utils import timezone
from core.permissions import PermissionRequiredMixin
from .models import Report, ReportSchedule, ReportExport, DashboardWidget, EXPORT_FORMATS
from .forms import ReportForm, ReportScheduleForm, DashboardWidgetForm
from .utils import generate_report

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

class ReportListView(PermissionRequiredMixin, ListView):
    """
    List all reports with filtering and search capabilities.
    """
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    required_permission = 'reports:read'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by report type
        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_types'] = Report._meta.get_field('report_type').choices
        context['search_term'] = self.request.GET.get('search', '')
        return context


class ReportDetailView(PermissionRequiredMixin, DetailView):
    """
    Display detailed report information and preview.
    """
    model = Report
    template_name = 'reports/detail.html'
    context_object_name = 'report'
    required_permission = 'reports:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent exports for this report
        context['recent_exports'] = ReportExport.objects.filter(
            report=self.object
        ).order_by('-created_at')[:5]
        
        # Get active schedules for this report
        context['active_schedules'] = ReportSchedule.objects.filter(
            report=self.object,
            is_active=True
        )
        
        # Get available export formats
        context['export_formats'] = EXPORT_FORMATS
        
        return context


class ReportBuilderView(PermissionRequiredMixin, CreateView):
    """
    Create a new custom report with configuration builder.
    """
    model = Report
    form_class = ReportForm
    template_name = 'reports/builder.html'
    success_url = reverse_lazy('reports:list')
    required_permission = 'reports:write'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        messages.success(self.request, f"Report '{form.instance.name}' created successfully!")
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


class DashboardView(PermissionRequiredMixin, TemplateView):
    """
    Main reports dashboard with configurable widgets.
    """
    template_name = 'reports/dashboard.html'
    required_permission = 'reports:read'

# In your DashboardView.get_context_data()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
    
    # Get active dashboard widgets for current tenant
        widgets = DashboardWidget.objects.filter(
            is_active=True,
            report__tenant_id=getattr(user, 'tenant_id', None)
        ).select_related('report').order_by('position', 'order')
    
        # Group widgets by position with default empty lists
        widget_groups = {
            'main': [],
            'sidebar': [],
            'footer': []
        }
    
        for widget in widgets:
            if widget.position not in widget_groups:
                widget_groups[widget.position] = []
            widget_groups[widget.position].append(widget)
    
        context['widget_groups'] = widget_groups
        context['widget_types'] = DashboardWidget.WIDGET_TYPES
        return context


class DashboardWidgetUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update dashboard widget configuration.
    """
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'reports/widget_form.html'
    success_url = reverse_lazy('reports:dashboard')
    required_permission = 'reports:write'

    def form_valid(self, form):
        messages.success(self.request, f"Widget '{form.instance.name}' updated successfully!")
        return super().form_valid(form)

    def get_queryset(self):
        # Ensure user can only edit widgets in their tenant
        return DashboardWidget.objects.filter(
            report__tenant_id=getattr(self.request.user, 'tenant_id', None)
        )


class DashboardWidgetCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new dashboard widget.
    """
    model = DashboardWidget
    form_class = DashboardWidgetForm
    template_name = 'reports/widget_form.html'
    success_url = reverse_lazy('reports:dashboard')
    required_permission = 'reports:write'

    def form_valid(self, form):
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        messages.success(self.request, f"Widget '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class DashboardWidgetDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete a dashboard widget.
    """
    model = DashboardWidget
    template_name = 'reports/widget_confirm_delete.html'
    success_url = reverse_lazy('reports:dashboard')
    required_permission = 'reports:write'

    def delete(self, request, *args, **kwargs):
        widget = self.get_object()
        messages.success(request, f"Widget '{widget.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return DashboardWidget.objects.filter(
            report__tenant_id=getattr(self.request.user, 'tenant_id', None)
        )


class ReportScheduleCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a scheduled report delivery.
    """
    model = ReportSchedule
    form_class = ReportScheduleForm
    template_name = 'reports/schedule_form.html'
    success_url = reverse_lazy('reports:list')
    required_permission = 'reports:write'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Set tenant_id
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        
        # Set the next_run date based on frequency
        from datetime import timedelta
        now = timezone.now()
        frequency = form.cleaned_data['frequency']
        
        if frequency == 'daily':
            form.instance.next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            form.instance.next_run = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            form.instance.next_run = now + timedelta(days=30)
        else:  # quarterly
            form.instance.next_run = now + timedelta(days=90)
            
        messages.success(self.request, f"Report schedule created successfully!")
        return super().form_valid(form)


class ReportScheduleUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update a report schedule.
    """
    model = ReportSchedule
    form_class = ReportScheduleForm
    template_name = 'reports/schedule_form.html'
    success_url = reverse_lazy('reports:list')
    required_permission = 'reports:write'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return ReportSchedule.objects.filter(
            report__tenant_id=getattr(self.request.user, 'tenant_id', None)
        )


class ReportScheduleDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete a report schedule.
    """
    model = ReportSchedule
    template_name = 'reports/schedule_confirm_delete.html'
    success_url = reverse_lazy('reports:list')
    required_permission = 'reports:write'

    def delete(self, request, *args, **kwargs):
        schedule = self.get_object()
        messages.success(request, f"Report schedule '{schedule.report.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return ReportSchedule.objects.filter(
            report__tenant_id=getattr(self.request.user, 'tenant_id', None)
        )


class ReportDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete a report.
    """
    model = Report
    template_name = 'reports/report_confirm_delete.html'
    success_url = reverse_lazy('reports:list')
    required_permission = 'reports:write'

    def delete(self, request, *args, **kwargs):
        report = self.get_object()
        messages.success(request, f"Report '{report.name}' deleted successfully!")
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
            generated_by=request.user,
            tenant_id=getattr(request.user, 'tenant_id', None),
            status='completed'
        )
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error exporting report: {str(e)}")
        return redirect('reports:detail', pk=report_id)


class ReportExportListView(PermissionRequiredMixin, ListView):
    """
    List all report exports.
    """
    model = ReportExport
    template_name = 'reports/export_list.html'
    context_object_name = 'exports'
    paginate_by = 20
    required_permission = 'reports:read'

    def get_queryset(self):
        return super().get_queryset().select_related('report', 'generated_by').order_by('-created_at')


class ScheduledReportsView(PermissionRequiredMixin, ListView):
    """
    List all scheduled reports.
    """
    model = ReportSchedule
    template_name = 'reports/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 20
    required_permission = 'reports:read'

    def get_queryset(self):
        return super().get_queryset().select_related('report').order_by('-created_at')


class GenerateReportView(PermissionRequiredMixin, View):
    """
    AJAX endpoint to generate report data based on configuration.
    """
    required_permission = 'reports:read'

    def post(self, request, *args, **kwargs):
        import json
        from django.db.models import Count, Sum, Avg, F
        from django.db.models.functions import TruncMonth, TruncYear, TruncDay
        from django.apps import apps

        try:
            data = json.loads(request.body)
            entity = data.get('entity')
            filters = data.get('filters', [])
            group_by = data.get('group_by')
            chart_type = data.get('chart_type', 'bar')
            
            # Map entity to model
            model_map = {
                'account': 'accounts.Account',
                'opportunity': 'opportunities.Opportunity',
                'lead': 'leads.Lead',
                'case': 'support.Case',
                'task': 'tasks.Task',
            }
            
            model_path = model_map.get(entity)
            if not model_path:
                return JsonResponse({'error': 'Invalid entity'}, status=400)
            
            try:
                app_label, model_name = model_path.split('.')
                Model = apps.get_model(app_label, model_name)
            except LookupError:
                return JsonResponse({'error': f'Model {entity} not found'}, status=400)

            # Base QuerySet (Tenant filtered)
            queryset = Model.objects.filter(tenant_id=request.user.tenant_id)

            # Apply Filters
            for f in filters:
                field = f.get('field')
                operator = f.get('operator')
                value = f.get('value')
                
                if field and operator and value:
                    lookup = f"{field}__{operator}" if operator != 'exact' else field
                    queryset = queryset.filter(**{lookup: value})

            # Special Logic: Conversion Rate
            if entity == 'lead' and group_by == 'conversion_rate':
                # Calculate conversion rate (Converted / Total) * 100
                # We can group by source or just show overall
                # Let's assume we want conversion rate by Source if group_by is 'conversion_rate' 
                # Actually, usually we group by Source AND calculate conversion rate.
                # But our UI only has one group_by. 
                # Let's handle a special case: if chart_type is 'conversion' (we might need to add this)
                # OR if we just return two bars: Converted vs Total?
                
                # Better approach for this sprint:
                # If entity is Lead and we are grouping by something (e.g. Source),
                # we can return the conversion rate AS the value instead of count.
                pass # Logic handled below in aggregation

            # Aggregation / Grouping
            labels = []
            dataset_data = []
            label_suffix = ''
            
            if group_by:
                # Date Grouping Logic
                date_field = None
                trunc_func = None
                
                if '__month' in group_by:
                    date_field = group_by.replace('__month', '')
                    trunc_func = TruncMonth
                elif '__year' in group_by:
                    date_field = group_by.replace('__year', '')
                    trunc_func = TruncYear
                elif '__day' in group_by:
                    date_field = group_by.replace('__day', '')
                    trunc_func = TruncDay
                
                if date_field and trunc_func:
                    # Date grouping
                    # Check if we sum amount (Revenue Report)
                    if entity == 'opportunity' and hasattr(Model, 'amount'):
                        data = queryset.annotate(period=trunc_func(date_field)).values('period').annotate(total=Sum('amount')).order_by('period')
                        value_key = 'total'
                        label_suffix = ' (Revenue)'
                    else:
                        data = queryset.annotate(period=trunc_func(date_field)).values('period').annotate(count=Count('id')).order_by('period')
                        value_key = 'count'
                        label_suffix = ' (Count)'
                        
                    for item in data:
                        labels.append(item['period'].strftime('%Y-%m-%d') if item['period'] else 'None')
                        dataset_data.append(item[value_key])
                        
                else:
                    # Standard Categorical Grouping
                    
                    # Special Case: Lead Conversion Rate by Group
                    if entity == 'lead' and chart_type == 'conversion':
                        # We want conversion rate per group
                        # Count total per group
                        total_data = queryset.values(group_by).annotate(total=Count('id'))
                        # Count converted per group
                        converted_data = queryset.filter(status='converted').values(group_by).annotate(converted=Count('id'))
                        
                        # Merge
                        converted_map = {item[group_by]: item['converted'] for item in converted_data}
                        
                        for item in total_data:
                            group_val = item[group_by]
                            total = item['total']
                            converted = converted_map.get(group_val, 0)
                            rate = (converted / total * 100) if total > 0 else 0
                            
                            labels.append(str(group_val) if group_val is not None else 'None')
                            dataset_data.append(round(rate, 1))
                        
                        label_suffix = ' (Conversion Rate %)'
                        
                    else:
                        # Default Count/Sum logic
                        has_amount = any(f.name == 'amount' for f in Model._meta.get_fields())
                        
                        if has_amount and entity == 'opportunity':
                            data = queryset.values(group_by).annotate(total=Sum('amount')).order_by(group_by)
                            value_key = 'total'
                            label_suffix = ' (Value)'
                        else:
                            data = queryset.values(group_by).annotate(count=Count('id')).order_by(group_by)
                            value_key = 'count'
                            label_suffix = ' (Count)'

                        for item in data:
                            label_val = item.get(group_by)
                            labels.append(str(label_val) if label_val is not None else 'None')
                            dataset_data.append(item.get(value_key))
            else:
                # No grouping
                count = queryset.count()
                labels = ['Total']
                dataset_data = [count]
                label_suffix = ''

            # Format for Chart.js
            chart_data = {
                'labels': labels,
                'datasets': [{
                    'label': f"{entity.title()}{label_suffix}",
                    'data': dataset_data,
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
            }
            
            return JsonResponse(chart_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)