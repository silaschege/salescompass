from django.urls import path
from . import views

app_name = 'opportunities'
urlpatterns = [

    # Kanban
    path('', views.OpportunityKanbanView.as_view(), name='kanban'),
    
    # Pipeline Kanban
    path('pipeline/', views.PipelineKanbanView.as_view(), name='pipeline'),
    
    # CRUD
    path('list/', views.OpportunityListView.as_view(), name='opportunities_list'),
    path('create/', views.OpportunityCreateView.as_view(), name='create'),
    path('<int:pk>/', views.OpportunityDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.OpportunityUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.OpportunityDeleteView.as_view(), name='delete'),
    
    # Forecast
    path('forecast/', views.ForecastDashboardView.as_view(), name='forecast_dashboard'),
    
    # Win/Loss
    path('win-loss/', views.WinLossAnalysisView.as_view(), name='win_loss_analysis'),

    # AJAX
    path('<int:opportunity_id>/update-stage/', views.update_opportunity_stage, name='update_stage'),
   
]
