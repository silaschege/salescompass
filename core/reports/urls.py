from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report CRUD
    path('', views.ReportListView.as_view(), name='list'),
    path('create/', views.ReportBuilderView.as_view(), name='create'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.ReportDeleteView.as_view(), name='delete'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('widget/create/', views.DashboardWidgetCreateView.as_view(), name='widget_create'),
    path('widget/<int:pk>/edit/', views.DashboardWidgetUpdateView.as_view(), name='widget_edit'),
    path('widget/<int:pk>/delete/', views.DashboardWidgetDeleteView.as_view(), name='widget_delete'),
    
    # Scheduling
    path('schedule/create/', views.ReportScheduleCreateView.as_view(), name='schedule_create'),
    path('schedule/<int:pk>/edit/', views.ReportScheduleUpdateView.as_view(), name='schedule_update'),
    path('schedule/<int:pk>/delete/', views.ReportScheduleDeleteView.as_view(), name='schedule_delete'),
    path('schedules/', views.ScheduledReportsView.as_view(), name='schedule_list'),
    
    # Exports
    path('export/<int:report_id>/', views.export_report, name='export_report'),
    path('exports/', views.ReportExportListView.as_view(), name='export_list'),
    
    # Generation (AJAX)
    path('generate/', views.GenerateReportView.as_view(), name='generate'),
]