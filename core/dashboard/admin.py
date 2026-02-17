from django.contrib import admin
from .models import DashboardWidget, WidgetType, WidgetCategory


@admin.register(WidgetType)
class WidgetTypeAdmin(admin.ModelAdmin):
    list_display = ['widget_name', 'label', 'tenant', 'widget_type_is_active', 'is_system', 'order', 'widget_type_created_at']
    list_filter = ['widget_type_is_active', 'is_system', 'tenant', 'widget_type_created_at']
    search_fields = ['widget_name', 'label']
    ordering = ['tenant', 'order', 'widget_name']
    readonly_fields = ['widget_type_created_at', 'widget_type_updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'widget_name', 'label', 'order')
        }),
        ('Status', {
            'fields': ('is_active', 'is_system')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WidgetCategory)
class WidgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'label', 'tenant', 'widget_category_is_active', 'is_system', 'order', 'widget_category_created_at']
    list_filter = ['widget_category_is_active', 'is_system', 'tenant', 'widget_category_created_at']
    search_fields = ['category_name', 'label']
    ordering = ['tenant', 'order', 'category_name']
    readonly_fields = ['widget_category_created_at', 'widget_category_updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'category_name', 'label', 'order')
        }),
        ('Status', {
            'fields': ('is_active', 'is_system')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['widget_name', 'tenant', 'widget_is_active', 'widget_created_at', 'widget_updated_at']
    list_filter = ['widget_is_active', 'tenant', 'widget_created_at']
    search_fields = ['widget_name', 'description']
    ordering = ['tenant', 'widget_name']
    readonly_fields = ['widget_created_at', 'widget_updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'widget_name', 'description', 'template_path')
        }),
        ('Dynamic Choices (New)', {
            'fields': ('widget_type_ref', 'category_ref'),
            'classes': ('collapse',)
        }),
        ('Legacy Choices', {
            'fields': ('widget_type_old', 'category_old'),
        }),
        ('Status', {
            'fields': ('widget_is_active',)
        }),
        ('Timestamps', {
            'fields': ('widget_created_at', 'widget_updated_at'),
            'classes': ('collapse',)
        }),
    )

# Register your models here.
