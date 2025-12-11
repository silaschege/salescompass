from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SystemConfigType, SystemConfigCategory, SystemEventType, SystemEventSeverity, HealthCheckType, HealthCheckStatus, MaintenanceStatus, MaintenanceType, PerformanceMetricType, PerformanceEnvironment, NotificationType, NotificationPriority


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Permissions', {'fields': ('role', 'phone', 'mfa_enabled')}),
        ('Customer Value Metrics', {
            'fields': ('customer_lifetime_value', 'acquisition_cost', 'retention_rate', 'avg_order_value', 'purchase_frequency', 'customer_since'),
            'classes': ('collapse',)
        }),
    )
    list_display = ['email', 'username', 'role', 'customer_lifetime_value', 'is_staff', 'is_superuser']
    list_filter = ['role', 'is_staff', 'is_superuser', 'customer_since']
    search_fields = ['email', 'username']
    ordering = ['email']


@admin.register(SystemConfigType)
class SystemConfigTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemConfigCategory)
class SystemConfigCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemEventType)
class SystemEventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SystemEventSeverity)
class SystemEventSeverityAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'color', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HealthCheckType)
class HealthCheckTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HealthCheckStatus)
class HealthCheckStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'color', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MaintenanceStatus)
class MaintenanceStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'color', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PerformanceMetricType)
class PerformanceMetricTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PerformanceEnvironment)
class PerformanceEnvironmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationPriority)
class NotificationPriorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'color', 'description', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
