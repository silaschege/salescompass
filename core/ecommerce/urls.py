from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='index'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('cart/', views.CartView.as_view(), name='cart_view'),
    path('cart/add/<int:pk>/', views.AddToCartView.as_view(), name='add_to_cart'),
]
