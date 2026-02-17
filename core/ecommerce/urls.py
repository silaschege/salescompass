from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='index'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('cart/', views.CartView.as_view(), name='cart_view'),
    path('cart/add/<int:pk>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order/confirmation/<int:pk>/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('my-orders/', views.OrderHistoryView.as_view(), name='order_list'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]
