from django.urls import path
from . import views


app_name = 'products'
urlpatterns = [
    # CRUD
    path('product_list/', views.ProductListView.as_view(), name='product_list'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete'),
    
    # Additional views
    path('competitor-mapping/', views.CompetitorMappingView.as_view(), name='competitor_mapping'),
    path('comparison/', views.ProductComparisonView.as_view(), name='comparison'),
]