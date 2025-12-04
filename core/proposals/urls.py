from django.urls import path, re_path
from . import views

app_name = 'proposals'
urlpatterns = [
    # Dashboard
    path('', views.EngagementDashboardView.as_view(), name='engagement_dashboard'),
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
    
  
]