from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from tenants.views import TenantAwareViewMixin
from core.views import SalesCompassListView, SalesCompassCreateView, SalesCompassUpdateView, SalesCompassDetailView, SalesCompassDeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import (
    ChartOfAccount, FiscalYear, FiscalPeriod,
    JournalEntry, JournalEntryLine, BankReconciliation,
    Budget, RecurringJournalEntry, AccountingIntegration,
    TaxRate, TaxRule, Currency, ExchangeRate, 
    CustomFinancialReport, BankAPIConfig
) 
from .forms import (
    ChartOfAccountForm, JournalEntryForm, 
    BudgetForm, RecurringJournalEntryForm, 
    AccountingIntegrationForm, FiscalYearForm,
    JournalEntryLineFormSet, TaxRateForm, TaxRuleForm,
    BankReconciliationForm, CurrencyForm, ExchangeRateForm,
    CustomFinancialReportForm, BankAPIConfigForm
)
from decimal import Decimal
from django.db import models

# --- Dashboard ---

class AccountingDashboardView(TemplateView):
    template_name = 'accounting/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Cash on Hand
        cash_balance = ChartOfAccount.objects.filter(
            tenant=tenant, is_bank_account=True
        ).aggregate(total=Sum('current_balance'))['total'] or 0
        
        # AR & AP
        ar_balance = ChartOfAccount.objects.filter(
            tenant=tenant, 
            account_type__in=['asset', 'asset_current'], 
            account_name__icontains='receivable'
        ).aggregate(total=Sum('current_balance'))['total'] or 0
        
        ap_balance = ChartOfAccount.objects.filter(
            tenant=tenant, 
            account_type__in=['liability', 'liability_current'], 
            account_name__icontains='payable'
        ).aggregate(total=Sum('current_balance'))['total'] or 0
        
        # Net Profit
        revenue = ChartOfAccount.objects.filter(
            tenant=tenant, account_type='revenue'
        ).aggregate(total=Sum('current_balance'))['total'] or 0
        
        expenses = ChartOfAccount.objects.filter(
            tenant=tenant, 
            account_type__in=['expense', 'cost_of_sales', 'other_expense']
        ).aggregate(total=Sum('current_balance'))['total'] or 0
        
        net_profit = revenue - expenses
        
        # New Context Data
        context['recent_journals'] = JournalEntry.objects.filter(
            tenant=tenant
        ).order_by('-created_at')[:5]
        
        # Budget Progress (Top 3)
        from .models import Budget
        context['top_budgets'] = Budget.objects.filter(
            tenant=tenant
        ).select_related('account', 'fiscal_year')[:3]
        
        # Alerts
        context['unbalanced_journals'] = JournalEntry.objects.filter(
            tenant=tenant, status='draft'
        ).count()
        
        context['cash_balance'] = cash_balance
        context['ar_balance'] = ar_balance
        context['ap_balance'] = ap_balance
        context['net_profit'] = net_profit
        
        return context

# --- Chart of Accounts ---

class ChartOfAccountListView(SalesCompassListView):
    model = ChartOfAccount
    template_name = 'accounting/coa_list.html'
    context_object_name = 'accounts'
    
    def get_queryset(self):
        # Already filtered by tenant via SalesCompassListView
        return super().get_queryset().order_by('account_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_accounts'] = self.get_queryset().exists()
        return context

class AccountingSetupView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        from .setup_service import AccountingSetupService
        try:
            AccountingSetupService.setup_tenant(request.user.tenant)
            messages.success(request, "Default accounts and integration rules initialized successfully.")
        except Exception as e:
            messages.error(request, f"Error initializing accounts: {str(e)}")
        return redirect('accounting:coa_list')

class ChartOfAccountCreateView(SalesCompassCreateView):
    model = ChartOfAccount
    form_class = ChartOfAccountForm
    template_name = 'accounting/coa_form.html'
    success_url = reverse_lazy('accounting:coa_list')
    success_message = "Account created successfully."

class ChartOfAccountUpdateView(SalesCompassUpdateView):
    model = ChartOfAccount
    form_class = ChartOfAccountForm
    template_name = 'accounting/coa_form.html'
    success_url = reverse_lazy('accounting:coa_list')
    success_message = "Account updated successfully."

