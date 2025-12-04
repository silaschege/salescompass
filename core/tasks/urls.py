from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Task CRUD
    path('', views.TaskListView.as_view(), name='list'),
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
]