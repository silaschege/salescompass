from django.urls import path
from . import views

app_name = 'manufacturing'

urlpatterns = [
    path('', views.ManufacturingDashboardView.as_view(), name='dashboard'),
    path('bom/', views.BOMListView.as_view(), name='bom_list'),
    path('bom/<int:pk>/', views.BOMDetailView.as_view(), name='bom_detail'),
    path('work-orders/', views.WorkOrderListView.as_view(), name='work_order_list'),
    path('work-orders/create/', views.WorkOrderCreateView.as_view(), name='work_order_create'),
    path('work-orders/<int:pk>/', views.WorkOrderDetailView.as_view(), name='work_order_detail'),
    path('floor/', views.ProductionFloorView.as_view(), name='production_floor'),
]
