from django.urls import path
from . import views
 
app_name = 'cases'
urlpatterns = [
    # CRUD
    path('', views.CaseListView.as_view(), name='case_list'),
    path('create/', views.CaseCreateView.as_view(), name='case_create'),
    path('<int:pk>/', views.CaseDetailView.as_view(), name='case_detail'),
    path('<int:pk>/edit/', views.CaseUpdateView.as_view(), name='case_update'),
    path('<int:pk>/delete/', views.CaseDeleteView.as_view(), name='case_delete'),
    
    # CSAT
    path('csat/survey/', views.CsatSurveyView.as_view(), name='csat_survey'),
    path('csat/thank-you/', views.CsatThankYouView.as_view(), name='csat_thank_you'),
    
    # Kanban
    path('kanban/', views.CaseKanbanView.as_view(), name='case_kanban'),

    path('detractors/', views.DetractorKanbanView.as_view(), name='detractor_kanban'),
    
    # Dashboard
    path('sla-dashboard/', views.SlaDashboardView.as_view(), name='sla_dashboard'),

    # AJAX Endpoints
        # Detractor status update
    path('api/update-detractor-status/', views.UpdateDetractorStatusView.as_view(), name='update_detractor_status'),
    path('api/update-case-status/', views.UpdateCaseStatusView.as_view(), name='update_case_status'),
    


    # Assignment Rules
    path('assignment-rules/', views.AssignmentRuleListView.as_view(), name='assignment_rule_list'),
    path('assignment-rules/create/', views.AssignmentRuleCreateView.as_view(), name='assignment_rule_create'),
    path('assignment-rules/<int:pk>/edit/', views.AssignmentRuleUpdateView.as_view(), name='assignment_rule_update'),
    path('assignment-rules/<int:pk>/delete/', views.AssignmentRuleDeleteView.as_view(), name='assignment_rule_delete'),

    # Assignment Rule Detail (missing)
    path('assignment-rules/<int:pk>/', views.AssignmentRuleDetailView.as_view(), name='assignment_rule_detail'),
    
    # CSAT Response Management
    path('csat-responses/', views.CsatResponseListView.as_view(), name='csat_response_list'),
    path('csat-responses/<int:pk>/', views.CsatResponseDetailView.as_view(), name='csat_response_detail'),
    
    # Case Comments
    path('comments/', views.CaseCommentListView.as_view(), name='case_comment_list'),
    path('comments/create/', views.CaseCommentCreateView.as_view(), name='case_comment_create'),
    path('comments/<int:pk>/edit/', views.CaseCommentUpdateView.as_view(), name='case_comment_update'),
    path('comments/<int:pk>/delete/', views.CaseCommentDeleteView.as_view(), name='case_comment_delete'),
    
    # Case Attachments
    path('attachments/', views.CaseAttachmentListView.as_view(), name='case_attachment_list'),
    path('attachments/create/', views.CaseAttachmentCreateView.as_view(), name='case_attachment_create'),
    path('attachments/<int:pk>/edit/', views.CaseAttachmentUpdateView.as_view(), name='case_attachment_update'),
    path('attachments/<int:pk>/delete/', views.CaseAttachmentDeleteView.as_view(), name='case_attachment_delete'),
    
    # SLA Policies
    path('sla-policies/', views.SlaPolicyListView.as_view(), name='sla_policy_list'),
    path('sla-policies/create/', views.SlaPolicyCreateView.as_view(), name='sla_policy_create'),
    path('sla-policies/<int:pk>/', views.SlaPolicyDetailView.as_view(), name='sla_policy_detail'),
    path('sla-policies/<int:pk>/edit/', views.SlaPolicyUpdateView.as_view(), name='sla_policy_update'),
    path('sla-policies/<int:pk>/delete/', views.SlaPolicyDeleteView.as_view(), name='sla_policy_delete'),
]


