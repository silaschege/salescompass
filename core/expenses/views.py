from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.db.models import Sum
from core.views import SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import ExpenseReport, ExpenseLine, ExpenseCategory
from .forms import ExpenseReportForm, ExpenseLineForm
from .services import ExpenseAccountingService

class ExpensesDashboardView(TemplateView):
    template_name = 'expenses/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Personal Stats
        my_reports = ExpenseReport.objects.filter(employee=self.request.user)
        context['my_pending_amount'] = my_reports.filter(status='draft').aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Tenant Analytics (Manager View)
        all_reports = ExpenseReport.objects.filter(tenant=tenant)
        context['total_spent_month'] = all_reports.filter(
            status__in=['approved', 'paid'], 
            approved_date__gte=start_of_month
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        context['pending_approval_total'] = all_reports.filter(status='submitted').aggregate(total=Sum('total_amount'))['total'] or 0
        
        # CAPEX Tracking (IFRS focus)
        context['capex_year'] = ExpenseLine.objects.filter(
            report__tenant=tenant,
            is_capex=True,
            report__status__in=['approved', 'paid'],
            date__gte=start_of_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent activity
        context['recent_reports'] = all_reports.order_by('-created_at')[:5]
        
        return context

class ExpenseReportListView(SalesCompassListView):
    model = ExpenseReport
    template_name = 'expenses/report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        # Users see their own, managers might see all (simplified for now)
        return super().get_queryset().filter(employee=self.request.user)

class ExpenseReportCreateView(SalesCompassCreateView):
    model = ExpenseReport
    form_class = ExpenseReportForm
    template_name = 'expenses/report_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        form.instance.employee = self.request.user
        form.instance.tenant = self.request.user.tenant
        form.instance.status = 'draft'
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('expenses:report_detail', kwargs={'pk': self.object.pk})

class ExpenseReportDetailView(SalesCompassDetailView):
    model = ExpenseReport
    template_name = 'expenses/report_detail.html'
    context_object_name = 'report'

class ExpenseLineCreateView(SalesCompassCreateView):
    model = ExpenseLine
    form_class = ExpenseLineForm
    template_name = 'expenses/line_form.html'
    
    def get_initial(self):
        report = get_object_or_404(ExpenseReport, pk=self.kwargs['pk'])
        return {'report': report}

    def form_valid(self, form):
        report = get_object_or_404(ExpenseReport, pk=self.kwargs['pk'])
        form.instance.report = report
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('expenses:report_detail', kwargs={'pk': self.kwargs['pk']})

class ExpenseReportSubmitView(View):
    def post(self, request, pk):
        report = get_object_or_404(ExpenseReport, pk=pk, employee=request.user)
        if report.status == 'draft':
            report.status = 'submitted'
            report.submitted_date = timezone.now()
            report.save()
            messages.success(request, "Expense report submitted for approval.")
        return redirect('expenses:report_detail', pk=pk)

class ExpenseReportApproveView(View):
    def post(self, request, pk):
        # Ideally check for permission
        report = get_object_or_404(ExpenseReport, pk=pk)
        if report.status == 'submitted':
            report.status = 'approved'
            report.approved_by = request.user
            report.approved_date = timezone.now()
            report.save()
            
            # IFRS: Post Accrual to GL
            try:
                ExpenseAccountingService.post_accrual(report, request.user)
                messages.success(request, "Expense report approved and accrued to GL.")
            except Exception as e:
                messages.warning(request, f"Approved, but accounting accrual failed: {str(e)}")
                
        return redirect('expenses:report_detail', pk=pk)

class ExpenseReportPayView(View):
    """
    Settles the expense report liability.
    """
    def post(self, request, pk):
        report = get_object_or_404(ExpenseReport, pk=pk)
        if report.status == 'approved':
            try:
                ExpenseAccountingService.post_payment(report, request.user)
                report.status = 'paid'
                report.save()
                messages.success(request, "Expense report settled and paid.")
            except Exception as e:
                messages.error(request, f"Payment settlement failed: {str(e)}")
                
        return redirect('expenses:report_detail', pk=pk)

class ExpenseApprovalInboxView(SalesCompassListView):
    model = ExpenseReport
    template_name = 'expenses/approval_workflow.html'
    context_object_name = 'pending_reports'
    
    def get_queryset(self):
        return super().get_queryset().filter(status='submitted')

class ExpenseCategoryListView(SalesCompassListView):
    model = ExpenseCategory
    template_name = 'expenses/category_list.html'
    context_object_name = 'categories'
