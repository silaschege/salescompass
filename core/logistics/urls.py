from django.urls import path
from . import views

app_name = 'logistics'

urlpatterns = [
    path('', views.LogisticsDashboardView.as_view(), name='dashboard'),
    path('shipments/', views.ShipmentListView.as_view(), name='shipment_list'),
    path('shipments/<int:pk>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    path('carriers/', views.CarrierListView.as_view(), name='carrier_list'),
]
