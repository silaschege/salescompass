# apps/marketing/urls.py
from django.urls import path, re_path
from . import views

app_name = 'marketing'
urlpatterns = [
    # Campaign CRUD
    path('', views.MarketingCampaignListView.as_view(), name='list'),
    path('create/', views.MarketingCampaignCreateView.as_view(), name='create'),
    path('<int:pk>/', views.MarketingCampaignDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.MarketingCampaignUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.MarketingCampaignDeleteView.as_view(), name='delete'),
    path('<int:pk>/send/', views.SendCampaignView.as_view(), name='send_campaign'),
    
    # Email Templates
    path('templates/', views.EmailTemplateListView.as_view(), name='template_list'),
    path('templates/builder/', views.TemplateBuilderView.as_view(), name='template_builder'),
    path('templates/create/', views.EmailTemplateCreateView.as_view(), name='template_create'),
    path('templates/preview/', views.TemplatePreviewView.as_view(), name='template_preview'),
    path('templates/<int:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/preview/', views.EmailTemplatePreviewView.as_view(), name='template_detail_preview'),
    path('templates/<int:pk>/activate/', views.ActivateTemplateView.as_view(), name='activate_template'),
    path('templates/<int:pk>/deactivate/', views.DeactivateTemplateView.as_view(), name='deactivate_template'),
    
    # Landing Pages
    path('landing-pages/', views.LandingPageListView.as_view(), name='landing_page_list'),
    path('landing-pages/create/', views.LandingPageCreateView.as_view(), name='landing_page_create'),
    path('landing-pages/<int:pk>/edit/', views.LandingPageUpdateView.as_view(), name='landing_page_update'),
    path('landing-pages/<int:pk>/builder/', views.LandingPageCreateView.as_view(), name='landing_builder'),
    
    # A/B Tests
    path('ab-tests/', views.AbTestListView.as_view(), name='ab_test_list'),
    path('ab-tests/create/', views.AbTestCreateView.as_view(), name='ab_test_create'),
    
    # Campaign Recipients
    path('recipients/<int:campaign_id>/', views.CampaignRecipientListView.as_view(), name='recipient_list'),
    
    # Marketing engagement tracking
    path('api/track-engagement/', views.TrackEngagementView.as_view(), name='track_engagement'),
    path('track/email-open/<int:recipient_id>/', views.track_email_open, name='track_email_open'),
    path('track/link-click/<int:recipient_id>/', views.track_link_click, name='track_link_click'),
    path('track/landing-page/<int:landing_page_id>/visit/', views.track_landing_page_visit, name='track_landing_page_visit'),
    
    # Unsubscribe
    path('unsubscribe/<int:recipient_id>/', views.UnsubscribeView.as_view(), name='unsubscribe'),
    
    # Calendar
    path('calendar/', views.CampaignCalendarView.as_view(), name='campaign_calendar'),
    path('api/update-schedule/', views.UpdateCampaignScheduleView.as_view(), name='update_campaign_schedule'),
    
    # Performance

    
    # Next Best Action (from engagement module)
    path('api/complete-action/', views.CompleteNextBestActionView.as_view(), name='complete_next_best_action'),

    # ... existing URLs ...

# Campaign Performance URLs
path('performance/list/', views.CampaignPerformanceListView.as_view(), name='performance_list'),
path('performance/<int:pk>/', views.CampaignPerformanceDetailView.as_view(), name='performance_detail'),
path('performance/create/', views.CampaignPerformanceCreateView.as_view(), name='performance_create'),
path('performance/<int:pk>/edit/', views.CampaignPerformanceUpdateView.as_view(), name='performance_update'),
path('performance/<int:pk>/delete/', views.CampaignPerformanceDeleteView.as_view(), name='performance_delete'),
path('performance/analytics/', views.CampaignPerformanceAnalyticsView.as_view(), name='performance_analytics'),

# Landing Page Block URLs
path('landing-pages/<int:landing_page_id>/blocks/', views.LandingPageBlockListView.as_view(), name='landing_page_blocks'),
path('landing-pages/<int:landing_page_id>/blocks/create/', views.LandingPageBlockCreateView.as_view(), name='landing_page_block_create'),
path('landing-page-blocks/<int:pk>/edit/', views.LandingPageBlockUpdateView.as_view(), name='landing_page_block_update'),
path('landing-page-blocks/<int:pk>/delete/', views.LandingPageBlockDeleteView.as_view(), name='landing_page_block_delete'),

# AJAX URLs for Builder
path('ajax/landing-pages/<int:landing_page_id>/blocks/update/', views.UpdateLandingPageBlocksView.as_view(), name='update_landing_page_blocks'),
path('ajax/landing-pages/<int:landing_page_id>/blocks/get/', views.GetLandingPageBlocksView.as_view(), name='get_landing_page_blocks'),

# Drip Campaign URLs
path('drip-campaigns/', views.DripCampaignListView.as_view(), name='drip_campaign_list'),
path('drip-campaigns/create/', views.DripCampaignCreateView.as_view(), name='drip_campaign_create'),
path('drip-campaigns/<int:pk>/', views.DripCampaignDetailView.as_view(), name='drip_campaign_detail'),
path('drip-campaigns/<int:pk>/edit/', views.DripCampaignUpdateView.as_view(), name='drip_campaign_update'),
path('drip-campaigns/<int:campaign_pk>/steps/add/', views.DripStepCreateView.as_view(), name='drip_step_create'),
path('drip-enrollments/create/', views.DripEnrollmentCreateView.as_view(), name='drip_enrollment_create'),
]