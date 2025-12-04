from django.contrib import admin
from .models import TenantUsage, ResourceLimit


@admin.register(TenantUsage)
class TenantUsageAdmin(admin.ModelAdmin):
    list_display = ['tenant_id', 'api_calls_count', 'storage_used_gb', 'active_db_connections', 'measured_at']
    list_filter = ['measured_at']
    search_fields = ['tenant_id']
    readonly_fields = ['created_at', 'updated_at']
    

@admin.register(ResourceLimit)
class ResourceLimitAdmin(admin.ModelAdmin):
    list_display = ['tenant_id', 'is_throttled', 'custom_api_limit', 'custom_storage_limit_gb', 'created_by']
    list_filter = ['is_throttled']
    search_fields = ['tenant_id', 'throttle_reason']
    readonly_fields = ['created_at', 'updated_at']
