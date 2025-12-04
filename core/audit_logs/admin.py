from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user_email', 'action_type', 'resource_type', 'severity', 'tenant_id']
    list_filter = ['severity', 'action_type', 'timestamp']
    search_fields = ['user_email', 'action_type', 'resource_type', 'description', 'ip_address']
    readonly_fields = ['timestamp', 'state_before', 'state_after', 'metadata']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Audit logs should only be created programmatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should never be deleted
        return False
