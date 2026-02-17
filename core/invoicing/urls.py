from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/<int:pk>/mark-paid/', views.InvoiceMarkPaidView.as_view(), name='invoice_mark_paid'),
    path('invoices/<int:pk>/send/', views.InvoiceSendView.as_view(), name='invoice_send'),
    path('invoices/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
    
    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    
    # Credit/Debit Notes
    path('credit-notes/', views.CreditNoteListView.as_view(), name='credit_note_list'),
    path('credit-notes/create/', views.CreditNoteCreateView.as_view(), name='credit_note_create'),
    path('debit-notes/', views.DebitNoteListView.as_view(), name='debit_note_list'),
    path('debit-notes/create/', views.DebitNoteCreateView.as_view(), name='debit_note_create'),
]
