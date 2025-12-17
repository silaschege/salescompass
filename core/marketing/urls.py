from django.urls import path
from . import views
from . import views_analytics

app_name = 'marketing'

urlpatterns = [
    # Dynamic choices API
    path('api/dynamic-choices/<str:model_name>/', views.get_marketing_dynamic_choices, name='get_marketing_dynamic_choices'),
    
    # CAC Analytics
    path('cac-analytics/', views.cac_analytics, name='cac_analytics'),
    
    # Campaign Status
    path('campaign-status/', views.CampaignStatusListView.as_view(), name='campaign_status_list'),
    path('campaign-status/create/', views.CampaignStatusCreateView.as_view(), name='campaign_status_create'),
    path('campaign-status/<int:pk>/update/', views.CampaignStatusUpdateView.as_view(), name='campaign_status_update'),
    path('campaign-status/<int:pk>/delete/', views.CampaignStatusDeleteView.as_view(), name='campaign_status_delete'),
    
    # Email Provider
    path('email-provider/', views.EmailProviderListView.as_view(), name='email_provider_list'),
    path('email-provider/create/', views.EmailProviderCreateView.as_view(), name='email_provider_create'),
    path('email-provider/<int:pk>/update/', views.EmailProviderUpdateView.as_view(), name='email_provider_update'),
    path('email-provider/<int:pk>/delete/', views.EmailProviderDeleteView.as_view(), name='email_provider_delete'),
    
    # Block Type
    path('block-type/', views.BlockTypeListView.as_view(), name='block_type_list'),
    path('block-type/create/', views.BlockTypeCreateView.as_view(), name='block_type_create'),
    path('block-type/<int:pk>/update/', views.BlockTypeUpdateView.as_view(), name='block_type_update'),
    path('block-type/<int:pk>/delete/', views.BlockTypeDeleteView.as_view(), name='block_type_delete'),
    
    # Email Category
    path('email-category/', views.EmailCategoryListView.as_view(), name='email_category_list'),
    path('email-category/create/', views.EmailCategoryCreateView.as_view(), name='email_category_create'),
    path('email-category/<int:pk>/update/', views.EmailCategoryUpdateView.as_view(), name='email_category_update'),
    path('email-category/<int:pk>/delete/', views.EmailCategoryDeleteView.as_view(), name='email_category_delete'),
    
    # Message Type
    path('message-type/', views.MessageTypeListView.as_view(), name='message_type_list'),
    path('message-type/create/', views.MessageTypeCreateView.as_view(), name='message_type_create'),
    path('message-type/<int:pk>/update/', views.MessageTypeUpdateView.as_view(), name='message_type_update'),
    path('message-type/<int:pk>/delete/', views.MessageTypeDeleteView.as_view(), name='message_type_delete'),
    
    # Message Category
    path('message-category/', views.MessageCategoryListView.as_view(), name='message_category_list'),
    path('message-category/create/', views.MessageCategoryCreateView.as_view(), name='message_category_create'),
    path('message-category/<int:pk>/update/', views.MessageCategoryUpdateView.as_view(), name='message_category_update'),
    path('message-category/<int:pk>/delete/', views.MessageCategoryDeleteView.as_view(), name='message_category_delete'),
    
    # Campaign
    path('campaign/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaign/create/', views.CampaignCreateView.as_view(), name='campaign_create'),
    path('campaign/<int:pk>/update/', views.CampaignUpdateView.as_view(), name='campaign_update'),
    path('campaign/<int:pk>/delete/', views.CampaignDeleteView.as_view(), name='campaign_delete'),
    
    # Email Template
    path('email-template/', views.EmailTemplateListView.as_view(), name='email_template_list'),
    path('email-template/create/', views.EmailTemplateCreateView.as_view(), name='email_template_create'),
    path('email-template/<int:pk>/update/', views.EmailTemplateUpdateView.as_view(), name='email_template_update'),
    path('email-template/<int:pk>/delete/', views.EmailTemplateDeleteView.as_view(), name='email_template_delete'),
    
    # Landing Page Block
    path('landing-page-block/', views.LandingPageBlockListView.as_view(), name='landing_page_block_list'),
    path('landing-page-block/create/', views.LandingPageBlockCreateView.as_view(), name='landing_page_block_create'),
    path('landing-page-block/<int:pk>/update/', views.LandingPageBlockUpdateView.as_view(), name='landing_page_block_update'),
    path('landing-page-block/<int:pk>/delete/', views.LandingPageBlockDeleteView.as_view(), name='landing_page_block_delete'),
    
    # Message Template
    path('message-template/', views.MessageTemplateListView.as_view(), name='message_template_list'),
    path('message-template/create/', views.MessageTemplateCreateView.as_view(), name='message_template_create'),
    path('message-template/<int:pk>/update/', views.MessageTemplateUpdateView.as_view(), name='message_template_update'),
    path('message-template/<int:pk>/delete/', views.MessageTemplateDeleteView.as_view(), name='message_template_delete'),
    
    # Email Campaign
    path('email-campaign/', views.EmailCampaignListView.as_view(), name='email_campaign_list'),
    path('email-campaign/create/', views.EmailCampaignCreateView.as_view(), name='email_campaign_create'),
    path('email-campaign/<int:pk>/update/', views.EmailCampaignUpdateView.as_view(), name='email_campaign_update'),
    path('email-campaign/<int:pk>/delete/', views.EmailCampaignDeleteView.as_view(), name='email_campaign_delete'),

    # Email Integration
    path('email-integration/', views.EmailIntegrationListView.as_view(), name='email_integration_list'),
    path('email-integration/create/', views.EmailIntegrationCreateView.as_view(), name='email_integration_create'),
    path('email-integration/<int:pk>/edit/', views.EmailIntegrationUpdateView.as_view(), name='email_integration_update'),
    path('email-integration/<int:pk>/delete/', views.EmailIntegrationDeleteView.as_view(), name='email_integration_delete'),
    
    # Analytics
    path('analytics/performance/', views_analytics.CampaignPerformanceView.as_view(), name='campaign_performance'),
]
