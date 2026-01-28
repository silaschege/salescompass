from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),
    
    # Warehouses
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/<int:pk>/edit/', views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    
    # Stock Levels
    path('stock/', views.StockLevelListView.as_view(), name='stock_list'),
    path('stock/<int:pk>/', views.StockLevelDetailView.as_view(), name='stock_detail'),
    
    # Stock Movements
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/add/', views.StockAddView.as_view(), name='stock_add'),
    path('movements/remove/', views.StockRemoveView.as_view(), name='stock_remove'),
    path('movements/transfer/', views.StockTransferView.as_view(), name='stock_transfer'),
    
    # Adjustments
    path('adjustments/', views.StockAdjustmentListView.as_view(), name='adjustment_list'),
    path('adjustments/create/', views.StockAdjustmentCreateView.as_view(), name='adjustment_create'),
    path('adjustments/<int:pk>/', views.StockAdjustmentDetailView.as_view(), name='adjustment_detail'),
    
    # Alerts
    path('alerts/', views.StockAlertListView.as_view(), name='alert_list'),
    path('alerts/<int:pk>/acknowledge/', views.AcknowledgeAlertView.as_view(), name='alert_acknowledge'),
    
    # Reorder Rules
    path('reorder-rules/', views.ReorderRuleListView.as_view(), name='reorder_list'),
    path('reorder-rules/create/', views.ReorderRuleCreateView.as_view(), name='reorder_create'),
    path('reorder-rules/<int:pk>/edit/', views.ReorderRuleUpdateView.as_view(), name='reorder_update'),
    
    # Transfers
    path('transfers/', views.TransferListView.as_view(), name='transfer_list'),
    path('transfers/create/', views.TransferCreateView.as_view(), name='transfer_create'),
    path('transfers/<int:pk>/', views.TransferDetailView.as_view(), name='transfer_detail'),
    path('transfers/<int:pk>/ship/', views.TransferShipView.as_view(), name='transfer_ship'),
    path('transfers/<int:pk>/receive/', views.TransferReceiveView.as_view(), name='transfer_receive'),
]

