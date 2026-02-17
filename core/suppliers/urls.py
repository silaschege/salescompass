from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    # Suppliers
    path('', views.SupplierListView.as_view(), name='supplier_list'),
    path('create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Contacts
    path('<int:supplier_pk>/contacts/add/', views.ContactCreateView.as_view(), name='contact_create'),
    path('<int:supplier_pk>/contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_update'),
    path('<int:supplier_pk>/contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),
    
    # Documents
    path('<int:supplier_pk>/documents/add/', views.DocumentCreateView.as_view(), name='document_create'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Reviews
    path('<int:supplier_pk>/reviews/add/', views.PerformanceReviewCreateView.as_view(), name='review_create'),
    
    # API
    path('api/search/', views.SupplierSearchAPI.as_view(), name='api_search'),
]
