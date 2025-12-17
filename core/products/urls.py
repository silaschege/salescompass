from django.urls import path
from . import views


app_name = 'products'
urlpatterns = [
    # CRUD
    # CRUD
    path('product_list/', views.ProductListView.as_view(), name='product_list'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Additional views
    path('competitor-mapping/', views.CompetitorMappingView.as_view(), name='competitor_mapping'),
    path('comparison/', views.ProductComparisonView.as_view(), name='comparison'),
]