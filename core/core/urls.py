from django.urls import path
from . import views

from django.views.generic import TemplateView

from accounts.views import CustomLoginView

from django.contrib.auth.views import LogoutView

app_name = 'core'

urlpatterns = [
    # Landing Page
    path('', views.home, name='home'),

    # Public Pages
    path('products/', TemplateView.as_view(template_name='public/products.html'), name='product'),
    path('solutions/', TemplateView.as_view(template_name='public/solutions.html'), name='solutions'),
    path('pricing/', TemplateView.as_view(template_name='public/pricing.html'), name='pricing'),
    path('customers/', TemplateView.as_view(template_name='public/customer.html'), name='customers'),
    path('company/', TemplateView.as_view(template_name='public/company.html'), name='company'),
    path('support/', TemplateView.as_view(template_name='public/support.html'), name='support'),
    path('try/', TemplateView.as_view(template_name='public/try.html'), name='try_free'),
    path('integrations/', TemplateView.as_view(template_name='public/integrations.html'), name='integrations'),
    path('api-docs/', TemplateView.as_view(template_name='public/api.html'), name='api_docs'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('apps/', views.AppSelectionView.as_view(), name='app_selection'),
    path('apps/settings/', views.AppSettingsView.as_view(), name='app_settings'),

    # CLV Dashboard
    path('clv-dashboard/', views.clv_dashboard, name='clv_dashboard'),
    
    # Add other existing URLs for core
    # (Note: The actual existing URLs would need to be added based on the original file)

    # Module Label URLs
    path('labels/', views.ModuleLabelListView.as_view(), name='module_label_list'),
    path('labels/create/', views.ModuleLabelCreateView.as_view(), name='module_label_create'),
    path('labels/<int:pk>/edit/', views.ModuleLabelUpdateView.as_view(), name='module_label_edit'),
    path('labels/<int:pk>/delete/', views.ModuleLabelDeleteView.as_view(), name='module_label_delete'),

    # Module Choice URLs
    path('module-choices/', views.ModuleChoiceListView.as_view(), name='module_choice_list'),
    path('module-choices/create/', views.ModuleChoiceCreateView.as_view(), name='module_choice_create'),
    path('module-choices/<int:pk>/edit/', views.ModuleChoiceUpdateView.as_view(), name='module_choice_edit'),
    path('module-choices/<int:pk>/delete/', views.ModuleChoiceDeleteView.as_view(), name='module_choice_delete'),

    # Model Choice URLs
    path('model-choices/', views.ModelChoiceListView.as_view(), name='model_choice_list'),
    path('model-choices/create/', views.ModelChoiceCreateView.as_view(), name='model_choice_create'),
    path('model-choices/<int:pk>/edit/', views.ModelChoiceUpdateView.as_view(), name='model_choice_edit'),
    path('model-choices/<int:pk>/delete/', views.ModelChoiceDeleteView.as_view(), name='model_choice_delete'),

    # Field Type URLs
    path('field-types/', views.FieldTypeListView.as_view(), name='field_type_list'),
    path('field-types/create/', views.FieldTypeCreateView.as_view(), name='field_type_create'),
    path('field-types/<int:pk>/edit/', views.FieldTypeUpdateView.as_view(), name='field_type_edit'),
    path('field-types/<int:pk>/delete/', views.FieldTypeDeleteView.as_view(), name='field_type_delete'),

    # Assignment Rule Type URLs
    path('assignment-rule-types/', views.AssignmentRuleTypeListView.as_view(), name='assignment_rule_type_list'),
    path('assignment-rule-types/create/', views.AssignmentRuleTypeCreateView.as_view(), name='assignment_rule_type_create'),
    path('assignment-rule-types/<int:pk>/edit/', views.AssignmentRuleTypeUpdateView.as_view(), name='assignment_rule_type_edit'),
    path('assignment-rule-types/<int:pk>/delete/', views.AssignmentRuleTypeDeleteView.as_view(), name='assignment_rule_type_delete'),
]

