from django.contrib import admin
from .models import WazoCallLog, WazoSMSLog, WazoExtension


@admin.register(WazoCallLog)
class WazoCallLogAdmin(admin.ModelAdmin):
    list_display = ['call_id', 'direction', 'from_number', 'to_number', 'status', 'duration', 'started_at', 'user']
    list_filter = ['direction', 'status', 'started_at']
    search_fields = ['call_id', 'from_number', 'to_number']
    readonly_fields = ['call_id', 'wazo_data']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Call Info', {
            'fields': ('call_id', 'direction', 'from_number', 'to_number', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'duration')
        }),
        ('CRM Links', {
            'fields': ('user', 'contact', 'lead', 'opportunity', 'account')
        }),
        ('Recording', {
            'fields': ('recording_url', 'notes')
        }),
        ('Raw Data', {
            'fields': ('wazo_data',),
            'classes': ('collapse',)
        }),
    )


@admin.register(WazoSMSLog)
class WazoSMSLogAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'direction', 'from_number', 'to_number', 'status', 'sent_at', 'user']
    list_filter = ['direction', 'status', 'sent_at']
    search_fields = ['message_id', 'from_number', 'to_number', 'body']
    readonly_fields = ['message_id', 'wazo_data']
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Message Info', {
            'fields': ('message_id', 'direction', 'from_number', 'to_number', 'body', 'status')
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at')
        }),
        ('CRM Links', {
            'fields': ('user', 'contact', 'lead')
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('wazo_data',),
            'classes': ('collapse',)
        }),
    )


@admin.register(WazoExtension)
class WazoExtensionAdmin(admin.ModelAdmin):
    list_display = ['user', 'extension', 'caller_id', 'is_active']
    list_filter = ['is_active']
    search_fields = ['user__username', 'user__email', 'extension', 'caller_id']
    raw_id_fields = ['user']
