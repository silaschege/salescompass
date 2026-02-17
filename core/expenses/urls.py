from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Dashboard
    path('', views.ExpensesDashboardView.as_view(), name='dashboard'),
    
    # Reports
    path('reports/', views.ExpenseReportListView.as_view(), name='report_list'),
    path('reports/create/', views.ExpenseReportCreateView.as_view(), name='report_create'),
    path('reports/<int:pk>/', views.ExpenseReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/submit/', views.ExpenseReportSubmitView.as_view(), name='report_submit'),
    path('reports/<int:pk>/approve/', views.ExpenseReportApproveView.as_view(), name='report_approve'),
    path('reports/<int:pk>/pay/', views.ExpenseReportPayView.as_view(), name='report_pay'),
    
    path('approval/inbox/', views.ExpenseApprovalInboxView.as_view(), name='approval_inbox'),
    
    # Categories
    path('categories/', views.ExpenseCategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.ExpenseCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.ExpenseCategoryUpdateView.as_view(), name='category_update'),
    
    # Lines
    path('reports/<int:pk>/add-line/', views.ExpenseLineCreateView.as_view(), name='line_create'),
    
    # Phase 2: Cards & Analytics
    path('cards/', views.CorporateCardListView.as_view(), name='card_list'),
    path('cards/add/', views.CorporateCardCreateView.as_view(), name='card_create'),
    path('cards/<int:pk>/edit/', views.CorporateCardUpdateView.as_view(), name='card_update'),
    path('cards/import/', views.CardTransactionImportView.as_view(), name='card_import'),
    path('analytics/data/', views.ExpenseAnalyticsDataView.as_view(), name='analytics_data'),
]
