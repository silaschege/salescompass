from django.urls import path
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
    

]