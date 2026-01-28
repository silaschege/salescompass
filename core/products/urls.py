from django.urls import path
from . import views


app_name = 'products'
urlpatterns = [
    # Product CRUD
    path('governance/', views.ProductGovernanceDashboardView.as_view(), name='governance_dashboard'),
    path('', views.ProductListView.as_view(), name='product_list'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Barcodes and Labels
    path('product-barcode/<int:pk>/', views.ProductBarcodeView.as_view(), name='product_barcode'),
    path('product-label/<int:pk>/', views.ProductLabelView.as_view(), name='product_label'),
    path('bulk-labels/', views.BulkLabelPrintView.as_view(), name='bulk_label_print'),
    
    # Category CRUD
    path('categories/', views.ProductCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ProductCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.ProductCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.ProductCategoryDeleteView.as_view(), name='category_delete'),
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
    
    # Price Lists
    path('price-lists/', views.PriceListListView.as_view(), name='pricelist_list'),
    path('price-lists/create/', views.PriceListCreateView.as_view(), name='pricelist_create'),
    path('price-lists/<int:pk>/edit/', views.PriceListUpdateView.as_view(), name='pricelist_edit'),
    path('price-lists/<int:pk>/delete/', views.PriceListDeleteView.as_view(), name='pricelist_delete'),
    
    # Price List Items
    path('price-lists/items/add/', views.PriceListItemCreateView.as_view(), name='pricelistitem_add'),
    path('price-lists/items/<int:pk>/delete/', views.PriceListItemDeleteView.as_view(), name='pricelistitem_delete'),
    
    # Coupons
    path('coupons/', views.CouponListView.as_view(), name='coupon_list'),
    path('coupons/create/', views.CouponCreateView.as_view(), name='coupon_create'),
    path('coupons/<int:pk>/edit/', views.CouponUpdateView.as_view(), name='coupon_update'),
    path('coupons/<int:pk>/delete/', views.CouponDeleteView.as_view(), name='coupon_delete'),
    
    # Promotions
    path('promotions/', views.PromotionListView.as_view(), name='promotion_list'),
    path('promotions/create/', views.PromotionCreateView.as_view(), name='promotion_create'),
    path('promotions/<int:pk>/edit/', views.PromotionUpdateView.as_view(), name='promotion_update'),
    path('promotions/<int:pk>/delete/', views.PromotionDeleteView.as_view(), name='promotion_delete'),
    
    # Supplier CRUD
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
]