class ChartOfAccountDetailView(SalesCompassDetailView):
    model = ChartOfAccount
    template_name = 'accounting/coa_detail.html'
    context_object_name = 'account'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.object
        
        # Calculate Ledger entries
        lines = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__status='posted',
            tenant=self.request.user.tenant
        ).select_related('journal_entry').order_by('journal_entry__entry_date', 'id')
        
        balance = 0
        ledger_entries = []
        for line in lines:
            if account.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                balance += line.debit - line.credit
            else:
                balance += line.credit - line.debit
            
            ledger_entries.append({
                'date': line.journal_entry.entry_date,
                'journal_id': line.journal_entry.id,
                'entry_number': line.journal_entry.entry_number,
                'description': line.description or line.journal_entry.description,
                'debit': line.debit,
                'credit': line.credit,
                'balance': balance
            })
            
        context['ledger_entries'] = ledger_entries[::-1] # Show most recent first
        return context

# --- Journal Entries ---



class JournalEntryListView(SalesCompassListView):
    model = JournalEntry
    template_name = 'accounting/journal_list.html'
    context_object_name = 'journals'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('created_by', 'currency').prefetch_related('lines')
        
        # Add filtering options
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(entry_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(entry_date__lte=date_to)
        if search:
            queryset = queryset.filter(
                models.Q(entry_number__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(reference__icontains=search)
            )
        
        return queryset.order_by('-entry_date', '-created_at')

class JournalEntryCreateView(SalesCompassCreateView):

    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'accounting/journal_form.html'
    success_url = reverse_lazy('accounting:journal_list')
    success_message = "Journal entry created successfully."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We'll handle lines via JS or FormSet in the template
        return context

class JournalEntryDetailView(SalesCompassDetailView):
    model = JournalEntry
    template_name = 'accounting/journal_detail.html'
    context_object_name = 'journal'
    
    def get_queryset(self):
        return super().get_queryset().select_related('created_by', 'posted_by', 'currency').prefetch_related('lines__account')

class JournalEntryPostView(SalesCompassDetailView):
    model = JournalEntry
    
    def post(self, request, *args, **kwargs):
        journal = self.get_object()
        from .services import JournalService
        
        try:
            JournalService.post_journal_entry(journal, request.user)
            messages.success(request, f"Journal {journal.entry_number} posted successfully.")
        except ValueError as e:
            messages.error(request, str(e))
            
        return redirect('accounting:journal_detail', pk=journal.pk)

# --- Reports ---

class TrialBalanceView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/trial_balance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .services import ReportService
        as_of_date = self.request.GET.get('date')
        if as_of_date:
            from django.utils.dateparse import parse_date
            as_of_date = parse_date(as_of_date)
        else:
             as_of_date = timezone.now().date()

        tb_data = ReportService.get_trial_balance(self.request.user.tenant, as_of_date)
        context.update(tb_data)
        context['as_of_date'] = as_of_date
        return context

class GeneralLedgerView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/general_ledger.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        account_id = self.request.GET.get('account_id')
        fiscal_year_id = self.request.GET.get('fiscal_year')
        
        # Determine Date Range
        if fiscal_year_id:
            fiscal_year = get_object_or_404(FiscalYear, id=fiscal_year_id, tenant=tenant)
            current_start_date = fiscal_year.start_date
            current_end_date = fiscal_year.end_date
            context['selected_fiscal_year'] = fiscal_year
        else:
            # Default to provided implementation or current year/month fallback could happen in template or here
            # For now stick to strict user input for dates if no FY selected
            if start_date:
                from django.utils.dateparse import parse_date
                current_start_date = parse_date(start_date)
            else:
                current_start_date = None
            
            if end_date:
                from django.utils.dateparse import parse_date
                current_end_date = parse_date(end_date)
            else:
                current_end_date = None

        # Update context for form
        context['accounts'] = ChartOfAccount.objects.filter(tenant=tenant).order_by('account_code')
        context['fiscal_years'] = FiscalYear.objects.filter(tenant=tenant).order_by('-start_date')
        context['start_date'] = current_start_date
        context['end_date'] = current_end_date
        
        # Accounts to Process
        if account_id:
            accounts = ChartOfAccount.objects.filter(id=account_id, tenant=tenant)
            context['selected_account_id'] = int(account_id)
        else:
            # Load all accounts if none selected, but might be heavy. 
            # Ideally user should usually select one, but requirement implies supporting "All".
            # Let's filter only those with transactions to be efficient?
            # For now, let's grab all active accounts.
            accounts = ChartOfAccount.objects.filter(tenant=tenant).order_by('account_code')

        report_data = []

        for account in accounts:
            # Base queryset
            queryset = JournalEntryLine.objects.filter(
                tenant=tenant,
                account=account,
                journal_entry__status='posted'
            ).select_related('journal_entry').order_by('journal_entry__entry_date', 'journal_entry__created_at')
            
            # Apply filters
            if current_start_date:
                queryset = queryset.filter(journal_entry__entry_date__gte=current_start_date)
            if current_end_date:
                queryset = queryset.filter(journal_entry__entry_date__lte=current_end_date)

            entries = []
            
            # Opening Balance Calculation
            running_balance = 0
            if current_start_date:
                opening_lines = JournalEntryLine.objects.filter(
                    tenant=tenant,
                    account=account,
                    journal_entry__status='posted',
                    journal_entry__entry_date__lt=current_start_date
                )
                op_debit = opening_lines.aggregate(s=Sum('debit'))['s'] or 0
                op_credit = opening_lines.aggregate(s=Sum('credit'))['s'] or 0
                
                if account.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                    running_balance = op_debit - op_credit
                else:
                    running_balance = op_credit - op_debit
            
            opening_balance = running_balance
            
            # Retrieve lines
            # Use iterator to save memory if large
            lines_data = list(queryset) 
            
            if not lines_data and opening_balance == 0:
                # Skip accounts with no activity and 0 opening balance if "All Accounts" is selected?
                # Maybe keeping them is better for completeness if specific account selected.
                if not account_id:
                   continue

            for line in lines_data:
                if account.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                    running_balance += (line.debit - line.credit)
                else:
                    running_balance += (line.credit - line.debit)
                    
                entries.append({
                    'date': line.journal_entry.entry_date,
                    'number': line.journal_entry.entry_number,
                    'journal_id': line.journal_entry.id, # Added for linking
                    'description': line.description or line.journal_entry.description,
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': running_balance
                })
            
            report_data.append({
                'account': account,
                'opening_balance': opening_balance,
                'entries': entries,
                'closing_balance': running_balance
            })

        context['report_data'] = report_data
        return context

    def get(self, request, *args, **kwargs):
        if request.GET.get('format') == 'csv':
            return self.export_csv(request)
        return super().get(request, *args, **kwargs)

    def export_csv(self, request):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="general_ledger.csv"'

        writer = csv.writer(response)
        writer.writerow(['General Ledger Report'])
        writer.writerow([])
        
        # Reuse context logic
        context = self.get_context_data()
        report_data = context.get('report_data', [])
        start_date = context.get('start_date')
        end_date = context.get('end_date')
        
        writer.writerow([f"Period: {start_date or 'Start'} to {end_date or 'End'}"])
        writer.writerow([])

        for data in report_data:
            account = data['account']
            writer.writerow([f"Account: {account.account_code} - {account.account_name}"])
            writer.writerow(['Date', 'Number', 'Description', 'Debit', 'Credit', 'Balance'])
            
            writer.writerow(['', '', 'Opening Balance', '', '', data['opening_balance']])
            
            for entry in data['entries']:
                writer.writerow([
                    entry['date'],
                    entry['number'],
                    entry['description'],
                    entry['debit'],
                    entry['credit'],
                    entry['balance']
                ])
                
            writer.writerow(['', '', 'Closing Balance', '', '', data['closing_balance']])
            writer.writerow([]) # Empty line between accounts
            
        return response

class IncomeStatementView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/income_statement.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .services import ReportService
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            from django.utils.dateparse import parse_date
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
        
        data = ReportService.get_income_statement(self.request.user.tenant, start_date, end_date)
        context.update(data)
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        return context

class BalanceSheetView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/balance_sheet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .services import ReportService
        as_of_date = self.request.GET.get('date')
        if as_of_date:
            from django.utils.dateparse import parse_date
            as_of_date = parse_date(as_of_date)
        else:
             as_of_date = timezone.now().date()
             
        data = ReportService.get_balance_sheet(self.request.user.tenant, as_of_date)
        context.update(data)
        context['as_of_date'] = as_of_date
        return context

class CashFlowView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/cash_flow.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .services import ReportService
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            from django.utils.dateparse import parse_date
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            
        data = ReportService.get_cash_flow_statement(self.request.user.tenant, start_date, end_date)
        context.update(data)
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        return context

# --- Reconciliations ---

class ReconciliationListView(SalesCompassListView):
    model = BankReconciliation
    template_name = 'accounting/reconciliation_list.html'
    context_object_name = 'reconciliations'

class ReconciliationCreateView(SalesCompassCreateView):
    model = BankReconciliation
    form_class = BankReconciliationForm
    template_name = 'accounting/reconciliation_form.html'
    success_url = reverse_lazy('accounting:reconciliation_list')
    success_message = "Reconciliation started successfully."
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.reconciled_by = self.request.user
        if form.instance.status == 'completed':
            form.instance.reconciled_at = timezone.now()
        return super().form_valid(form)

class ReconciliationUpdateView(SalesCompassUpdateView):
    model = BankReconciliation
    form_class = BankReconciliationForm
    template_name = 'accounting/reconciliation_form.html'
    success_url = reverse_lazy('accounting:reconciliation_list')
    success_message = "Reconciliation updated successfully."
    
    def form_valid(self, form):
        if form.instance.status == 'completed' and not form.instance.reconciled_at:
            form.instance.reconciled_at = timezone.now()
        return super().form_valid(form)

# --- Budgets ---

class BudgetListView(SalesCompassListView):
    model = Budget
    template_name = 'accounting/budget_list.html'
    context_object_name = 'budgets'

class BudgetCreateView(SalesCompassCreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'accounting/budget_form.html'
    success_url = reverse_lazy('accounting:budget_list')
    success_message = "Budget created successfully."

class BudgetUpdateView(SalesCompassUpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'accounting/budget_form.html'
    success_url = reverse_lazy('accounting:budget_list')
    success_message = "Budget updated successfully."

# --- Recurring Journals ---

class RecurringJournalListView(SalesCompassListView):
    model = RecurringJournalEntry
    template_name = 'accounting/recurring_journal_list.html'
    context_object_name = 'recurring_journals'

class RecurringJournalCreateView(SalesCompassCreateView):
    model = RecurringJournalEntry
    form_class = RecurringJournalEntryForm
    template_name = 'accounting/recurring_journal_form.html'
    success_url = reverse_lazy('accounting:recurring_journal_list')
    success_message = "Recurring journal template created."

class RecurringJournalUpdateView(SalesCompassUpdateView):
    model = RecurringJournalEntry
    form_class = RecurringJournalEntryForm
    template_name = 'accounting/recurring_journal_form.html'
    success_url = reverse_lazy('accounting:recurring_journal_list')
    success_message = "Recurring journal template updated."

# --- Accounting Integrations ---

class IntegrationListView(SalesCompassListView):
    model = AccountingIntegration
    template_name = 'accounting/integration_list.html'
    context_object_name = 'integrations'

class IntegrationCreateView(SalesCompassCreateView):
    model = AccountingIntegration
    form_class = AccountingIntegrationForm
    template_name = 'accounting/integration_form.html'
    success_url = reverse_lazy('accounting:integration_list')
    success_message = "Integration rule created."

class IntegrationUpdateView(SalesCompassUpdateView):
    model = AccountingIntegration
    form_class = AccountingIntegrationForm
    template_name = 'accounting/integration_form.html'
    success_url = reverse_lazy('accounting:integration_list')
    success_message = "Integration rule updated."

# --- Fiscal Management ---

class FiscalYearListView(SalesCompassListView):
    model = FiscalYear
    template_name = 'accounting/fiscal_year_list.html'
    context_object_name = 'fiscal_years'

class FiscalYearCreateView(SalesCompassCreateView):
    model = FiscalYear
    form_class = FiscalYearForm
    template_name = 'accounting/fiscal_year_form.html'
    success_url = reverse_lazy('accounting:fiscal_year_list')
    success_message = "Fiscal year created."

class FiscalYearUpdateView(SalesCompassUpdateView):
    model = FiscalYear
    form_class = FiscalYearForm
    template_name = 'accounting/fiscal_year_form.html'
    success_url = reverse_lazy('accounting:fiscal_year_list')
    success_message = "Fiscal year updated."

class FiscalPeriodCloseView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/fiscal_management/close_period.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = get_object_or_404(FiscalPeriod, id=self.kwargs['pk'], tenant=self.request.user.tenant)
        context['period'] = period
        
        # Checklist requirements
        context['unposted_journals'] = JournalEntry.objects.filter(
            tenant=self.request.user.tenant,
            entry_date__range=(period.start_date, period.end_date),
            status='draft'
        ).count()
        
        return context

    def post(self, request, *args, **kwargs):
        period = get_object_or_404(FiscalPeriod, id=self.kwargs['pk'], tenant=self.request.user.tenant)
        
        # Validate - e.g., no draft entries
        if JournalEntry.objects.filter(tenant=request.user.tenant, entry_date__range=(period.start_date, period.end_date), status='draft').exists():
            messages.error(request, "Cannot close period with draft journal entries.")
            return redirect('accounting:close_period', pk=period.pk)
            
        period.is_closed = True
        period.save()
        messages.success(request, f"Period {period.name} closed successfully.")
        return redirect('accounting:fiscal_year_list') # Or wherever appropriate

# --- Tax Management ---

class TaxRateListView(SalesCompassListView):
    model = TaxRate
    template_name = 'accounting/tax_rate_list.html'
    context_object_name = 'tax_rates'

class TaxRateCreateView(SalesCompassCreateView):
    model = TaxRate
    form_class = TaxRateForm
    template_name = 'accounting/tax_rate_form.html'
    success_url = reverse_lazy('accounting:tax_rate_list')
    success_message = "Tax rate created successfully."

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class TaxRateUpdateView(SalesCompassUpdateView):
    model = TaxRate
    form_class = TaxRateForm
    template_name = 'accounting/tax_rate_form.html'
    success_url = reverse_lazy('accounting:tax_rate_list')
    success_message = "Tax rate updated successfully."

class TaxRateDeleteView(SalesCompassDeleteView):
    model = TaxRate
    template_name = 'accounting/tax_rate_confirm_delete.html'
    success_url = reverse_lazy('accounting:tax_rate_list')

class TaxRuleListView(SalesCompassListView):
    model = TaxRule
    template_name = 'accounting/tax_rule_list.html'
    context_object_name = 'tax_rules'

class TaxRuleCreateView(SalesCompassCreateView):
    model = TaxRule
    form_class = TaxRuleForm
    template_name = 'accounting/tax_rule_form.html'
    success_url = reverse_lazy('accounting:tax_rule_list')
    success_message = "Tax rule created successfully."

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)

class TaxRuleUpdateView(SalesCompassUpdateView):
    model = TaxRule
    form_class = TaxRuleForm
    template_name = 'accounting/tax_rule_form.html'
    success_url = reverse_lazy('accounting:tax_rule_list')
    success_message = "Tax rule updated successfully."

class TaxRuleDeleteView(SalesCompassDeleteView):
    model = TaxRule
    template_name = 'accounting/tax_rule_confirm_delete.html'
    success_url = reverse_lazy('accounting:tax_rule_list')

# --- Bank Statement Management ---

from .models import BankStatement, BankStatementLine
from .forms import BankStatementImportForm
from .services import BankService

class BankStatementListView(SalesCompassListView):
    model = BankStatement
    template_name = 'accounting/bank_statement_list.html'
    context_object_name = 'statements'

class BankStatementImportView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/bank_statement_import.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BankStatementImportForm(tenant=self.request.user.tenant)
        return context

    def post(self, request, *args, **kwargs):
        form = BankStatementImportForm(request.POST, request.FILES, tenant=request.user.tenant)
        if form.is_valid():
            account = form.cleaned_data['account']
            file = request.FILES['file']
            
            try:
                statement = BankService.import_statement(
                    tenant=request.user.tenant,
                    account=account,
                    file_obj=file,
                    filename=file.name
                )
                if statement:
                    messages.success(request, f"Statement imported successfully: {len(statement.lines.all())} lines found.")
                    return redirect('accounting:statement_detail', pk=statement.pk)
                else:
                    messages.error(request, "Failed to parse statement. Please check the format.")
            except Exception as e:
                messages.error(request, f"Error importing statement: {str(e)}")
        
        return self.render_to_response(self.get_context_data(form=form))

class BankStatementDetailView(SalesCompassDetailView):
    """
    This is the main reconciliation interface for a statement.
    """
    model = BankStatement
    template_name = 'accounting/reconciliation_detail.html'
    context_object_name = 'statement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        statement = self.object
        
        # Group lines by reconciled status
        lines = statement.lines.all().order_by('date', 'id')
        reconciled_count = 0
        for line in lines:
            if not line.is_reconciled:
                line.suggestions = BankService.suggest_matches(line)
            else:
                reconciled_count += 1
        
        context['statement_lines'] = lines
        context['reconciled_count'] = reconciled_count
        context['total_count'] = lines.count()
        context['progress_percentage'] = int((reconciled_count / lines.count() * 100)) if lines.count() > 0 else 0
        return context

class VATReturnView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/vat_return.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .services import ReportService
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            from django.utils.dateparse import parse_date
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            
        data = ReportService.get_vat_return(self.request.user.tenant, start_date, end_date)
        context.update(data)
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        return context

class BankStatementMatchView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    """
    Endpoint to process a match between a bank line and a journal line.
    """
    def post(self, request, *args, **kwargs):
        bank_line_id = request.POST.get('bank_line_id')
        journal_line_id = request.POST.get('journal_line_id')
        
        bank_line = get_object_or_404(BankStatementLine, id=bank_line_id, tenant=request.user.tenant)
        journal_line = get_object_or_404(JournalEntryLine, id=journal_line_id, tenant=request.user.tenant)
        
        try:
            BankService.reconcile(bank_line, journal_line)
            messages.success(request, "Line reconciled successfully.")
        except ValueError as e:
            messages.error(request, str(e))
            
        return redirect('accounting:statement_detail', pk=bank_line.statement.pk)

# --- Multi-currency Management ---

class CurrencyListView(SalesCompassListView):
    model = Currency
    template_name = 'accounting/currency_list.html'
    context_object_name = 'currencies'

class CurrencyCreateView(SalesCompassCreateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'accounting/currency_form.html'
    success_url = reverse_lazy('accounting:currency_list')
    success_message = "Currency added successfully."

class CurrencyUpdateView(SalesCompassUpdateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'accounting/currency_form.html'
    success_url = reverse_lazy('accounting:currency_list')
    success_message = "Currency updated successfully."

class ExchangeRateListView(SalesCompassListView):
    model = ExchangeRate
    template_name = 'accounting/exchange_rate_list.html'
    context_object_name = 'rates'

class ExchangeRateCreateView(SalesCompassCreateView):
    model = ExchangeRate
    form_class = ExchangeRateForm
    template_name = 'accounting/exchange_rate_form.html'
    success_url = reverse_lazy('accounting:exchange_rate_list')
    success_message = "Exchange rate recorded successfully."

# --- Custom Financial Reports ---

class CustomReportListView(SalesCompassListView):
    model = CustomFinancialReport
    template_name = 'accounting/reports/custom_report_list.html'
    context_object_name = 'reports'

class CustomReportCreateView(SalesCompassCreateView):
    model = CustomFinancialReport
    form_class = CustomFinancialReportForm
    template_name = 'accounting/reports/custom_report_form.html'
    success_url = reverse_lazy('accounting:custom_report_list')
    success_message = "Custom report defined successfully."

class CustomReportUpdateView(SalesCompassUpdateView):
    model = CustomFinancialReport
    form_class = CustomFinancialReportForm
    template_name = 'accounting/reports/custom_report_form.html'
    success_url = reverse_lazy('accounting:custom_report_list')
    success_message = "Custom report definition updated."

class CustomReportRunView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/custom_report_run.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = get_object_or_404(CustomFinancialReport, id=self.kwargs['pk'], tenant=self.request.user.tenant)
        from .services import ReportService
        
        # Custom report generation logic
        as_of_date = self.request.GET.get('date', timezone.now().date())
        if isinstance(as_of_date, str):
            from django.utils.dateparse import parse_date
            as_of_date = parse_date(as_of_date) or timezone.now().date()
            
        context['report'] = report
        context['as_of_date'] = as_of_date
        context['report_data'] = ReportService.get_custom_report(self.request.user.tenant, report, as_of_date)
        
        return context

# --- Bank API Configuration ---

class BankAPIConfigListView(SalesCompassListView):
    model = BankAPIConfig
    template_name = 'accounting/bank_api_list.html'
    context_object_name = 'configs'

class BankAPIConfigCreateView(SalesCompassCreateView):
    model = BankAPIConfig
    form_class = BankAPIConfigForm
    template_name = 'accounting/bank_api_form.html'
    success_url = reverse_lazy('accounting:bank_api_list')
    success_message = "Bank API configuration saved."

class BankAPIConfigUpdateView(SalesCompassUpdateView):
    model = BankAPIConfig
    form_class = BankAPIConfigForm
    template_name = 'accounting/bank_api_form.html'
    success_url = reverse_lazy('accounting:bank_api_list')
    success_message = "Bank API configuration updated."
