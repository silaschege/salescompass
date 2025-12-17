from django.urls import path
from . import views

app_name = 'commissions'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'), # Renamed for clarity, kept ''
   
    path('list/', views.CommissionListView.as_view(), name='list'),
    path('history/', views.CommissionListView.as_view(), name='history'),
    path('payments/', views.CommissionPaymentListView.as_view(), name='payments'),
    path('payments/<int:pk>/', views.CommissionPaymentDetailView.as_view(), name='payment_detail'),
]
