from django.contrib import admin
from .models import TaskPriority, TaskStatus

@admin.register(TaskPriority)
class TaskPriorityAdmin(admin.ModelAdmin):
    list_display = ['label', 'name', 'order', 'color', 'is_active', 'is_system']
    list_filter = ['is_active', 'is_system', 'tenant_id']
    search_fields = ['name', 'label']
    ordering = ['order', 'label']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ['name', 'is_system']
        return ['is_system']


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ['label', 'name', 'order', 'color', 'is_active', 'is_system']
    list_filter = ['is_active', 'is_system', 'tenant_id']
    search_fields = ['name', 'label']
    ordering = ['order', 'label']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ['name', 'is_system']
        return ['is_system']
