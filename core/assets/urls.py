from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Dashboard
    path('', views.AssetsDashboardView.as_view(), name='dashboard'),
    
    # Assets
    path('list/', views.AssetListView.as_view(), name='asset_list'),
    path('add/', views.AssetCreateView.as_view(), name='asset_create'),
    path('<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('<int:pk>/schedule/', views.AssetDepreciationScheduleView.as_view(), name='asset_schedule'),
    path('<int:pk>/edit/', views.AssetUpdateView.as_view(), name='asset_update'),
    path('<int:asset_pk>/impairment/', views.AssetImpairmentCreateView.as_view(), name='asset_impairment'),
    path('<int:asset_pk>/revaluation/', views.AssetRevaluationCreateView.as_view(), name='asset_revaluation'),
    path('<int:asset_pk>/dispose/', views.AssetDisposalCreateView.as_view(), name='asset_disposal'),
    path('<int:asset_pk>/verify/', views.AssetVerificationCreateView.as_view(), name='asset_verification'),
    path('<int:asset_pk>/maintenance/', views.AssetMaintenanceCreateView.as_view(), name='asset_maintenance'),
    path('<int:asset_pk>/schedule/', views.MaintenanceScheduleCreateView.as_view(), name='maintenance_schedule'),
    path('<int:pk>/qrcode/', views.AssetQRCodeView.as_view(), name='asset_qrcode'),
    path('<int:pk>/mobile/', views.MobileAssetAuditView.as_view(), name='asset_mobile'),
    
    # Reports
    path('reports/register/', views.AssetRegisterReportView.as_view(), name='asset_register_report'),
    path('reports/disclosure/', views.AssetDisclosureReportView.as_view(), name='asset_disclosure_report'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # Actions
    path('run-depreciation/', views.RunDepreciationActionView.as_view(), name='run_depreciation'),
]
