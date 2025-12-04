from django.urls import path, re_path
from . import views

app_name = 'nps'
urlpatterns = [
    # NPS Dashboard
    path('', views.NpsDashboardView.as_view(), name='nps_dashboard'),
    path('trend/', views.NpsTrendChartsView.as_view(), name='nps_trend_charts'),
    path('responses/', views.NpsResponsesView.as_view(), name='nps_responses'),
    path('surveys/create/', views.NpsSurveyCreateView.as_view(), name='nps_survey_create'),
    
    # Detractor Kanban
    path('detractors/', views.DetractorKanbanView.as_view(), name='detractor_kanban'),
    path('api/update-detractor-status/', views.UpdateDetractorStatusView.as_view(), name='update_detractor_status'),
    
    # Survey Submission
    path('submit/<int:survey_id>', views.SubmitNPSView.as_view(), name='submit_nps'),
    
    # A/B Testing
    path('ab-test/create/', views.CreateNpsAbTestView.as_view(), name='create_nps_ab_test'),
]