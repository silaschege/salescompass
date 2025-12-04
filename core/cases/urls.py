from django.urls import path
from . import views

app_name = 'cases'
urlpatterns = [
    # CRUD
    path('', views.CaseListView.as_view(), name='list'),
    path('create/', views.CaseCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CaseDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.CaseUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.CaseDeleteView.as_view(), name='delete'),
    
    # CSAT
    path('csat/survey/', views.CsatSurveyView.as_view(), name='csat_survey'),
    path('csat/thank-you/', views.CsatThankYouView.as_view(), name='csat_thank_you'),
    
    # Knowledge Base
    path('knowledge-base/', views.KnowledgeBaseView.as_view(), name='knowledge_base'),
    
    # Kanban
    path('kanban/', views.CaseKanbanView.as_view(), name='kanban'),

    path('detractors/', views.DetractorKanbanView.as_view(), name='detractor_kanban'),
    
    # Dashboard
    path('sla-dashboard/', views.SlaDashboardView.as_view(), name='sla_dashboard'),

    # AJAX Endpoints
        # Detractor status update
    path('api/update-detractor-status/', views.UpdateDetractorStatusView.as_view(), name='update_detractor_status'),
    path('api/update-case-status/', views.UpdateCaseStatusView.as_view(), name='update_case_status'),
]

