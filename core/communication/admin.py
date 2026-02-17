from django.contrib import admin
from .models import (
    NotificationTemplate, EmailSMSServiceConfiguration, CommunicationHistory,
    Email, SMS, CallLog, ChatMessage, EmailSignature
)
from .whatsapp_models import WhatsAppConfiguration, WhatsAppMessage, WhatsAppTemplate

@admin.register(WhatsAppConfiguration)
class WhatsAppConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'tenant', 'is_active', 'is_primary')
    list_filter = ('tenant', 'is_active', 'is_primary')
    search_fields = ('name', 'phone_number')

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'direction', 'from_number', 'to_number', 'status', 'created_at')
    list_filter = ('direction', 'status', 'tenant')
    search_fields = ('from_number', 'to_number', 'body', 'message_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_name', 'language', 'category', 'status', 'tenant')
    list_filter = ('status', 'category', 'tenant')
    search_fields = ('template_name', 'body_text')

admin.site.register(NotificationTemplate)
admin.site.register(EmailSMSServiceConfiguration)
admin.site.register(CommunicationHistory)
admin.site.register(Email)
admin.site.register(SMS)
admin.site.register(CallLog)
admin.site.register(ChatMessage)
admin.site.register(EmailSignature)
