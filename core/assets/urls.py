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
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # Actions
    path('run-depreciation/', views.RunDepreciationActionView.as_view(), name='run_depreciation'),
]
