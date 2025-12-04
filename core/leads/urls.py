from django.urls import path, re_path
from . import views
from . import api

app_name = 'leads'
urlpatterns = [
    # CRUD
    path('', views.LeadListView.as_view(), name='leads_list'),
    path('create/', views.LeadCreateView.as_view(), name='create'),
    path('<int:pk>/', views.LeadDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.LeadUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.LeadDeleteView.as_view(), name='delete'),

    # Pipeline Kanban
    path('pipeline/', views.LeadPipelineView.as_view(), name='pipeline'),

    # account to lead creation
    path('accounts/<int:account_pk>/quick-create/', views.quick_create_lead_from_account, name='quick_create_from_account'),

    # Analytics
    path('analytics/', views.LeadAnalyticsView.as_view(), name='leads_analytics'),
    
    # Web-to-Lead
    path('web-to-lead/', views.WebToLeadListView.as_view(), name='web_to_lead_list'),
    path('web-to-lead/builder/', views.WebToLeadBuilderView.as_view(), name='web_to_lead_builder'),
    path('web-to-lead/<int:form_id>/', views.WebToLeadFormView.as_view(), name='web_to_lead_form'),
    
    # AJAX
    path('<int:lead_id>/update-status/', views.update_lead_status, name='update_status'),
    
    # Public API
    path('api/v1/capture/', api.WebToLeadView.as_view(), name='api_lead_capture'),
]