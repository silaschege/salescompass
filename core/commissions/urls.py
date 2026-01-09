from django.urls import path
from . import views

app_name = 'commissions'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('list/', views.CommissionListView.as_view(), name='list'),
    path('history/', views.CommissionListView.as_view(), name='history'),
    path('statement/', views.CommissionStatementView.as_view(), name='statement'),
    path('statement/pdf/', views.CommissionStatementPDFView.as_view(), name='statement_pdf'),
    path('payments/', views.CommissionPaymentListView.as_view(), name='payments'),
    path('payments/<int:pk>/', views.CommissionPaymentDetailView.as_view(), name='payment_detail'),
    
    # New Phase 1 features
    path('quota/', views.QuotaAttainmentView.as_view(), name='quota_attainment'),
    path('what-if/', views.WhatIfCalculatorView.as_view(), name='what_if_calculator'),
    
    # New Phase 2 features
    path('plans/', views.CommissionPlanListView.as_view(), name='plan_list'),
    path('plans/create/', views.CommissionPlanCreateView.as_view(), name='plan_create'),
    path('plans/<int:pk>/edit/', views.CommissionPlanUpdateView.as_view(), name='plan_update'),
    path('plans/<int:pk>/clone/', views.CommissionPlanCloneView.as_view(), name='plan_clone'),
    path('templates/', views.CommissionPlanTemplateView.as_view(), name='plan_templates'),
    
    # Commission rule endpoints
    path('plans/<int:plan_id>/rules/create/', views.CommissionRuleCreateView.as_view(), name='rule_create'),
    path('rules/<int:pk>/edit/', views.CommissionRuleUpdateView.as_view(), name='rule_update'),
    path('rules/<int:pk>/delete/', views.CommissionRuleDeleteView.as_view(), name='rule_delete'),
    
    # Plan versioning endpoints
    path('plans/<int:plan_id>/versions/', views.CommissionPlanVersionListView.as_view(), name='plan_version_list'),
    path('plans/<int:plan_id>/versions/create/', views.CommissionPlanCreateVersionView.as_view(), name='plan_version_create'),
    path('versions/<int:pk>/', views.CommissionPlanVersionDetailView.as_view(), name='plan_version_detail'),
    
    # Plan template endpoints
    path('templates/create/', views.CommissionPlanTemplateCreateView.as_view(), name='plan_template_create'),
    path('templates/<int:pk>/edit/', views.CommissionPlanTemplateUpdateView.as_view(), name='plan_template_update'),
    path('templates/<int:pk>/delete/', views.CommissionPlanTemplateDeleteView.as_view(), name='plan_template_delete'),
    
    # New Phase 3 features
    path('forecasting/', views.ForecastingView.as_view(), name='forecasting'),
    
    # New Phase 4 features
    path('team/', views.TeamDashboardView.as_view(), name='team_dashboard'),
    
    # Export endpoints
    path('export/payroll/', views.PayrollExportView.as_view(), name='export_payroll'),
    path('export/api/', views.CommissionAPIExportView.as_view(), name='export_api'),
]