from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Task CRUD
    path('', views.TaskListView.as_view(), name='list'),
    path('undone/', views.UndoneWorkView.as_view(), name='undone_work'),
    path('create/', views.TaskCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='delete'),
    
    # Task actions
    path('api/complete/', views.CompleteTaskView.as_view(), name='complete_task'),
    path('<int:task_id>/comments/add/', views.AddTaskCommentView.as_view(), name='add_comment'),
    path('<int:task_id>/attachments/upload/', views.UploadTaskAttachmentView.as_view(), name='upload_attachment'),
    
    # Views
    path('dashboard/', views.TaskDashboardView.as_view(), name='dashboard'),
    path('calendar/', views.TaskCalendarView.as_view(), name='calendar'),
    path('my-tasks/', views.MyTasksView.as_view(), name='my_tasks'),
    path('kanban/', views.TaskKanbanView.as_view(), name='kanban'),
    
    # Related object task creation
    path('accounts/<int:account_pk>/create/', views.TaskCreateView.as_view(), name='create_from_account'),
    path('opportunities/<int:opportunity_pk>/create/', views.TaskCreateView.as_view(), name='create_from_opportunity'),
    path('leads/<int:lead_pk>/create/', views.TaskCreateView.as_view(), name='create_from_lead'),
    path('cases/<int:case_pk>/create/', views.TaskCreateView.as_view(), name='create_from_case'),
    
    # Task Templates
    path('templates/', views.TaskTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.TaskTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.TaskTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.TaskTemplateDeleteView.as_view(), name='template_delete'),
    
    # Task Priority Management
    path('priorities/', views.TaskPriorityListView.as_view(), name='priority_list'),
    path('priorities/create/', views.TaskPriorityCreateView.as_view(), name='priority_create'),
    path('priorities/<int:pk>/edit/', views.TaskPriorityUpdateView.as_view(), name='priority_update'),
    path('priorities/<int:pk>/delete/', views.TaskPriorityDeleteView.as_view(), name='priority_delete'),
    
    # Task Status Management
    path('statuses/', views.TaskStatusListView.as_view(), name='status_list'),
    path('statuses/create/', views.TaskStatusCreateView.as_view(), name='status_create'),
    path('statuses/<int:pk>/edit/', views.TaskStatusUpdateView.as_view(), name='status_update'),
    path('statuses/<int:pk>/delete/', views.TaskStatusDeleteView.as_view(), name='status_delete'),
    
    # Task Type Management
    path('types/', views.TaskTypeListView.as_view(), name='type_list'),
    path('types/create/', views.TaskTypeCreateView.as_view(), name='type_create'),
    path('types/<int:pk>/edit/', views.TaskTypeUpdateView.as_view(), name='type_update'),
    path('types/<int:pk>/delete/', views.TaskTypeDeleteView.as_view(), name='type_delete'),
    
    # Recurrence Pattern Management
    path('patterns/', views.RecurrencePatternListView.as_view(), name='pattern_list'),
    path('patterns/create/', views.RecurrencePatternCreateView.as_view(), name='pattern_create'),
    path('patterns/<int:pk>/edit/', views.RecurrencePatternUpdateView.as_view(), name='pattern_update'),
    path('patterns/<int:pk>/delete/', views.RecurrencePatternDeleteView.as_view(), name='pattern_delete'),
    
    # Task Dependencies
    path('dependencies/create/', views.TaskDependencyCreateView.as_view(), name='dependency_create'),
    path('dependencies/<int:pk>/delete/', views.TaskDependencyDeleteView.as_view(), name='dependency_delete'),
    
    # Task Comments
    path('<int:pk>/comments/', views.TaskCommentsView.as_view(), name='comments'),
    
    # Task Attachments
    path('<int:pk>/attachments/upload/', views.UploadTaskAttachmentView.as_view(), name='attachment_upload'),
    path('<int:pk>/attachments/<int:attachment_pk>/download/', views.DownloadTaskAttachmentView.as_view(), name='attachment_download'),
    
    # Task Time Entries
    path('<int:pk>/time-entries/add/', views.AddTaskTimeEntryView.as_view(), name='time_entry_add'),
    path('<int:pk>/time-entries/<int:time_entry_pk>/edit/', views.UpdateTaskTimeEntryView.as_view(), name='time_entry_update'),
    path('<int:pk>/time-entries/<int:time_entry_pk>/delete/', views.DeleteTaskTimeEntryView.as_view(), name='time_entry_delete'),
    
    # Task Sharing
    path('<int:pk>/share/', views.ShareTaskView.as_view(), name='share_task'),
    path('<int:pk>/unshare/<int:sharing_id>/', views.UnshareTaskView.as_view(), name='unshare_task'),
    
    # Subtasks
    path('<int:pk>/subtasks/create/', views.CreateSubtaskView.as_view(), name='create_subtask'),
    
    # Task Activities
    path('<int:pk>/activities/', views.TaskActivitiesView.as_view(), name='activities'),
    
    # Bulk Operations
    path('bulk-update/', views.BulkUpdateTasksView.as_view(), name='bulk_update'),
    path('bulk-delete/', views.BulkDeleteTasksView.as_view(), name='bulk_delete'),
    path('bulk-assign/', views.BulkAssignTasksView.as_view(), name='bulk_assign'),
    
    # API endpoint for dynamic choices
    path('api/dynamic-choices/<str:model_name>/', views.get_task_dynamic_choices, name='dynamic_choices'),
]