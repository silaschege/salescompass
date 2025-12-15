from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    # CRUD
    path('accounts/', views.AccountListView.as_view(), name='accounts_list'),
    path('create/', views.AccountCreateView.as_view(), name='accounts_create'),
    path('<int:pk>/', views.AccountDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AccountUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.AccountDeleteView.as_view(), name='delete'),

    
    # Bulk Import
    path('import/upload/', views.BulkImportUploadView.as_view(), name='bulk_import_upload'),
    path('import/map/', views.BulkImportMapView.as_view(), name='bulk_import_map'),
    path('import/preview/', views.BulkImportPreviewView.as_view(), name='bulk_import_preview'),
    
    # Kanban
    path('', views.AccountKanbanView.as_view(), name='accounts_kanban'),
    path('api/update-status/', views.update_account_status, name='update_status'),

    # Contact URLs
    path('contacts/', views.ContactListView.as_view(), name='contact_list'),
    path('contacts/create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_update'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),
    
    # Account-specific contact URLs
    path('accounts/<int:account_pk>/contacts/', views.AccountContactListView.as_view(), name='account_contact_list'),
    
    # Team Members
    path('members/', views.OrganizationMemberListView.as_view(), name='member_list'),
    path('members/create/', views.OrganizationMemberCreateView.as_view(), name='member_create'),
    path('members/<int:pk>/', views.OrganizationMemberDetailView.as_view(), name='member_detail'),
    path('members/<int:pk>/edit/', views.OrganizationMemberUpdateView.as_view(), name='member_update'),
    path('members/<int:pk>/delete/', views.OrganizationMemberDeleteView.as_view(), name='member_delete'),

    # Team Roles
    path('roles/', views.TeamRoleListView.as_view(), name='role_list'),
    path('roles/create/', views.TeamRoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', views.TeamRoleUpdateView.as_view(), name='role_update'),
    path('roles/<int:pk>/delete/', views.TeamRoleDeleteView.as_view(), name='role_delete'),

    # Territories
    path('territories/', views.TerritoryListView.as_view(), name='territory_list'),
    path('territories/create/', views.TerritoryCreateView.as_view(), name='territory_create'),
    path('territories/<int:pk>/edit/', views.TerritoryUpdateView.as_view(), name='territory_update'),
    path('territories/<int:pk>/delete/', views.TerritoryDeleteView.as_view(), name='territory_delete'),

    # Admin URLs
    path('admin/', include('accounts.admin_urls')),
]
