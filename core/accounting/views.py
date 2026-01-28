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
    TaxRate, TaxRule
)
from .forms import (
    ChartOfAccountForm, JournalEntryForm, 
    BudgetForm, RecurringJournalEntryForm, 
    AccountingIntegrationForm, FiscalYearForm,
    JournalEntryLineFormSet, TaxRateForm, TaxRuleForm
)
from decimal import Decimal

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

        context['trial_balance'] = ReportService.get_trial_balance(self.request.user.tenant, as_of_date)
        context['as_of_date'] = as_of_date
        
        # Calculate totals for display
        total_debit = Decimal(0)
        total_credit = Decimal(0)
        
        for row in context['trial_balance']:
            if row['type'] in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                if row['balance'] >= 0:
                    total_debit += row['balance']
                else:
                    total_credit += abs(row['balance'])
            else:
                # Liability/Equity/Revenue
                if row['balance'] >= 0:
                    total_credit += row['balance']
                else:
                    total_debit += abs(row['balance'])
                    
        context['total_debit'] = total_debit
        context['total_credit'] = total_credit
        return context

class GeneralLedgerView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/general_ledger.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        account_id = self.request.GET.get('account_id')
        
        context['accounts'] = ChartOfAccount.objects.filter(tenant=tenant).order_by('account_code')
        
        if account_id:
            account = get_object_or_404(ChartOfAccount, id=account_id, tenant=tenant)
            queryset = JournalEntryLine.objects.filter(
                tenant=tenant,
                account=account,
                journal_entry__status='posted'
            ).select_related('journal_entry').order_by('journal_entry__entry_date')
            
            if start_date:
                queryset = queryset.filter(journal_entry__entry_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(journal_entry__entry_date__lte=end_date)
                
            entries = []
            running_balance = 0
            
            # Opening Balance
            if start_date:
                # Logic similar to before but updated for types
                opening_lines = JournalEntryLine.objects.filter(
                    tenant=tenant, account=account,
                    journal_entry__status='posted',
                    journal_entry__entry_date__lt=start_date
                )
                op_debit = opening_lines.aggregate(s=Sum('debit'))['s'] or 0
                op_credit = opening_lines.aggregate(s=Sum('credit'))['s'] or 0
                
                if account.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                    running_balance = op_debit - op_credit
                else:
                    running_balance = op_credit - op_debit
            
            context['opening_balance'] = running_balance
            
            for line in queryset:
                if account.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                    running_balance += (line.debit - line.credit)
                else:
                    running_balance += (line.credit - line.debit)
                    
                entries.append({
                    'date': line.journal_entry.entry_date,
                    'number': line.journal_entry.entry_number,
                    'description': line.description or line.journal_entry.description,
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': running_balance
                })
                
            context['ledger_entries'] = entries
            context['selected_account'] = account
            
        return context

class IncomeStatementView(LoginRequiredMixin, TenantAwareViewMixin, TemplateView):
    template_name = 'accounting/reports/income_statement.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Simplified P&L. For full IFRS, use ReportService if expaned.
        # For now, let's just grab data manually but supporting new types.
        
        tenant = self.request.user.tenant
        
        # Revenue
        revenues = ChartOfAccount.objects.filter(tenant=tenant, account_type='revenue')
        total_revenue = revenues.aggregate(t=Sum('current_balance'))['t'] or 0
        
        # Cost of Sales
        cogs = ChartOfAccount.objects.filter(tenant=tenant, account_type='cost_of_sales')
        total_cogs = cogs.aggregate(t=Sum('current_balance'))['t'] or 0
        
        gross_profit = total_revenue - total_cogs
        
        # Expenses
        expenses = ChartOfAccount.objects.filter(tenant=tenant, account_type__in=['expense', 'other_expense'])
        total_expense = expenses.aggregate(t=Sum('current_balance'))['t'] or 0
        
        net_income = gross_profit - total_expense
        
        context['revenues'] = revenues
        context['total_revenue'] = total_revenue
        context['cogs'] = cogs
        context['total_cogs'] = total_cogs
        context['gross_profit'] = gross_profit
        context['expenses'] = expenses
        context['total_expense'] = total_expense
        context['net_income'] = net_income
        
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

# --- Reconciliations ---

class ReconciliationListView(SalesCompassListView):
    model = BankReconciliation
    template_name = 'accounting/reconciliation_list.html'
    context_object_name = 'reconciliations'

class ReconciliationCreateView(SalesCompassCreateView):
    model = BankReconciliation
    fields = ['account', 'statement_date', 'opening_balance', 'closing_balance', 'status']
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
    fields = ['account', 'statement_date', 'opening_balance', 'closing_balance', 'status']
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
