from django.urls import path
from . import views
 
app_name = 'reports'


urlpatterns = [
    # Report CRUD
    path('', views.ReportListView.as_view(), name='report_list'),
    path('create/', views.ReportBuilderView.as_view(), name='create'),
    path('builder/', views.ReportBuilderView.as_view(), name='builder'),
    path('public/<uuid:token>/', views.PublicReportView.as_view(), name='public_view'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('<int:pk>/delete/', views.ReportDeleteView.as_view(), name='report_delete'),
    path('report_list/', views.ReportListView.as_view(), name='report_list'),  # Additional name for navigation
    
    # Sales Analytics
    path('sales-analytics/', views.SalesAnalyticsDashboardView.as_view(), name='sales_analytics'),

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
    
    # Snapshots and Subscriptions
    path('<int:report_id>/snapshots/', views.ReportSnapshotListView.as_view(), name='snapshot_list'),
    path('<int:report_id>/snapshots/create/', views.ReportSnapshotCreateView.as_view(), name='snapshot_create'),
    path('<int:report_id>/subscribe/', views.SubscriptionToggleView.as_view(), name='subscribe_toggle'),
    
    # Generation (AJAX)
    path('generate/', views.GenerateReportView.as_view(), name='generate'),
    
    # Business Metrihttp://127.0.0.1:8000/reports/schedules/cs Exports
    path('export/clv-metrics/', views.export_clv_metrics, name='export_clv_metrics'),
    path('export/cac-metrics/', views.export_cac_metrics, name='export_cac_metrics'),
    path('export/sales-velocity-metrics/', views.export_sales_velocity_metrics, name='export_sales_velocity_metrics'),
    path('export/roi-metrics/', views.export_roi_metrics, name='export_roi_metrics'),
    path('export/conversion-funnel-metrics/', views.export_conversion_funnel_metrics, name='export_conversion_funnel_metrics'),
    path('export/all-metrics/', views.export_all_metrics, name='export_all_metrics'),
]