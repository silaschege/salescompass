from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.db.models import Sum
from core.views import SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView, SalesCompassUpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import ExpenseReport, ExpenseLine, ExpenseCategory
from .forms import ExpenseReportForm, ExpenseLineForm, CorporateCardForm, ExpenseCategoryForm
from .services import ExpenseAccountingService, ApprovalService, PolicyService

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
        
        # Phase 2 Flags
        context['analytics_enabled'] = True
        
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
        
        # Policy Check (Pre-save validation)
        # Note: We create a temporary instance to validate
        temp_line = form.save(commit=False)
        temp_line.report = report
        temp_line.tenant = self.request.user.tenant
        
        violations = PolicyService.validate_line(temp_line)
        blocking_violations = [v['message'] for v in violations if v['action'] == 'block']
        warning_violations = [v['message'] for v in violations if v['action'] == 'warn']
        
        if blocking_violations:
            for msg in blocking_violations:
                messages.error(self.request, f"Policy Violation: {msg}")
            return self.form_invalid(form)
            
        if warning_violations:
            for msg in warning_violations:
                messages.warning(self.request, f"Policy Warning: {msg}")

        form.instance.report = report
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('expenses:report_detail', kwargs={'pk': self.kwargs['pk']})

class ExpenseReportSubmitView(View):
    def post(self, request, pk):
        report = get_object_or_404(ExpenseReport, pk=pk, employee=request.user)
        if report.status == 'draft' or report.status == 'rejected':
            # Check for blocking policies before submission
            is_blocked, warnings = PolicyService.check_report_policies(report)
            
            if is_blocked:
                messages.error(request, "Cannot submit report due to policy violations. Please fix blocked items.")
                for w in warnings:
                   messages.warning(request, w)
                return redirect('expenses:report_detail', pk=pk)

            ApprovalService.submit_report(report, request.user)
            messages.success(request, f"Expense report submitted. Status: {report.get_status_display()}")
            
        return redirect('expenses:report_detail', pk=pk)

class ExpenseReportApproveView(View):
    def post(self, request, pk):
        # Ideally check for permission based on ApprovalStep
        report = get_object_or_404(ExpenseReport, pk=pk)
        
        # Determine if user is allowed to approve
        # Logic: User must be the assigned approver OR have the required role
        # For MVP/Phase 1 execution, we bypass complex permission checks but implementation is ready
        
        if report.status in ['submitted', 'pending_approval']:
            ApprovalService.approve_step(report, request.user)
            messages.success(request, "Approval step completed.")
            
            if report.status == 'approved':
                 messages.success(request, "Report fully approved and accrued.")

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
        # Should filter by what the user can approve
        # user = self.request.user
        # return ExpenseReport.objects.filter(status='pending_approval', current_step__approver_user=user)
        # For broad visibility in execution phase:
        return super().get_queryset().filter(status__in=['submitted', 'pending_approval'])

class ExpenseCategoryListView(SalesCompassListView):
    model = ExpenseCategory
    template_name = 'expenses/category_list.html'
    context_object_name = 'categories'


# Phase 2 Views

class CorporateCardListView(SalesCompassListView):
    from .models import CorporateCard
    model = CorporateCard
    template_name = 'expenses/card_list.html'
    context_object_name = 'cards'

class CardTransactionImportView(View):
    def get(self, request):
        from .models import CorporateCard
        cards = CorporateCard.objects.filter(tenant=request.user.tenant, is_active=True)
        return render(request, 'expenses/card_import.html', {'cards': cards})

    def post(self, request):
        from .models import CorporateCard
        from .services import CardImportService
        
        card_id = request.POST.get('card_id')
        csv_file = request.FILES.get('csv_file')
        
        if not card_id or not csv_file:
            messages.error(request, "Please select a card and upload a CSV file.")
            return redirect('expenses:card_import')
            
        card = get_object_or_404(CorporateCard, pk=card_id, tenant=request.user.tenant)
        
        try:
            count = CardImportService.import_transactions_csv(csv_file, card)
            messages.success(request, f"Successfully imported {count} transactions.")
            
            # Trigger auto-match
            matches = CardImportService.auto_match_transactions(request.user.tenant)
            if matches > 0:
                messages.info(request, f"Auto-matched {matches} transactions to existing expenses.")
                
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
            
        return redirect('expenses:card_list')

from django.http import JsonResponse
class ExpenseAnalyticsDataView(View):
    def get(self, request):
        from .services import AnalyticsService
        tenant = request.user.tenant
        
        # Default last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=30)
        
        category_data = AnalyticsService.get_spend_by_category(tenant, start_date, end_date)
        trend_data = AnalyticsService.get_spend_trend(tenant, start_date, end_date)
        
        return JsonResponse({
            'by_category': list(category_data),
            'trend': list(trend_data)
        })

class ExpenseCategoryCreateView(SalesCompassCreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:category_list')
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class ExpenseCategoryUpdateView(SalesCompassUpdateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:category_list')
    success_message = "Category updated successfully."

class CorporateCardCreateView(SalesCompassCreateView):
    from .models import CorporateCard
    model = CorporateCard
    form_class = CorporateCardForm
    template_name = 'expenses/card_form.html'
    success_url = reverse_lazy('expenses:card_list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class CorporateCardUpdateView(SalesCompassUpdateView):
    from .models import CorporateCard
    model = CorporateCard
    form_class = CorporateCardForm
    template_name = 'expenses/card_form.html'
    success_url = reverse_lazy('expenses:card_list')
    success_message = "Corporate card updated successfully."
