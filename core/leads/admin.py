from django.contrib import admin
from .models import LeadSource, LeadStatus

@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ['label', 'source_name', 'order', 'color', 'source_is_active', 'is_system']
    list_filter = ['source_is_active', 'is_system', 'tenant']
    search_fields = ['source_name', 'label']
    ordering = ['order', 'label']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ['source_name', 'is_system']
        return ['is_system']


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ['label', 'status_name', 'order', 'color', 'status_is_active', 'is_system']
    list_filter = ['status_is_active', 'is_system', 'tenant']
    search_fields = ['status_name', 'label']
    ordering = ['order', 'label']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ['status_name', 'is_system']
        return ['is_system']
