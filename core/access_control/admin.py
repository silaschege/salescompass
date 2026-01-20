from django.contrib import admin
from .models import AccessControl, TenantAccessControl, RoleAccessControl, UserAccessControl

class TenantAccessControlInline(admin.TabularInline):
    model = TenantAccessControl
    extra = 0

@admin.register(AccessControl)
class AccessControlAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'access_type', 'default_enabled']
    list_filter = ['access_type', 'default_enabled']
    search_fields = ['name', 'key']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'key', 'description')
        }),
        ('Access Configuration', {
            'fields': ('access_type', 'default_enabled', 'config_schema')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [TenantAccessControlInline]

@admin.register(TenantAccessControl)
class TenantAccessControlAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'access_control', 'is_enabled']
    list_filter = ['is_enabled', 'tenant', 'access_control__access_type']
    search_fields = ['tenant__name', 'access_control__name', 'access_control__key']
    autocomplete_fields = ['tenant', 'access_control']

@admin.register(RoleAccessControl)
class RoleAccessControlAdmin(admin.ModelAdmin):
    list_display = ['role', 'access_control', 'is_enabled']
    list_filter = ['is_enabled', 'role__tenant', 'access_control__access_type']
    search_fields = ['role__name', 'access_control__name', 'access_control__key']
    autocomplete_fields = ['role', 'access_control']

@admin.register(UserAccessControl)
class UserAccessControlAdmin(admin.ModelAdmin):
    list_display = ['user', 'access_control', 'is_enabled']
    list_filter = ['is_enabled', 'access_control__access_type']
    search_fields = ['user__email', 'access_control__name', 'access_control__key']
    autocomplete_fields = ['user', 'access_control']
