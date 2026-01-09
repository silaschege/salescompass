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
    
    # Promoter Advocacy
    path('promoters/', views.PromoterAdvocacyView.as_view(), name='promoter_advocacy'),
    path('promoters/referrals/', views.PromoterReferralListView.as_view(), name='promoter_referrals'),
    path('promoters/referrals/<int:pk>/update/', views.PromoterReferralUpdateView.as_view(), name='update_promoter_referral'),
    
    # Survey Submission
    path('submit/<int:survey_id>/', views.SubmitNPSView.as_view(), name='submit_nps'),
    
    # A/B Testing
    path('ab-test/create/', views.CreateNpsAbTestView.as_view(), name='create_nps_ab_test'),
    
    # In-App Widget
    path('widget/', views.InAppNPSWidgetView.as_view(), name='in_app_widget'),
    path('embed-example/', views.EmbedNPSWidgetView.as_view(), name='embed_example'),
    
    # Escalation Rules
    path('escalation-rules/', views.NpsEscalationRuleListView.as_view(), name='escalation_rules'),
    path('escalation-rules/create/', views.NpsEscalationRuleCreateView.as_view(), name='create_escalation_rule'),
    path('escalation-rules/<int:pk>/update/', views.NpsEscalationRuleUpdateView.as_view(), name='update_escalation_rule'),


    
    # Escalation Actions
    path('escalation-actions/', views.NpsEscalationActionListView.as_view(), name='escalation_actions'),
    path('escalation-actions/create/', views.NpsEscalationActionCreateView.as_view(), name='create_escalation_action'),
    path('escalation-actions/<int:pk>/update/', views.NpsEscalationActionUpdateView.as_view(), name='update_escalation_action'),
    
    # Escalation Action Logs
    path('escalation-action-logs/', views.NpsEscalationActionLogListView.as_view(), name='escalation_action_logs'),
    
    # Trend Snapshots
    path('trend-snapshots/', views.NpsTrendSnapshotListView.as_view(), name='trend_snapshots'),
]
