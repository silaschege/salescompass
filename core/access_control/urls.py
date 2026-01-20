
from django.urls import path
from . import views

app_name = 'access_control'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('manage/', views.ManageAccessView.as_view(), name='manage_access'),
    path('tenants/', views.TenantAccessListView.as_view(), name='tenant_list'),
    path('users/', views.UserAccessListView.as_view(), name='user_list'),
    path('manage/tenant/<str:tenant_id>/', views.TenantAccessDetailView.as_view(), name='tenant_access_detail'),
    path('manage/role/<int:role_id>/', views.RoleAccessDetailView.as_view(), name='role_access_detail'),
    path('manage/user/<int:user_id>/', views.UserAccessDetailView.as_view(), name='user_access_detail'),
    path('manage/assign/tenant/', views.AssignTenantAccessView.as_view(), name='assign_tenant_access'),
    path('manage/assign/tenant/delete/<int:pk>/', views.DeleteTenantAccessView.as_view(), name='delete_tenant_access'),
    path('manage/assign/tenant/bulk-delete/', views.BulkDeleteTenantAccessView.as_view(), name='bulk_delete_tenant_access'),
    path('create/', views.CreateAccessControlView.as_view(), name='create_access'),
    path('edit/<int:pk>/', views.EditAccessControlView.as_view(), name='edit_access'),
    path('delete/<int:pk>/', views.DeleteAccessControlView.as_view(), name='delete_access'),
    path('api/', views.AccessControlAPIView.as_view(), name='api'),
]