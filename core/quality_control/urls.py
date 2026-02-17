from django.urls import path
from . import views

app_name = 'quality_control'

urlpatterns = [
    path('', views.QualityDashboardView.as_view(), name='dashboard'),
    path('rules/', views.InspectionRuleListView.as_view(), name='rule_list'),
    path('rules/create/', views.InspectionRuleCreateView.as_view(), name='rule_create'),
    path('rules/<int:pk>/edit/', views.InspectionRuleUpdateView.as_view(), name='rule_update'),
    path('logs/', views.InspectionLogListView.as_view(), name='log_list'),
    path('logs/create/', views.InspectionLogCreateView.as_view(), name='log_create'),
    path('ncr/', views.NCRListView.as_view(), name='ncr_list'),
    path('ncr/<int:pk>/edit/', views.NCRUpdateView.as_view(), name='ncr_update'),
    path('capa/', views.CAPAListView.as_view(), name='capa_list'),
    path('capa/create/', views.CAPACreateView.as_view(), name='capa_create'),
    path('capa/<int:pk>/edit/', views.CAPAUpdateView.as_view(), name='capa_update'),
    path('charts/', views.TemplateView.as_view(template_name='quality_control/control_charts.html'), name='control_charts'),
    path('api/rule/<int:pk>/', views.rule_detail_api, name='rule_detail_api'),
    path('api/charts/data/', views.ControlChartDataAPI.as_view(), name='chart_data_api'),
    path('api/sampling/calculate/', views.calculate_sample_api, name='calculate_sample_api'),
    
    # Quality Check Library
    path('library/', views.QualityCheckLibraryListView.as_view(), name='library_list'),
    path('library/create/', views.QualityCheckLibraryCreateView.as_view(), name='library_create'),
    path('library/<int:pk>/edit/', views.QualityCheckLibraryUpdateView.as_view(), name='library_update'),
    path('api/library/', views.library_list_api, name='library_list_api'),
]
