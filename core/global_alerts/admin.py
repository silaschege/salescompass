from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'severity', 'start_time', 'end_time', 'is_active', 'is_global']
    list_filter = ['severity', 'alert_type', 'is_active', 'is_global']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Alert Details', {
            'fields': ('title', 'message', 'alert_type', 'severity')
        }),
        ('Scheduling', {
            'fields': ('start_time', 'end_time')
        }),
        ('Targeting', {
            'fields': ('is_global', 'target_tenant_ids')
        }),
        ('Display Options', {
            'fields': ('is_dismissible', 'show_on_all_pages', 'is_active')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
