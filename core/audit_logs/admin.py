from django.contrib import admin
from .models import AuditReport, AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['audit_log_created_at', 'user', 'action', 'resource_type', 'tenant']
    list_filter = ['action', 'audit_log_created_at']
    search_fields = ['user__email', 'action', 'resource_type', 'resource_name', 'ip_address']
    readonly_fields = ['audit_log_created_at', 'old_values', 'new_values', 'metadata']
    date_hierarchy = 'audit_log_created_at'
    
    def has_add_permission(self, request):
        # Audit logs should only be created programmatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should never be deleted
        return False
