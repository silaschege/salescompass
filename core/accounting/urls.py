from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('', views.AccountingDashboardView.as_view(), name='dashboard'),
    
    # Chart of Accounts
    path('chart-of-accounts/', views.ChartOfAccountListView.as_view(), name='coa_list'),
    path('chart-of-accounts/setup/', views.AccountingSetupView.as_view(), name='coa_setup'),
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
    path('reports/cash-flow/', views.CashFlowView.as_view(), name='cash_flow'),
    
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
    path('fiscal-periods/<int:pk>/close/', views.FiscalPeriodCloseView.as_view(), name='close_period'),
    # Tax Management
    path('taxes/rates/', views.TaxRateListView.as_view(), name='tax_rate_list'),
    path('taxes/rates/create/', views.TaxRateCreateView.as_view(), name='tax_rate_create'),
    path('taxes/rates/<int:pk>/edit/', views.TaxRateUpdateView.as_view(), name='tax_rate_update'),
    path('taxes/rates/<int:pk>/delete/', views.TaxRateDeleteView.as_view(), name='tax_rate_delete'),
    
    path('taxes/rules/', views.TaxRuleListView.as_view(), name='tax_rule_list'),
    path('taxes/rules/create/', views.TaxRuleCreateView.as_view(), name='tax_rule_create'),
    path('taxes/rules/<int:pk>/edit/', views.TaxRuleUpdateView.as_view(), name='tax_rule_update'),
    path('taxes/rules/<int:pk>/delete/', views.TaxRuleDeleteView.as_view(), name='tax_rule_delete'),

    # Bank Statements
    path('statements/', views.BankStatementListView.as_view(), name='statement_list'),
    path('statements/import/', views.BankStatementImportView.as_view(), name='statement_import'),
    path('statements/<int:pk>/', views.BankStatementDetailView.as_view(), name='statement_detail'),
    path('statements/match/', views.BankStatementMatchView.as_view(), name='statement_match'),

    # VAT Report
    path('reports/vat-return/', views.VATReturnView.as_view(), name='vat_return'),

    # Multi-currency Management
    path('currencies/', views.CurrencyListView.as_view(), name='currency_list'),
    path('currencies/create/', views.CurrencyCreateView.as_view(), name='currency_create'),
    path('currencies/<int:pk>/edit/', views.CurrencyUpdateView.as_view(), name='currency_update'),
    path('exchange-rates/', views.ExchangeRateListView.as_view(), name='exchange_rate_list'),
    path('exchange-rates/create/', views.ExchangeRateCreateView.as_view(), name='exchange_rate_create'),

    # Custom Financial Reports
    path('reports/custom/', views.CustomReportListView.as_view(), name='custom_report_list'),
    path('reports/custom/create/', views.CustomReportCreateView.as_view(), name='custom_report_create'),
    path('reports/custom/<int:pk>/edit/', views.CustomReportUpdateView.as_view(), name='custom_report_update'),
    path('reports/custom/<int:pk>/run/', views.CustomReportRunView.as_view(), name='custom_report_run'),

    # Bank API Configuration
    path('bank-api/', views.BankAPIConfigListView.as_view(), name='bank_api_list'),
    path('bank-api/create/', views.BankAPIConfigCreateView.as_view(), name='bank_api_create'),
    path('bank-api/<int:pk>/edit/', views.BankAPIConfigUpdateView.as_view(), name='bank_api_update'),
]
