from django.urls import path
from django.views.generic import RedirectView
from . import views, wizard_views, bi_builder_views
from .bi_views import BIDashboardView, DataExplorerView, DrillDownView, MetricsAPIView, ActivityFeedAPIView, ChartDataAPIView, ComparativeAnalysisAPIView, StreamingDataAPIView

app_name = 'dashboard'
 
urlpatterns = [
    # Dashboard views
    path('', views.CockpitView.as_view(), name='cockpit'),
    path('render/<int:pk>/', views.DashboardRenderView.as_view(), name='render'),
    
    # API
    path('api/model-fields/', wizard_views.ModelFieldsAPIView.as_view(), name='model_fields_api'),
    path('api/preview/', bi_builder_views.DashboardPreviewAPIView.as_view(), name='dashboard_preview_api'),
    path('api/save/', bi_builder_views.DashboardSaveAPIView.as_view(), name='dashboard_save_api'),

    # BI Builder (New)
    path('builder/', bi_builder_views.BIDashboardBuilderView.as_view(), name='bi_builder'),
    
    # Wizard (Deprecated - keeping for fallback if needed)
    path('wizard/step1/', wizard_views.DashboardWizardStep1View.as_view(), name='wizard_step1'),
    path('wizard/step3/', wizard_views.DashboardWizardStep3View.as_view(), name='wizard_step3'),
    path('wizard/save/', wizard_views.DashboardWizardSaveView.as_view(), name='wizard_save'),
    path('wizard/api/model-fields/', wizard_views.ModelFieldsAPIView.as_view(), name='wizard_model_fields_api'),
    
    # Dashboard management
    path('save/', views.SaveDashboardView.as_view(), name='save_dashboard'),
    
    # Role-based dashboards
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('manager/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('support/', views.SupportDashboardView.as_view(), name='support_dashboard'),
    
    # Business Intelligence Dashboard

    # Redirect BI paths to main dashboard builder/viewer
    path('bi/', RedirectView.as_view(pattern_name='dashboard:cockpit', permanent=False), name='bi_dashboard'),
    path('bi/explorer/', DataExplorerView.as_view(), name='data_explorer'), # Keep Explorer for now as tool
    path('bi/drill-down/<str:metric>/', DrillDownView.as_view(), name='drill_down'), # Keep Drill Down for now
    path('bi/api/metrics/', MetricsAPIView.as_view(), name='bi_metrics_api'),
    path('bi/api/activity/', ActivityFeedAPIView.as_view(), name='activity_feed_api'),
    path('bi/api/chart/<str:chart_type>/', ChartDataAPIView.as_view(), name='chart_data_api'),
    path('bi/api/comparative/', ComparativeAnalysisAPIView.as_view(), name='comparative_analysis_api'),
    path('bi/api/streaming/', StreamingDataAPIView.as_view(), name='streaming_data_api'),
    
    # Widget Type CRUD URLs
    path('widget-types/', views.WidgetTypeListView.as_view(), name='widget_type_list'),
    path('widget-types/create/', views.WidgetTypeCreateView.as_view(), name='widget_type_create'),
    path('widget-types/<int:pk>/update/', views.WidgetTypeUpdateView.as_view(), name='widget_type_update'),
    path('widget-types/<int:pk>/delete/', views.WidgetTypeDeleteView.as_view(), name='widget_type_delete'),

    # Widget Category CRUD URLs
    path('widget-categories/', views.WidgetCategoryListView.as_view(), name='widget_category_list'),
    path('widget-categories/create/', views.WidgetCategoryCreateView.as_view(), name='widget_category_create'),
    path('widget-categories/<int:pk>/update/', views.WidgetCategoryUpdateView.as_view(), name='widget_category_update'),
    path('widget-categories/<int:pk>/delete/', views.WidgetCategoryDeleteView.as_view(), name='widget_category_delete'),

    # Dynamic choices dashboard
    path('dynamic-choices/', views.dynamic_choices_dashboard, name='dynamic_choices_dashboard'),
    path('api/dynamic-choices/<str:model_name>/', views.get_dynamic_choices_api, name='dynamic_choices_api'),
]