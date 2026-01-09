from django.urls import path
from . import views

app_name = 'settings_app'

urlpatterns = [
    # Dashboard
    path('', views.SettingsDashboardView.as_view(), name='dashboard'),
    
    # CRM Settings
    path('crm/', views.CrmSettingsListView.as_view(), name='list'),
    path('crm/<int:pk>/edit/', views.CrmSettingsUpdateView.as_view(), name='update'),
    
    # Tenant Settings
    path('tenant/', views.TenantSettingsView.as_view(), name='tenant_settings'),
    

    # Lead Settings
    path('leads/statuses/', views.LeadStatusListView.as_view(), name='lead_status_list'),
    path('leads/statuses/create/', views.LeadStatusCreateView.as_view(), name='lead_status_create'),
    path('leads/statuses/<int:pk>/edit/', views.LeadStatusUpdateView.as_view(), name='lead_status_update'),
    path('leads/statuses/<int:pk>/delete/', views.LeadStatusDeleteView.as_view(), name='lead_status_delete'),
    
    path('leads/sources/', views.LeadSourceListView.as_view(), name='lead_source_list'),
    path('leads/sources/create/', views.LeadSourceCreateView.as_view(), name='lead_source_create'),
    path('leads/sources/<int:pk>/edit/', views.LeadSourceUpdateView.as_view(), name='lead_source_update'),
    path('leads/sources/<int:pk>/delete/', views.LeadSourceDeleteView.as_view(), name='lead_source_delete'),
    
    # Opportunity Settings
    path('opportunities/stages/', views.OpportunityStageListView.as_view(), name='opportunity_stage_list'),
    path('opportunities/stages/create/', views.OpportunityStageCreateView.as_view(), name='opportunity_stage_create'),
    path('opportunities/stages/<int:pk>/edit/', views.OpportunityStageUpdateView.as_view(), name='opportunity_stage_update'),
    path('opportunities/stages/<int:pk>/delete/', views.OpportunityStageDeleteView.as_view(), name='opportunity_stage_delete'),
    
    # Custom Fields
    path('custom-fields/', views.CustomFieldListView.as_view(), name='custom_field_list'),
    path('custom-fields/create/', views.CustomFieldCreateView.as_view(), name='custom_field_create'),
    path('custom-fields/<int:pk>/edit/', views.CustomFieldUpdateView.as_view(), name='custom_field_update'),
    path('custom-fields/<int:pk>/delete/', views.CustomFieldDeleteView.as_view(), name='custom_field_delete'),
    
    # Module Labels
    path('module-labels/', views.ModuleLabelListView.as_view(), name='module_label_list'),
    path('module-labels/create/', views.ModuleLabelCreateView.as_view(), name='module_label_create'),
    path('module-labels/<int:pk>/edit/', views.ModuleLabelUpdateView.as_view(), name='module_label_update'),
    path('module-labels/<int:pk>/delete/', views.ModuleLabelDeleteView.as_view(), name='module_label_delete'),
    
    # Assignment Rules
    path('assignment-rules/', views.AssignmentRuleListView.as_view(), name='assignment_rule_list'),
    path('assignment-rules/create/', views.AssignmentRuleCreateView.as_view(), name='assignment_rule_create'),
    path('assignment-rules/<int:pk>/edit/', views.AssignmentRuleUpdateView.as_view(), name='assignment_rule_update'),
    path('assignment-rules/<int:pk>/delete/', views.AssignmentRuleDeleteView.as_view(), name='assignment_rule_delete'),
    
    # Pipeline Stages
    path('pipeline-stages/', views.PipelineStageListView.as_view(), name='pipeline_stage_list'),
    path('pipeline-stages/create/', views.PipelineStageCreateView.as_view(), name='pipeline_stage_create'),
    path('pipeline-stages/<int:pk>/edit/', views.PipelineStageUpdateView.as_view(), name='pipeline_stage_update'),
    path('pipeline-stages/<int:pk>/delete/', views.PipelineStageDeleteView.as_view(), name='pipeline_stage_delete'),
    
    # API Keys
    path('api-keys/', views.APIKeyListView.as_view(), name='apikey_list'),
    path('api-keys/create/', views.APIKeyCreateView.as_view(), name='apikey_create'),
    path('api-keys/<int:pk>/delete/', views.APIKeyDeleteView.as_view(), name='apikey_delete'),
    
    # Webhooks
    path('webhooks/', views.WebhookListView.as_view(), name='webhook_list'),
    path('webhooks/create/', views.WebhookCreateView.as_view(), name='webhook_create'),
    path('webhooks/<int:pk>/edit/', views.WebhookUpdateView.as_view(), name='webhook_update'),
    path('webhooks/<int:pk>/delete/', views.WebhookDeleteView.as_view(), name='webhook_delete'),
    
    # Lead Scoring Rules
    path('scoring-rules/', views.ScoringRulesListView.as_view(), name='scoring_rules_list'),
    path('scoring-rules/behavioral/create/', views.BehavioralScoringRuleCreateView.as_view(), name='behavioral_scoring_create'),
    path('scoring-rules/behavioral/<int:pk>/edit/', views.BehavioralScoringRuleUpdateView.as_view(), name='behavioral_scoring_update'),
    path('scoring-rules/behavioral/<int:pk>/delete/', views.BehavioralScoringRuleDeleteView.as_view(), name='behavioral_scoring_delete'),
    path('scoring-rules/demographic/create/',views.DemographicScoringRuleCreateView.as_view(), name='demographic_scoring_create'),
    path('scoring-rules/demographic/<int:pk>/edit/', views.DemographicScoringRuleUpdateView.as_view(), name='demographic_scoring_update'),
    path('scoring-rules/demographic/<int:pk>/delete/', views.DemographicScoringRuleDeleteView.as_view(), name='demographic_scoring_delete'),
    path('scoring-rules/decay/', views.ScoreDecayConfigView.as_view(), name='score_decay_config'),
]