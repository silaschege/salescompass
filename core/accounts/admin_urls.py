from django.urls import path
from . import admin_views

app_name = 'accounts'

urlpatterns = [
    # User Management
    path('admin/dashboard/', admin_views.UserManagementDashboardView.as_view(), name='admin_user_dashboard'),
    path('admin/users/', admin_views.UserListView.as_view(), name='admin_user_list'),
    path('admin/users/create/', admin_views.UserCreateView.as_view(), name='admin_user_create'),
    path('admin/users/<int:user_id>/edit/', admin_views.UserUpdateView.as_view(), name='admin_user_update'),
    path('admin/users/<int:user_id>/delete/', admin_views.UserDeleteView.as_view(), name='admin_user_delete'),
    path('admin/users/bulk/', admin_views.UserBulkOperationsView.as_view(), name='user_bulk_operations'),
    path('admin/users/activity/', admin_views.UserActivityView.as_view(), name='user_activity'),
    path('admin/users/roles/', admin_views.UserRoleManagementView.as_view(), name='user_role_management'),
    path('admin/users/access-review/', admin_views.UserAccessReviewView.as_view(), name='user_access_review'),
    path('admin/users/mfa/', admin_views.MFAManagementView.as_view(), name='mfa_management'),
    path('admin/users/certification/', admin_views.UserAccessCertificationView.as_view(), name='user_access_certification'),
]
