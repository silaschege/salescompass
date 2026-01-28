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
    path('reports/<int:pk>/settle/', views.ExpenseReportPayView.as_view(), name='report_pay'),
    
    path('approvals/', views.ExpenseApprovalInboxView.as_view(), name='approval_inbox'),
    
    # Categories
    path('categories/', views.ExpenseCategoryListView.as_view(), name='category_list'),
    
    # Lines
    path('reports/<int:pk>/add-line/', views.ExpenseLineCreateView.as_view(), name='line_create'),
]
