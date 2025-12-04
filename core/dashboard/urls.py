from django.urls import path
from . import views
from . import wizard_views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard views
    path('', views.CockpitView.as_view(), name='cockpit'),
    path('render/<int:pk>/', views.DashboardRenderView.as_view(), name='render'),
    
    # Wizard (replaces builder)
    path('builder/', wizard_views.DashboardWizardStep1View.as_view(), name='builder'),
    path('wizard/step1/', wizard_views.DashboardWizardStep1View.as_view(), name='wizard_step1'),
    path('wizard/step2/', wizard_views.DashboardWizardStep2View.as_view(), name='wizard_step2'),
    path('wizard/step3/', wizard_views.DashboardWizardStep3View.as_view(), name='wizard_step3'),
    path('wizard/save/', wizard_views.DashboardWizardSaveView.as_view(), name='wizard_save'),
    path('wizard/api/model-fields/', wizard_views.ModelFieldsAPIView.as_view(), name='wizard_model_fields_api'),
    
    # Dashboard management
    path('save/', views.SaveDashboardView.as_view(), name='save_dashboard'),
    
    # Role-based dashboards
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('manager/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('support/', views.SupportDashboardView.as_view(), name='support_dashboard'),
]
