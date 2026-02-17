from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    # Dashboard
    path('', views.PurchasingDashboardView.as_view(), name='dashboard'),
    
    # Purchase Orders
    path('orders/', views.PurchaseOrderListView.as_view(), name='po_list'),
    path('orders/create/', views.PurchaseOrderCreateView.as_view(), name='po_create'),
    path('orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='po_detail'),
    path('orders/<int:pk>/edit/', views.PurchaseOrderUpdateView.as_view(), name='po_update'),
    path('orders/<int:pk>/receive/', views.PurchaseOrderReceiveView.as_view(), name='po_receive'),
    
    # Supplier Invoices
    path('invoices/', views.SupplierInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.SupplierInvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.SupplierInvoiceDetailView.as_view(), name='invoice_detail'),

    # Supplier Payments
    path('payments/', views.SupplierPaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.SupplierPaymentCreateView.as_view(), name='payment_create'),
    
    # API Endpoints
    path('api/invoices/', views.get_invoice_details_api, name='api_invoice_details'),
    
    # Goods Receipts
    path('receipts/', views.GRNListView.as_view(), name='grn_list'),
    path('receipts/<int:pk>/', views.GRNDetailView.as_view(), name='grn_detail'),
    
    # Purchase Requisitions
    path('requisitions/', views.PurchaseRequisitionListView.as_view(), name='requisition_list'),
    path('requisitions/create/', views.PurchaseRequisitionCreateView.as_view(), name='requisition_create'),
    path('requisitions/<int:pk>/', views.PurchaseRequisitionDetailView.as_view(), name='requisition_detail'),
    path('requisitions/<int:pk>/edit/', views.PurchaseRequisitionUpdateView.as_view(), name='requisition_update'),
    path('requisitions/<int:pk>/convert/', views.PurchaseRequisitionConvertToPOView.as_view(), name='requisition_convert'),
]
