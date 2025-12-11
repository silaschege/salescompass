from django.urls import path, re_path
from . import views
from . import api

app_name = 'leads'
urlpatterns = [
    # CRUD
    path('', views.LeadListView.as_view(), name='lead_list'),
    path('create/', views.LeadCreateView.as_view(), name='lead_create'),
    path('<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('<int:pk>/edit/', views.LeadUpdateView.as_view(), name='lead_update'),
    path('<int:pk>/delete/', views.DeleteView.as_view(), name='lead_delete'),

    # Pipeline Kanban
    path('pipeline/', views.LeadPipelineView.as_view(), name='lead_pipeline'),

    # account to lead creation
    path('accounts/<int:account_pk>/quick-create/', views.quick_create_lead_from_account, name='quick_create_from_account'),

    # Analytics
    path('analytics/', views.LeadAnalyticsView.as_view(), name='lead_analytics'),
    
    # CAC Analytics
    path('cac-analytics/', views.CACAnalyticsView.as_view(), name='cac_analytics'),
    path('channel-metrics/<str:channel>/', views.ChannelMetricsView.as_view(), name='channel_metrics'),
    path('campaign-metrics/<str:campaign>/', views.CampaignMetricsView.as_view(), name='campaign_metrics'),
    
    # Marketing Channel Management
    path('marketing-channels/', views.MarketingChannelListView.as_view(), name='marketingchannel_list'),
    path('marketing-channels/create/', views.MarketingChannelCreateView.as_view(), name='marketingchannel_create'),
    path('marketing-channels/<int:pk>/edit/', views.MarketingChannelUpdateView.as_view(), name='marketingchannel_update'),
    path('marketing-channels/<int:pk>/delete/', views.MarketingChannelDeleteView.as_view(), name='marketingchannel_delete'),
    
    # Web-to-Lead
    path('web-to-lead/', views.WebToLeadListView.as_view(), name='web_to_lead_list'),
    path('web-to-lead/builder/', views.WebToLeadBuilderView.as_view(), name='web_to_lead_builder'),
    path('web-to-lead/<int:form_id>/', views.WebToLeadFormView.as_view(), name='web_to_lead_form'),
    
    # AJAX
    path('<int:lead_id>/update-status/', views.update_lead_status, name='update_status'),
    path('ajax/get-dynamic-choices/<str:choice_model_name>/', views.get_dynamic_choices, name='get_dynamic_choices'),
    
    # Public API
    path('api/v1/capture/', api.WebToLeadView.as_view(), name='api_lead_capture'),
]
