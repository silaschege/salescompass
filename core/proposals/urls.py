from django.urls import path, re_path
from . import views

app_name = 'proposals'
urlpatterns = [
    # Dashboard
    path('', views.ProposalDashboardView.as_view(), name='proposal_dashboard'),
    # CRUD
    path('list/', views.ProposalListView.as_view(), name='list'),
    path('create/', views.ProposalCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProposalDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProposalUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ProposalDeleteView.as_view(), name='delete'),
    
    # Email and PDF
    path('<int:pk>/send-email/', views.SendProposalEmailView.as_view(), name='send_email'),
    path('<int:pk>/generate-pdf/', views.GenerateProposalPDFView.as_view(), name='generate_pdf'),
    
    # Tracking
    path('track/open/<str:token>/', views.track_email_open_view, name='track_open'),
    path('track/click/<str:token>/', views.track_link_click_view, name='track_click'),
    path('<int:pk>/track-view/', views.TrackProposalView.as_view(), name='track_proposal_view'),
    path('<int:pk>/track-esg/', views.TrackESGSectionView.as_view(), name='track_esg_view'),
    
    # Client actions (accept/reject proposals)
    path('<int:pk>/accept/', views.AcceptProposalView.as_view(), name='accept_proposal'),
    path('<int:pk>/reject/', views.RejectProposalView.as_view(), name='reject_proposal'),
    
    # Templates
    path('templates/', views.ProposalTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ProposalTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.ProposalTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.ProposalTemplateDeleteView.as_view(), name='template_delete'),
  
    # Analytics
    path('events/', views.ProposalEventsView.as_view(), name='events'),
    path('analytics/', views.ProposalAnalyticsView.as_view(), name='analytics'),
    
    # Signature
    path('<int:pk>/sign/', views.ProposalSignView.as_view(), name='sign_proposal'),
    path('<int:pk>/save-signature/', views.save_proposal_signature, name='save_signature'),

    # Approval workflow URLs
    path('approval-dashboard/', views.ProposalApprovalsView.as_view(), name='approvals_dashboard'),
    path('<int:pk>/approval/', views.ProposalApprovalDashboardView.as_view(), name='proposal_approval'),
    path('<int:pk>/start-approval/', views.StartApprovalView.as_view(), name='start_approval'),
    path('<int:pk>/submit-approval/', views.SubmitApprovalView.as_view(), name='submit_approval'),
    
    # Approval template URLs
    path('approval-templates/', views.ApprovalTemplateListView.as_view(), name='approval_template_list'),
    path('approval-templates/<int:pk>/', views.ApprovalTemplateDetailView.as_view(), name='approval_template_detail'),
    path('approval-templates/create/', views.ApprovalTemplateCreateView.as_view(), name='approval_template_create'),
    path('approval-templates/<int:pk>/edit/', views.ApprovalTemplateUpdateView.as_view(), name='approval_template_edit'),
    path('approval-templates/manage/', views.ManageApprovalTemplateView.as_view(), name='manage_approval_templates'),
    path('<int:pk>/set-template/', views.ProposalSetTemplateView.as_view(), name='set_approval_template'),
]