from django.urls import path
from . import views

app_name = 'customer_portal'

urlpatterns = [
    path('', views.PortalDashboardView.as_view(), name='dashboard'),
    path('invoices/', views.PortalInvoiceListView.as_view(), name='invoice_list'),
    path('tickets/', views.PortalTicketListView.as_view(), name='ticket_list'),
    path('proposals/', views.PortalProposalListView.as_view(), name='proposal_list'),
    
    # Ecommerce Routes
    path('orders/', views.EcommerceOrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.EcommerceOrderDetailView.as_view(), name='order_detail'),
    path('profile/', views.EcommerceProfileView.as_view(), name='profile'),
]
