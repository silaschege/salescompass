from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('', views.AccountingDashboardView.as_view(), name='dashboard'),
    
    # Chart of Accounts
    path('chart-of-accounts/', views.ChartOfAccountListView.as_view(), name='coa_list'),
    path('chart-of-accounts/create/', views.ChartOfAccountCreateView.as_view(), name='coa_create'),
    path('chart-of-accounts/<int:pk>/', views.ChartOfAccountDetailView.as_view(), name='coa_detail'),
    path('chart-of-accounts/<int:pk>/edit/', views.ChartOfAccountUpdateView.as_view(), name='coa_update'),
    
    # Journal Entries
    path('journals/', views.JournalEntryListView.as_view(), name='journal_list'),
    path('journals/create/', views.JournalEntryCreateView.as_view(), name='journal_create'),
    path('journals/<int:pk>/', views.JournalEntryDetailView.as_view(), name='journal_detail'),
    path('journals/<int:pk>/post/', views.JournalEntryPostView.as_view(), name='journal_post'),
    
    # Reports
    path('reports/trial-balance/', views.TrialBalanceView.as_view(), name='trial_balance'),
    path('reports/general-ledger/', views.GeneralLedgerView.as_view(), name='general_ledger'),
    path('reports/income-statement/', views.IncomeStatementView.as_view(), name='income_statement'),
    path('reports/balance-sheet/', views.BalanceSheetView.as_view(), name='balance_sheet'),
    
    # Reconciliations
    path('reconciliations/', views.ReconciliationListView.as_view(), name='reconciliation_list'),
    path('reconciliations/create/', views.ReconciliationCreateView.as_view(), name='reconciliation_create'),
    path('reconciliations/<int:pk>/edit/', views.ReconciliationUpdateView.as_view(), name='reconciliation_update'),

    # Budgets
    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('budgets/create/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='budget_update'),

    # Recurring Journals
    path('recurring-journals/', views.RecurringJournalListView.as_view(), name='recurring_journal_list'),
    path('recurring-journals/create/', views.RecurringJournalCreateView.as_view(), name='recurring_journal_create'),
    path('recurring-journals/<int:pk>/edit/', views.RecurringJournalUpdateView.as_view(), name='recurring_journal_update'),

    # Integrations
    path('integrations/', views.IntegrationListView.as_view(), name='integration_list'),
    path('integrations/create/', views.IntegrationCreateView.as_view(), name='integration_create'),
    path('integrations/<int:pk>/edit/', views.IntegrationUpdateView.as_view(), name='integration_update'),

    # Fiscal Years
    path('fiscal-years/', views.FiscalYearListView.as_view(), name='fiscal_year_list'),
    path('fiscal-years/create/', views.FiscalYearCreateView.as_view(), name='fiscal_year_create'),
    path('fiscal-years/<int:pk>/edit/', views.FiscalYearUpdateView.as_view(), name='fiscal_year_update'),
    # Tax Management
    path('taxes/rates/', views.TaxRateListView.as_view(), name='tax_rate_list'),
    path('taxes/rates/create/', views.TaxRateCreateView.as_view(), name='tax_rate_create'),
    path('taxes/rates/<int:pk>/edit/', views.TaxRateUpdateView.as_view(), name='tax_rate_update'),
    path('taxes/rates/<int:pk>/delete/', views.TaxRateDeleteView.as_view(), name='tax_rate_delete'),
    
    path('taxes/rules/', views.TaxRuleListView.as_view(), name='tax_rule_list'),
    path('taxes/rules/create/', views.TaxRuleCreateView.as_view(), name='tax_rule_create'),
    path('taxes/rules/<int:pk>/edit/', views.TaxRuleUpdateView.as_view(), name='tax_rule_update'),
    path('taxes/rules/<int:pk>/delete/', views.TaxRuleDeleteView.as_view(), name='tax_rule_delete'),
]
