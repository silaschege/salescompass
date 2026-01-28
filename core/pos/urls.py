from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    # Main POS Terminal Interface
    path('', views.POSDashboardView.as_view(), name='dashboard'),
    path('terminal/', views.POSTerminalView.as_view(), name='terminal'),
    path('terminal/<int:terminal_id>/', views.POSTerminalView.as_view(), name='terminal_select'),
    
    # Terminals
    path('terminals/', views.TerminalListView.as_view(), name='terminal_list'),
    path('terminals/create/', views.TerminalCreateView.as_view(), name='terminal_create'),
    path('terminals/<int:pk>/edit/', views.TerminalUpdateView.as_view(), name='terminal_update'),
    path('terminals/<int:pk>/hardware/', views.HardwareTestView.as_view(), name='terminal_hardware_test'),
    
    # Sessions
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/open/', views.SessionOpenView.as_view(), name='session_open'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/close/', views.SessionCloseView.as_view(), name='session_close'),
    
    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/void/', views.TransactionVoidView.as_view(), name='transaction_void'),
    
    # Receipts
    path('receipts/<int:pk>/', views.ReceiptView.as_view(), name='receipt_view'),
    path('receipts/<int:pk>/print/', views.ReceiptPrintView.as_view(), name='receipt_print'),
    path('receipts/<int:pk>/preview/', views.ReceiptPreviewView.as_view(), name='receipt_preview'),
    
    # Refunds
    path('refunds/', views.RefundListView.as_view(), name='refund_list'),
    path('refunds/create/<int:transaction_id>/', views.RefundCreateView.as_view(), name='refund_create'),
    path('refunds/<int:pk>/', views.RefundDetailView.as_view(), name='refund_detail'),
    path('refunds/<int:pk>/approve/', views.RefundApproveView.as_view(), name='refund_approve'),
    
    # Cash Drawer
    path('cash-drawer/', views.CashDrawerView.as_view(), name='cash_drawer'),
    path('cash-drawer/pay-in/', views.CashPayInView.as_view(), name='cash_pay_in'),
    path('cash-drawer/pay-out/', views.CashPayOutView.as_view(), name='cash_pay_out'),
    
    # API endpoints for terminal
    path('api/products/', views.ProductListAPI.as_view(), name='api_product_list'),
    path('api/categories/', views.CategoryListAPI.as_view(), name='api_category_list'),
    path('api/products/search/', views.ProductSearchAPI.as_view(), name='api_product_search'),
    path('api/products/barcode/<str:barcode>/', views.ProductBarcodeAPI.as_view(), name='api_product_barcode'),
    path('api/transactions/', views.TransactionCreateAPI.as_view(), name='api_transaction_create'),
    path('api/transactions/<int:pk>/', views.TransactionDetailAPI.as_view(), name='api_transaction_detail'),
    path('api/transactions/<int:pk>/lines/', views.TransactionLineAPI.as_view(), name='api_transaction_lines'),
    path('api/transactions/<int:pk>/lines/<int:line_id>/', views.TransactionLineUpdateAPI.as_view(), name='api_transaction_line_update'),
    path('api/transactions/<int:pk>/pay/', views.TransactionPayAPI.as_view(), name='api_transaction_pay'),
    path('api/transactions/<int:pk>/clear/', views.TransactionClearAPI.as_view(), name='api_transaction_clear'),
    path('api/transactions/<int:pk>/hold/', views.TransactionHoldAPI.as_view(), name='api_transaction_hold'),
    path('api/transactions/held/', views.HeldTransactionsAPI.as_view(), name='api_held_transactions'),
    path('api/transactions/<int:pk>/resume/', views.TransactionResumeAPI.as_view(), name='api_transaction_resume'),
    path('api/transactions/<int:pk>/customer/', views.TransactionCustomerAPI.as_view(), name='api_transaction_customer'),
    path('api/products/stock/', views.ProductStockAPI.as_view(), name='api_product_stock'),
    path('api/hardware/test/<int:pk>/', views.HardwareTestAPI.as_view(), name='api_hardware_test'),
    
    # Reports
    path('reports/', views.POSReportsView.as_view(), name='reports'),
    path('reports/x-report/', views.XReportView.as_view(), name='report_x'),
    path('reports/z-report/', views.ZReportView.as_view(), name='report_z'),
    path('reports/daily/', views.DailySalesReportView.as_view(), name='report_daily'),
    path('reports/cashier/', views.CashierReportView.as_view(), name='report_cashier'),
    path('reports/products/', views.ProductSalesReportView.as_view(), name='report_product_sales'),
    path('reports/trends/', views.SalesTrendsReportView.as_view(), name='report_sales_trends'),
    path('reports/payments/', views.PaymentMethodsReportView.as_view(), name='report_payment_methods'),
    path('reports/refunds-voids/', views.RefundsVoidsReportView.as_view(), name='report_refunds_voids'),
]

