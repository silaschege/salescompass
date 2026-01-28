from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'marketing'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='marketing:campaign_list', permanent=False), name='index'),
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
    path('campaign/<int:pk>/clone/', views.clone_campaign, name='campaign_clone'),

    
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
    


    # Analytics & Reports
    path('analytics/performance/', views.CampaignPerformanceView.as_view(), name='campaign_performance'),
    path('analytics/budget-vs-actual/', views.BudgetVsActualView.as_view(), name='budget_vs_actual'),
    path('analytics/pipeline-influence/', views.PipelineInfluenceView.as_view(), name='pipeline_influence'),
    path('analytics/roi-calculator/', views.ROICalculatorView.as_view(), name='roi_calculator'),
    path('api/roi-calculate/', views.ROICalculatorAPIView.as_view(), name='roi_calculator_api'),
    path('analytics/deliverability/', views.DeliverabilityReportView.as_view(), name='deliverability_report'),
    
    # Campaign Calendar
    path('calendar/', views.campaign_calendar_view, name='campaign_calendar'),



    # Segments
    path('segment/', views.SegmentListView.as_view(), name='segment_list'),
    path('segment/create/', views.SegmentCreateView.as_view(), name='segment_create'),
    path('segment/<int:pk>/update/', views.SegmentUpdateView.as_view(), name='segment_update'),
    path('segment/<int:pk>/delete/', views.SegmentDeleteView.as_view(), name='segment_delete'),
    path('segment/<int:pk>/members/', views.segment_members, name='segment_members'),
    path('segment/<int:segment_pk>/members/add/', views.add_segment_member, name='add_segment_member'),
    path('segment/<int:segment_pk>/members/<int:member_pk>/remove/', views.remove_segment_member, name='remove_segment_member'),

    # Nurture Campaigns
    path('nurture/', views.NurtureCampaignListView.as_view(), name='nurture_campaign_list'),
    path('nurture/create/', views.NurtureCampaignCreateView.as_view(), name='nurture_campaign_create'),
    path('nurture/<int:pk>/update/', views.NurtureCampaignUpdateView.as_view(), name='nurture_campaign_update'),
    path('nurture/<int:pk>/delete/', views.NurtureCampaignDeleteView.as_view(), name='nurture_campaign_delete'),

    # Drip Campaigns
    path('drip/', views.DripCampaignListView.as_view(), name='drip_campaign_list'),
    path('drip/create/', views.DripCampaignCreateView.as_view(), name='drip_campaign_create'),
    path('drip/<int:pk>/update/', views.DripCampaignUpdateView.as_view(), name='drip_campaign_update'),
    path('drip/<int:pk>/delete/', views.DripCampaignDeleteView.as_view(), name='drip_campaign_delete'),
    path('drip/<int:drip_pk>/enroll/', views.enroll_in_drip, name='enroll_in_drip'),
    
    # Drip Steps
    path('drip/<int:campaign_pk>/steps/create/', views.DripStepCreateView.as_view(), name='drip_step_create'),
    path('drip/steps/<int:pk>/update/', views.DripStepUpdateView.as_view(), name='drip_step_update'),
    path('drip/steps/<int:pk>/delete/', views.DripStepDeleteView.as_view(), name='drip_step_delete'),

    # A/B Testing
    path('ab-tests/', views.ABTestListView.as_view(), name='ab_test_list'),
    path('ab-tests/create/', views.ABTestCreateView.as_view(), name='ab_test_create'),
    path('ab-tests/<int:pk>/update/', views.ABTestUpdateView.as_view(), name='ab_test_update'),
    path('ab-tests/<int:pk>/delete/', views.ABTestDeleteView.as_view(), name='ab_test_delete'),
    path('ab-tests/<int:pk>/activate/', views.activate_ab_test, name='activate_ab_test'),
    path('ab-tests/<int:pk>/deactivate/', views.deactivate_ab_test, name='deactivate_ab_test'),
    path('ab-tests/<int:pk>/results/', views.ab_test_results, name='ab_test_results'),
    path('ab-tests/<int:pk>/declare-winner/', views.declare_ab_test_winner, name='declare_ab_test_winner'),
    
    # Automated A/B Tests
    path('ab-automated/', views.ABAutomatedTestListView.as_view(), name='ab_automated_test_list'),
    path('ab-automated/create/', views.ABAutomatedTestCreateView.as_view(), name='ab_automated_test_create'),
    path('ab-automated/<int:pk>/update/', views.ABAutomatedTestUpdateView.as_view(), name='ab_automated_test_update'),
    path('ab-automated/<int:pk>/delete/', views.ABAutomatedTestDeleteView.as_view(), name='ab_automated_test_delete'),

    # A/B Tracking
    path('ab-track/open/<int:variant_id>/<str:recipient_email>/', views.track_ab_test_open, name='track_ab_test_open'),
    path('ab-track/click/<int:variant_id>/<str:recipient_email>/', views.track_ab_test_click, name='track_ab_test_click'),
]
