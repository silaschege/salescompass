from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('dashboard/', views.ProjectDashboardView.as_view(), name='dashboard'),
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('<int:pk>/gantt/', views.ProjectGanttView.as_view(), name='project_gantt'),
    path('<int:pk>/gantt/data/', views.ProjectGanttDataView.as_view(), name='project_gantt_data'),
    
    # Timesheets
    path('timesheets/', views.TimesheetListView.as_view(), name='timesheet_list'),
    path('timesheets/<int:pk>/', views.TimesheetDetailView.as_view(), name='timesheet_detail'),
    path('timesheets/<int:pk>/submit/', views.TimesheetSubmitView.as_view(), name='timesheet_submit'),
    
    # Approvals
    path('approvals/', views.TimesheetApprovalListView.as_view(), name='timesheet_approval_list'),
    path('approvals/<int:pk>/', views.TimesheetApproveRejectView.as_view(), name='timesheet_approve_reject'),

    # Reports
    path('reports/profitability/', views.ProjectProfitabilityView.as_view(), name='profitability_report'),
    path('reports/capacity/', views.ResourceCapacityView.as_view(), name='resource_capacity'),
    path('reports/revenue-recognition/', views.RevenueRecognitionView.as_view(), name='revenue_recognition'),
]
