from django.contrib import admin
from .models import TaskPriority, TaskStatus

@admin.register(TaskPriority)
class TaskPriorityAdmin(admin.ModelAdmin):
    list_display = ['label', 'priority_name', 'order', 'color', 'priority_is_active', 'is_system']
    list_filter = ['priority_is_active', 'is_system', 'tenant']
    search_fields = ['priority_name', 'label']
    ordering = ['order', 'label']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ['priority_name', 'is_system']
        return ['is_system']


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ['label', 'status_name', 'order', 'color', 'status_is_active', 'is_system']
    list_filter = ['status_is_active', 'is_system', 'tenant']
    search_fields = ['status_name', 'label']
    ordering = ['order', 'label']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ['status_name', 'is_system']
        return ['is_system']
