from django.urls import path, include
from . import views
 
app_name = 'accounts'
urlpatterns = [
    # CRUD
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/export/', views.export_accounts_csv, name='account_export'),
    path('create/', views.AccountCreateView.as_view(), name='account_create'),
    path('<int:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account_update'),
    path('<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),

    
    # Bulk Import
    path('import/upload/', views.BulkImportUploadView.as_view(), name='bulk_import_upload'),
    path('import/map/', views.BulkImportMapView.as_view(), name='bulk_import_map'),
    path('import/preview/', views.BulkImportPreviewView.as_view(), name='bulk_import_preview'),
    
    # Kanban
    path('', views.AccountKanbanView.as_view(), name='account_kanban'),
    path('api/update-status/', views.update_account_status, name='update_status'),

    # Contact URLs
    path('contacts/', views.ContactListView.as_view(), name='contact_list'),
    path('contacts/create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_update'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),
    
    # Account-specific contact URLs
    path('accounts/<int:account_pk>/contacts/', views.AccountContactListView.as_view(), name='account_contact_list'),
    

    # Admin URLs
    path('admin/', include('accounts.admin_urls')),


    # Analytics URLs
    path('analytics/<int:account_pk>/', views.AccountAnalyticsView.as_view(), name='account_analytics'),
    path('dashboard/', views.AccountsDashboardView.as_view(), name='accounts_dashboard'),
    
    # API endpoints
    path('api/account-health/<int:account_id>/', views.check_account_health, name='check_account_health'),
    path('api/update-account-health/', views.trigger_account_health_update, name='trigger_account_health_update'),
    
    # New API endpoints for real-time updates
    path('api/engagement-trend/<int:account_id>/', views.get_engagement_trend, name='get_engagement_trend'),
    path('api/revenue-analysis/<int:account_id>/', views.get_revenue_analysis, name='get_revenue_analysis'),
    path('api/health-history/<int:account_id>/', views.get_health_history, name='get_health_history'),
]
