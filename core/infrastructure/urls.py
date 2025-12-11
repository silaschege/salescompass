from django.urls import path
from . import views

app_name = 'infrastructure'

urlpatterns = [
    # Application Module Management
    path('admin/modules/', views.AppModuleListView.as_view(), name='app_module_list'),
    path('admin/modules/create/', views.AppModuleCreateView.as_view(), name='app_module_create'),
    path('admin/modules/<int:module_id>/update/', views.AppModuleUpdateView.as_view(), name='app_module_update'),
    path('admin/modules/<int:module_id>/delete/', views.AppModuleDeleteView.as_view(), name='app_module_delete'),
    path('admin/modules/dashboard/', views.AppModuleManagementView.as_view(), name='app_module_dashboard'),
    
    # Tenant Module Provisioning
    path('admin/tenant-modules/', views.TenantModuleProvisionListView.as_view(), name='tenant_module_provision_list'),
    path('admin/tenant-modules/create/', views.TenantModuleProvisionCreateView.as_view(), name='tenant_module_provision_create'),
    path('admin/tenant-modules/<int:provision_id>/update/', views.TenantModuleProvisionUpdateView.as_view(), name='tenant_module_provision_update'),
    
    # Module Provision Workflows
    path('admin/workflows/', views.ModuleProvisionWorkflowListView.as_view(), name='module_provision_workflow_list'),
    
    # Module Dependencies
    path('admin/dependencies/', views.ModuleDependencyListView.as_view(), name='module_dependency_list'),
    path('admin/dependencies/create/', views.ModuleDependencyCreateView.as_view(), name='module_dependency_create'),
    path('admin/dependencies/<int:dependency_id>/update/', views.ModuleDependencyUpdateView.as_view(), name='module_dependency_update'),
    
    # Module Provision Dashboard
    path('admin/provision-dashboard/', views.ModuleProvisionDashboardView.as_view(), name='module_provision_dashboard'),
    
    # Module Health Check
    path('admin/health-check/', views.ModuleHealthCheckView.as_view(), name='module_health_check'),
    
    # Module Configuration
    path('admin/module/<int:provision_id>/config/', views.ModuleConfigurationView.as_view(), name='module_configuration'),
]
