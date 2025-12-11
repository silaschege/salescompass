from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    # Sales Velocity
    path('sales-velocity/', views.sales_velocity_dashboard, name='sales_velocity_dashboard'),
    path('sales-velocity-analysis/', views.sales_velocity_analysis, name='sales_velocity_analysis'),
    path('opportunity-funnel/', views.opportunity_funnel_analysis, name='opportunity_funnel_analysis'),
    
    # Add other existing URLs for opportunities
    # (Note: The actual existing URLs would need to be added based on the original file)
]
