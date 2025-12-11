from django import forms
from .models import Task, TaskPriority, TaskStatus, TaskType, RecurrencePattern
from tenants.models import Tenant as TenantModel


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'task_description', 'assigned_to', 'created_by', 'account', 'opportunity', 
                  'lead', 'case', 'priority', 'priority_ref', 'status', 'status_ref', 
                  'task_type', 'task_type_ref', 'due_date', 'completed_at', 
                  'is_recurring', 'recurrence_pattern', 'recurrence_pattern_ref', 
                  'recurrence_end_date', 'parent_task', 'estimated_hours', 'actual_hours']
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Load dynamic choices based on tenant
        if self.tenant:
            self.fields['priority_ref'].queryset = TaskPriority.objects.filter(tenant_id=self.tenant.id)
            self.fields['status_ref'].queryset = TaskStatus.objects.filter(tenant_id=self.tenant.id)
            self.fields['task_type_ref'].queryset = TaskType.objects.filter(tenant_id=self.tenant.id)
            self.fields['recurrence_pattern_ref'].queryset = RecurrencePattern.objects.filter(tenant_id=self.tenant.id)
        else:
            self.fields['priority_ref'].queryset = TaskPriority.objects.none()
            self.fields['status_ref'].queryset = TaskStatus.objects.none()
            self.fields['task_type_ref'].queryset = TaskType.objects.none()
            self.fields['recurrence_pattern_ref'].queryset = RecurrencePattern.objects.none()


class TaskPriorityForm(forms.ModelForm):
    class Meta:
        model = TaskPriority
        fields = ['priority_name', 'label', 'order', 'color', 'priority_is_active', 'is_system']


class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = TaskStatus
        fields = ['status_name', 'label', 'order', 'color', 'status_is_active', 'is_system']


class TaskTypeForm(forms.ModelForm):
    class Meta:
        model = TaskType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']


class RecurrencePatternForm(forms.ModelForm):
    class Meta:
        model = RecurrencePattern
        fields = ['pattern_name', 'label', 'order', 'pattern_is_active', 'is_system']
