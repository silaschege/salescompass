from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
   
    path('', views.SalesDashboardView.as_view(), name='sales_dashboard'),
    path('list/', views.SaleListView.as_view(), name='sale_list'),
    path('create/', views.SaleCreateView.as_view(), name='sale_create'),
    path('<int:pk>/', views.SaleDetailView.as_view(), name='sale_detail'),
    path('<int:pk>/edit/', views.SaleUpdateView.as_view(), name='sale_update'),
    
    # Commission URLs
    path('commissions/', views.commission_dashboard, name='commission_dashboard'),
    path('commissions/rules/', views.CommissionRuleListView.as_view(), name='rule_list'),
    path('commissions/rules/create/', views.CommissionRuleCreateView.as_view(), name='rule_create'),
    path('commissions/rules/<int:pk>/edit/', views.CommissionRuleUpdateView.as_view(), name='rule_update'),
    path('commissions/rules/<int:pk>/delete/', views.CommissionRuleDeleteView.as_view(), name='rule_delete'),
    
    # Territory Optimization URLs
    path('territories/performance/', views.territory_performance_dashboard, name='territory_performance_dashboard'),
    path('territories/optimization/', views.territory_assignment_optimization_dashboard, name='territory_assignment_optimization_dashboard'),
    path('territories/optimization/<int:territory_id>/run/', views.run_territory_optimization, name='run_territory_optimization'),
    path('territories/comparison/', views.territory_comparison_tool, name='territory_comparison_tool'),
    path('api/territories/performance/', views.territory_performance_api, name='territory_performance_api'),
]
