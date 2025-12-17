from django.urls import path, include
from . import views

app_name = 'automation'

urlpatterns = [
    # CRUD operations
    path('', include('automation.urls_rules')), # Business Rules
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
    
    # Workflow CRUD
    path('workflows/', views.WorkflowListView.as_view(), name='workflow_list'),
    path('workflow/create/', views.WorkflowCreateView.as_view(), name='workflow_create'),
    path('workflow/<int:pk>/', views.WorkflowDetailView.as_view(), name='workflow_detail'),
    path('workflow/<int:pk>/update/', views.WorkflowUpdateView.as_view(), name='workflow_update'),
    path('workflow/<int:pk>/delete/', views.WorkflowDeleteView.as_view(), name='workflow_delete'),
    
    # Workflow Actions
    path('workflow-actions/', views.WorkflowActionListView.as_view(), name='workflow_action_list'),
    path('workflow-action/<int:pk>/', views.WorkflowActionDetailView.as_view(), name='workflow_action_detail'),
    path('workflow-action/<int:pk>/edit/', views.WorkflowActionUpdateView.as_view(), name='workflow_action_update'),
    path('workflow-action/<int:pk>/delete/', views.WorkflowActionDeleteView.as_view(), name='workflow_action_delete'),
    
    # Workflow Executions
    path('workflow-executions/', views.WorkflowExecutionListView.as_view(), name='workflow_execution_list'),
    path('workflow-execution/<int:pk>/', views.WorkflowExecutionDetailView.as_view(), name='workflow_execution_detail'),
    path('workflow-execution/<int:pk>/edit/', views.WorkflowExecutionUpdateView.as_view(), name='workflow_execution_update'),
    
    # Workflow Triggers
    path('workflow-triggers/', views.WorkflowTriggerListView.as_view(), name='workflow_trigger_list'),
    path('workflow-trigger/<int:pk>/', views.WorkflowTriggerDetailView.as_view(), name='workflow_trigger_detail'),
    path('workflow-trigger/<int:pk>/edit/', views.WorkflowTriggerUpdateView.as_view(), name='workflow_trigger_update'),
    path('workflow-trigger/<int:pk>/delete/', views.WorkflowTriggerDeleteView.as_view(), name='workflow_trigger_delete'),
    
    # Workflow Templates
    path('workflow-templates/', views.WorkflowTemplateListView.as_view(), name='workflow_template_list'),
    path('workflow-template/<int:pk>/', views.WorkflowTemplateDetailView.as_view(), name='workflow_template_detail'),
    path('workflow-template/<int:pk>/edit/', views.WorkflowTemplateUpdateView.as_view(), name='workflow_template_update'),
    path('workflow-template/<int:pk>/delete/', views.WorkflowTemplateDeleteView.as_view(), name='workflow_template_delete'),
]
