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
