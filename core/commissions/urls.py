from django.urls import path
from . import views

app_name = 'commissions'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='list'), # Dashboard is the main view
    path('history/', views.CommissionListView.as_view(), name='history'),
]
