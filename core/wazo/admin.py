from django.contrib import admin
from .models import WazoCallLog, WazoSMSLog, WazoExtension, VoicemailTemplate


@admin.register(WazoCallLog)
class WazoCallLogAdmin(admin.ModelAdmin):
    list_display = ['call_id', 'direction', 'from_number', 'to_number', 'status', 'duration', 'started_at', 'user', 'tenant']
    list_filter = ['direction', 'status', 'started_at', 'tenant']
    search_fields = ['call_id', 'from_number', 'to_number']
    readonly_fields = ['call_id', 'wazo_data']
    date_hierarchy = 'started_at'
    raw_id_fields = ['user', 'contact', 'lead', 'opportunity', 'account']
    
    fieldsets = (
        ('Call Info', {
            'fields': ('call_id', 'direction', 'from_number', 'to_number', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'ended_at', 'duration')
        }),
        ('CRM Links', {
            'fields': ('tenant', 'user', 'contact', 'lead', 'opportunity', 'account')
        }),
        ('Recording', {
            'fields': ('recording_url', 'notes')
        }),
        ('Raw Data', {
            'fields': ('wazo_data',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'tenant')


@admin.register(WazoSMSLog)
class WazoSMSLogAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'direction', 'from_number', 'to_number', 'status', 'sent_at', 'user', 'tenant']
    list_filter = ['direction', 'status', 'sent_at', 'tenant']
    search_fields = ['message_id', 'from_number', 'to_number', 'body']
    readonly_fields = ['message_id', 'wazo_data']
    date_hierarchy = 'sent_at'
    raw_id_fields = ['user', 'contact', 'lead']
    
    fieldsets = (
        ('Message Info', {
            'fields': ('message_id', 'direction', 'from_number', 'to_number', 'body', 'status')
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at')
        }),
        ('CRM Links', {
            'fields': ('tenant', 'user', 'contact', 'lead')
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
    list_display = ['user', 'extension', 'caller_id', 'is_active', 'tenant']
    list_filter = ['is_active', 'tenant']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'extension', 'caller_id']
    raw_id_fields = ['user']
    list_editable = ['is_active']
    
    fieldsets = (
        (None, {
            'fields': ('tenant', 'user', 'is_active')
        }),
        ('Extension Details', {
            'fields': ('extension', 'caller_id', 'wazo_user_uuid')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'tenant')


@admin.register(VoicemailTemplate)
class VoicemailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration', 'is_active', 'tenant']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        (None, {
            'fields': ('tenant', 'name', 'description', 'is_active')
        }),
        ('Audio', {
            'fields': ('audio_file', 'audio_url', 'duration'),
            'description': 'Upload an audio file OR provide an external URL'
        }),
    )
