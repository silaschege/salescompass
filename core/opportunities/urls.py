from django.urls import path
from . import views
from . import views_pipeline

app_name = 'opportunities'

urlpatterns = [
    # CRUD
    path('', views.OpportunityListView.as_view(), name='opportunity_list'),
    path('create/', views.OpportunityCreateView.as_view(), name='opportunity_create'),
    path('<int:pk>/', views.OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('<int:pk>/edit/', views.OpportunityUpdateView.as_view(), name='opportunity_update'),
    path('<int:pk>/delete/', views.OpportunityDeleteView.as_view(), name='opportunity_delete'),
    
    # Pipeline
    path('pipeline/', views_pipeline.PipelineKanbanView.as_view(), name='pipeline_kanban'),
    path('api/update-stage/<int:opportunity_id>/', views_pipeline.update_opportunity_stage, name='update_stage'),

    # Sales Velocity
    path('sales-velocity/', views.sales_velocity_dashboard, name='sales_velocity_dashboard'),
    path('sales-velocity-analysis/', views.sales_velocity_analysis, name='sales_velocity_analysis'),
    path('opportunity-funnel/', views.opportunity_funnel_analysis, name='opportunity_funnel_analysis'),
    
    # Revenue Forecast
    path('forecast/', views.RevenueForecastView.as_view(), name='revenue_forecast'),
    
    # Add other existing URLs for opportunities
    # (Note: The actual existing URLs would need to be added based on the original file)

    # Assignment Rules
    path('assignment-rules/', views.AssignmentRuleListView.as_view(), name='assignment_rule_list'),
    path('assignment-rules/create/', views.AssignmentRuleCreateView.as_view(), name='assignment_rule_create'),
    path('assignment-rules/<int:pk>/edit/', views.AssignmentRuleUpdateView.as_view(), name='assignment_rule_update'),
    path('assignment-rules/<int:pk>/delete/', views.AssignmentRuleDeleteView.as_view(), name='assignment_rule_delete'),

    # Pipeline Stages
    path('stages/', views.OpportunityStageListView.as_view(), name='stage_list'),
    path('stages/create/', views.OpportunityStageCreateView.as_view(), name='stage_create'),
    path('stages/<int:pk>/edit/', views.OpportunityStageUpdateView.as_view(), name='stage_update'),
    path('stages/<int:pk>/delete/', views.OpportunityStageDeleteView.as_view(), name='stage_delete'),

    # Pipeline Types
    path('pipeline-types/', views.PipelineTypeListView.as_view(), name='type_list'),
    path('pipeline-types/create/', views.PipelineTypeCreateView.as_view(), name='type_create'),
    path('pipeline-types/<int:pk>/edit/', views.PipelineTypeUpdateView.as_view(), name='type_update'),
    path('pipeline-types/<int:pk>/delete/', views.PipelineTypeDeleteView.as_view(), name='type_delete'),


]
