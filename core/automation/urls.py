from django.urls import path
from . import views

app_name = 'automation'

urlpatterns = [
    # CRUD operations
    path('', views.AutomationListView.as_view(), name='list'),
    path('create/', views.AutomationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AutomationDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AutomationUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.AutomationDeleteView.as_view(), name='delete'),
    
    # API endpoints (for integration with other modules)
    path('api/trigger/', views.TriggerAutomationView.as_view(), name='trigger_automation'),
    path('api/execute/<int:automation_id>/', views.ExecuteAutomationView.as_view(), name='execute_automation'),
    
    # Monitoring and analytics
    path('logs/', views.AutomationLogListView.as_view(), name='log_list'),
    path('logs/<int:pk>/', views.AutomationLogDetailView.as_view(), name='log_detail'),
    
    # System management
    path('system/', views.SystemAutomationListView.as_view(), name='system_list'),
    path('import/', views.import_automation_view, name='import'),
    path('export/', views.export_automation_view, name='export'),

    # automation conditions
    path('action/', views.AutomationActionCreateView.as_view(), name='action_create'),
    path('conditions/create/', views.AutomationConditionCreateView.as_view(), name='condition_create'),
    
    # Workflow Builder
    path('builder/', views.workflow_builder, name='workflow_builder'),
    path('builder/<int:workflow_id>/', views.workflow_builder, name='workflow_builder_edit'),
    path('api/save-workflow/', views.save_workflow, name='save_workflow'),
    path('api/load-workflow/<int:workflow_id>/', views.load_workflow, name='load_workflow'),
]