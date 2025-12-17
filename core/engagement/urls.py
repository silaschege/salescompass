from django.urls import path
from . import views


app_name = 'engagement'
urlpatterns = [
    # Engagement Feed
    path('feed/', views.EngagementFeedView.as_view(), name='feed'),
    path('events/<int:pk>/', views.EngagementEventDetailView.as_view(), name='event_detail'),
    # Engagement Detail
    path('events/<int:pk>/edit/', views.EngagementEventUpdateView.as_view(), name='event_update'),
    
# Next Best Actions - Complete CRUD + API
    path('reports/disengaged/', views.DisengagedAccountsView.as_view(), name='disengaged_accounts'),
    path('reports/leaderboard/', views.EngagementLeaderboardView.as_view(), name='leaderboard'),
    path('next-best-actions/', views.NextBestActionListView.as_view(), name='next_best_action'),
    path('next-best-actions/create/', views.NextBestActionCreateView.as_view(), name='next_best_action_create'),
    path('next-best-actions/<int:pk>/', views.NextBestActionDetailView.as_view(), name='next_best_action_detail'),
    path('next-best-actions/<int:pk>/edit/', views.NextBestActionUpdateView.as_view(), name='next_best_action_update'),
    path('next-best-actions/<int:pk>/delete/', views.NextBestActionDeleteView.as_view(), name='next_best_action_delete'),
  
    
    # AJAX/API Endpoints
    path('api/complete-next-best-action/', views.CompleteNextBestActionView.as_view(), name='complete_next_best_action'),
    
    # Legacy API endpoint (for backward compatibility)
    path('api/complete-action/<int:pk>/', views.complete_next_best_action_with_note_view, name='api_complete_next_best_action_with_note'),
    path('api/start-action/<int:pk>/', views.start_next_best_action_view, name='api_start_next_best_action'),
    
    # # Next Best Action Templates (if you have them)
    # path('next-best-action-templates/', views.NextBestActionTemplateListView.as_view(), name='nba_template_list'),
    # path('next-best-action-templates/create/', views.NextBestActionTemplateCreateView.as_view(), name='nba_template_create'),
    
    # Playbooks
    path('playbooks/', views.EngagementPlaybookListView.as_view(), name='playbook_list'),
    path('playbooks/create/', views.EngagementPlaybookCreateView.as_view(), name='playbook_create'),
    path('playbooks/<int:pk>/', views.EngagementPlaybookDetailView.as_view(), name='playbook_detail'),
    path('playbooks/<int:pk>/edit/', views.EngagementPlaybookUpdateView.as_view(), name='playbook_update'),
    
    # Playbook Steps
    path('playbooks/<int:playbook_id>/steps/add/', views.PlaybookStepCreateView.as_view(), name='playbook_step_create'),
    path('playbooks/steps/<int:pk>/edit/', views.PlaybookStepUpdateView.as_view(), name='playbook_step_update'),
    path('playbooks/steps/<int:pk>/delete/', views.PlaybookStepDeleteView.as_view(), name='playbook_step_delete'),

    # Dashboard
    path('dashboard/', views.EngagementDashboardView.as_view(), name='dashboard'),
    
]



    # # Webhooks
    # path('webhooks/', views.EngagementWebhookListView.as_view(), name='webhook_list'),
    # path('webhooks/create/', views.EngagementWebhookCreateView.as_view(), name='webhook_create'),
    # path('webhooks/<int:pk>/edit/', views.EngagementWebhookUpdateView.as_view(), name='webhook_update'),
    # path('webhooks/<int:pk>/delete/', views.EngagementWebhookDeleteView.as_view(), name='webhook_delete'),