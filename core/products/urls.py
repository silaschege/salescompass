from django.urls import path
from . import views


app_name = 'products'
urlpatterns = [
    # Product CRUD
    path('product_list/', views.ProductListView.as_view(), name='product_list'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # ProductBundle CRUD
    path('bundle_list/', views.ProductBundleListView.as_view(), name='productbundle_list'),
    path('bundle/create/', views.ProductBundleCreateView.as_view(), name='productbundle_create'),
    path('bundle/<int:pk>/', views.ProductBundleDetailView.as_view(), name='productbundle_detail'),
    path('bundle/<int:pk>/edit/', views.ProductBundleUpdateView.as_view(), name='productbundle_update'),
    path('bundle/<int:pk>/delete/', views.ProductBundleDeleteView.as_view(), name='productbundle_delete'),
    
    # CompetitorProduct CRUD
    path('competitor_list/', views.CompetitorProductListView.as_view(), name='competitorproduct_list'),
    path('competitor/create/', views.CompetitorProductCreateView.as_view(), name='competitorproduct_create'),
    path('competitor/<int:pk>/', views.CompetitorProductDetailView.as_view(), name='competitorproduct_detail'),
    path('competitor/<int:pk>/edit/', views.CompetitorProductUpdateView.as_view(), name='competitorproduct_update'),
    path('competitor/<int:pk>/delete/', views.CompetitorProductDeleteView.as_view(), name='competitorproduct_delete'),
    
    # ProductComparison CRUD
    path('comparison_list/', views.ProductComparisonListView.as_view(), name='productcomparison_list'),
    path('comparison/create/', views.ProductComparisonCreateView.as_view(), name='productcomparison_create'),
    path('comparison/<int:pk>/', views.ProductComparisonDetailView.as_view(), name='productcomparison_detail'),
    path('comparison/<int:pk>/edit/', views.ProductComparisonUpdateView.as_view(), name='productcomparison_update'),
    path('comparison/<int:pk>/delete/', views.ProductComparisonDeleteView.as_view(), name='productcomparison_delete'),
    
    # ProductDependency CRUD
    path('dependency_list/', views.ProductDependencyListView.as_view(), name='productdependency_list'),
    path('dependency/create/', views.ProductDependencyCreateView.as_view(), name='productdependency_create'),
    path('dependency/<int:pk>/edit/', views.ProductDependencyUpdateView.as_view(), name='productdependency_update'),
    path('dependency/<int:pk>/delete/', views.ProductDependencyDeleteView.as_view(), name='productdependency_delete'),
    
    # Additional views
    path('competitor-mapping/', views.CompetitorMappingView.as_view(), name='competitor_mapping'),
    path('comparison/', views.ProductComparisonView.as_view(), name='comparison'),
]