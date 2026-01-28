from django.urls import path
from . import views

app_name = 'quality_control'

urlpatterns = [
    path('', views.QualityDashboardView.as_view(), name='dashboard'),
    path('rules/', views.InspectionRuleListView.as_view(), name='rule_list'),
    path('logs/', views.InspectionLogListView.as_view(), name='log_list'),
    path('logs/create/', views.InspectionLogCreateView.as_view(), name='log_create'),
    path('ncr/', views.NCRListView.as_view(), name='ncr_list'),
]
