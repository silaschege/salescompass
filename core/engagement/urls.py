from django.urls import path
from . import views
from . import api_views

app_name = 'engagement'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.EngagementDashboardView.as_view(), name='dashboard'),
    path('account-breakdowns/', views.EngagementAccountBreakdownView.as_view(), name='account_breakdowns'),
    
    # Engagement Events
    path('feed/', views.EngagementFeedView.as_view(), name='feed'),
    path('events/<int:pk>/', views.EngagementEventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/edit/', views.EngagementEventUpdateView.as_view(), name='event_update'),
    path('api/events/merge/', views.EngagementMergeView.as_view(), name='event_merge'),
    path('data-quality/', views.EngagementDataQualityView.as_view(), name='data_quality'),
    
    # Engagement Event Comments
    path('events/<int:event_pk>/comments/add/', views.EngagementEventCommentCreateView.as_view(), name='event_comment_create'),
    
    # Next Best Actions - Complete CRUD
    path('next-best-actions/', views.NextBestActionListView.as_view(), name='next_best_action'),
    path('next-best-actions/create/', views.NextBestActionCreateView.as_view(), name='next_best_action_create'),
    path('next-best-actions/<int:pk>/', views.NextBestActionDetailView.as_view(), name='next_best_action_detail'),
    path('next-best-actions/<int:pk>/edit/', views.NextBestActionUpdateView.as_view(), name='next_best_action_update'),
    path('next-best-actions/<int:pk>/delete/', views.NextBestActionDeleteView.as_view(), name='next_best_action_delete'),
    
    # Next Best Actions - Special operations
    path('next-best-actions/<int:pk>/start/', views.start_next_best_action_view, name='start_next_best_action'),
    
    # Next Best Action Comments
    path('next-best-actions/<int:nba_pk>/comments/add/', views.NextBestActionCommentCreateView.as_view(), name='nba_comment_create'),
    
    # AJAX/API Endpoints for Next Best Actions
    path('api/complete-next-best-action/', views.CompleteNextBestActionView.as_view(), name='complete_next_best_action'),
    path('api/complete-action/<int:pk>/', views.complete_next_best_action_with_note_view, name='complete_next_best_action_with_note'),
    path('api/start-action/<int:pk>/', views.start_next_best_action_view, name='start_next_best_action_api'),
    
    # Reports
    path('reports/disengaged/', views.DisengagedAccountsView.as_view(), name='disengaged_accounts'),
    path('reports/disengaged/export/<str:format>/', views.DisengagedAccountsExportView.as_view(), name='disengaged_accounts_export'),
    path('reports/top-engaged/', views.TopEngagedAccountsView.as_view(), name='top_engaged_accounts'),
    path('reports/top-engaged/export/<str:format>/', views.TopEngagedAccountsExportView.as_view(), name='top_engaged_accounts_export'),
    path('reports/leaderboard/', views.EngagementLeaderboardView.as_view(), name='leaderboard'),
    
    # Playbooks
    path('playbooks/', views.EngagementPlaybookListView.as_view(), name='playbook_list'),
    path('playbooks/create/', views.EngagementPlaybookCreateView.as_view(), name='playbook_create'),
    path('playbooks/<int:pk>/', views.EngagementPlaybookDetailView.as_view(), name='playbook_detail'),
    path('playbooks/<int:pk>/edit/', views.EngagementPlaybookUpdateView.as_view(), name='playbook_update'),
    
    # Playbook Steps
    path('playbooks/<int:playbook_id>/steps/add/', views.PlaybookStepCreateView.as_view(), name='playbook_step_create'),
    path('playbooks/steps/<int:pk>/edit/', views.PlaybookStepUpdateView.as_view(), name='playbook_step_update'),
    path('playbooks/steps/<int:pk>/delete/', views.PlaybookStepDeleteView.as_view(), name='playbook_step_delete'),
    
    # Engagement Workflows
    path('workflows/', views.EngagementWorkflowListView.as_view(), name='workflow_list'),
    path('workflows/create/', views.EngagementWorkflowCreateView.as_view(), name='workflow_create'),
    path('workflows/<int:pk>/edit/', views.EngagementWorkflowUpdateView.as_view(), name='workflow_update'),
    path('workflows/<int:pk>/delete/', views.EngagementWorkflowDeleteView.as_view(), name='workflow_delete'),
    
    # Attribution Reports
    path('reports/attribution/', views.AttributionReportView.as_view(), name='attribution_report'),
    
    # Playbooks
    path('playbooks/', views.EngagementPlaybookListView.as_view(), name='playbook_list'),
    path('playbooks/create/', views.EngagementPlaybookCreateView.as_view(), name='playbook_create'),
    path('playbooks/<int:pk>/', views.EngagementPlaybookDetailView.as_view(), name='playbook_detail'),
    path('playbooks/<int:pk>/edit/', views.EngagementPlaybookUpdateView.as_view(), name='playbook_update'),
    path('playbooks/<int:pk>/clone/', views.PlaybookCloneView.as_view(), name='playbook_clone'),
    path('playbooks/<int:pk>/execute/', views.PlaybookExecutionStartView.as_view(), name='playbook_execute'),
    
    # Playbook Executions
    path('playbook-executions/<int:pk>/', views.PlaybookExecutionDetailView.as_view(), name='playbook_execution_detail'),
    path('playbook-executions/<int:pk>/complete/', views.PlaybookExecutionCompleteView.as_view(), name='playbook_execution_complete'),

    # Playbook Steps
    path('playbooks/<int:playbook_id>/steps/add/', views.PlaybookStepCreateView.as_view(), name='playbook_step_create'),
    path('playbooks/steps/<int:pk>/edit/', views.PlaybookStepUpdateView.as_view(), name='playbook_step_update'),
    path('playbooks/steps/<int:pk>/delete/', views.PlaybookStepDeleteView.as_view(), name='playbook_step_delete'),

    
    # Incoming webhooks with HMAC verification
    path('incoming-webhook/<int:webhook_id>/', views.IncomingWebhookView.as_view(), name='incoming_webhook'),


    
    # Incoming webhooks with HMAC verification
    path('incoming-webhook/<int:webhook_id>/', views.IncomingWebhookView.as_view(), name='incoming_webhook'),
    
    # API endpoints
    path('api/events/', api_views.EngagementEventListCreateAPIView.as_view(), name='api_event_list_create'),
    path('api/events/<int:pk>/', api_views.EngagementEventDetailAPIView.as_view(), name='api_event_detail'),
    path('api/events/bulk-create/', api_views.BulkEngagementEventCreateAPIView.as_view(), name='api_bulk_event_create'),
    path('api/actions/', api_views.NextBestActionListCreateAPIView.as_view(), name='api_action_list_create'),
    path('api/actions/<int:pk>/', api_views.NextBestActionDetailAPIView.as_view(), name='api_action_detail'),
    path('api/statuses/', api_views.EngagementStatusListAPIView.as_view(), name='api_status_list'),
    path('api/webhooks/', api_views.EngagementWebhookListCreateAPIView.as_view(), name='api_webhook_list_create'),
    path('api/webhooks/<int:pk>/', api_views.EngagementWebhookDetailAPIView.as_view(), name='api_webhook_detail'),


]