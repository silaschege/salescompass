from django import forms
from .models import Task, TaskPriority, TaskStatus, TaskType, RecurrencePattern,TaskDependency,TaskTimeEntry
from tenants.models import Tenant as TenantModel


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'task_description', 'assigned_to', 'created_by', 'account', 'opportunity', 
                  'lead', 'case', 'priority', 'priority_ref', 'status', 'status_ref', 
                  'task_type', 'task_type_ref', 'due_date', 'completed_at', 
                  'is_recurring', 'recurrence_pattern', 'recurrence_pattern_ref', 
                  'recurrence_end_date', 'parent_task', 'estimated_hours', 'actual_hours',
                  'content_type', 'object_id']
        
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title'
            }),
            'task_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter task description'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'created_by': forms.Select(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'opportunity': forms.Select(attrs={'class': 'form-control'}),
            'lead': forms.Select(attrs={'class': 'form-control'}),
            'case': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'priority_ref': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'status_ref': forms.Select(attrs={'class': 'form-control'}),
            'task_type': forms.Select(attrs={'class': 'form-control'}),
            'task_type_ref': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'completed_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'recurrence_pattern': forms.Select(attrs={'class': 'form-control'}),
            'recurrence_pattern_ref': forms.Select(attrs={'class': 'form-control'}),
            'recurrence_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'parent_task': forms.Select(attrs={'class': 'form-control'}),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'actual_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
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
        
        widgets = {
            'priority_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter priority name (e.g., low, medium, high)'
            }),
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter priority label (e.g., Low, Medium, High)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#6c757d'
            }),
            'priority_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = TaskStatus
        fields = ['status_name', 'label', 'order', 'color', 'status_is_active', 'is_system']
        
        widgets = {
            'status_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter status name (e.g., todo, in_progress, completed)'
            }),
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter status label (e.g., To Do, In Progress, Completed)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#6c757d'
            }),
            'status_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class TaskTypeForm(forms.ModelForm):
    class Meta:
        model = TaskType
        fields = ['type_name', 'label', 'order', 'type_is_active', 'is_system']
        
        widgets = {
            'type_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter type name (e.g., lead_review, custom)'
            }),
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter type label (e.g., Lead Review, Custom Task)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'type_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class RecurrencePatternForm(forms.ModelForm):
    class Meta:
        model = RecurrencePattern
        fields = ['pattern_name', 'label', 'order', 'pattern_is_active', 'is_system']
        
        widgets = {
            'pattern_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter pattern name (e.g., daily, weekly)'
            }),
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter pattern label (e.g., Daily, Weekly)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'pattern_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

# In forms.py
class TaskDependencyForm(forms.ModelForm):
    class Meta:
        model = TaskDependency
        fields = ['predecessor', 'successor', 'dependency_type', 'lag_time']
        
        widgets = {
            'predecessor': forms.Select(attrs={'class': 'form-control'}),
            'successor': forms.Select(attrs={'class': 'form-control'}),
            'dependency_type': forms.Select(attrs={'class': 'form-control'}),
            'lag_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'placeholder': 'HH:MM:SS'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            # Filter tasks to same tenant
            self.fields['predecessor'].queryset = Task.objects.filter(tenant_id=self.tenant.id)
            self.fields['successor'].queryset = Task.objects.filter(tenant_id=self.tenant.id)
        
# In forms.py
class TaskTimeEntryForm(forms.ModelForm):
    class Meta:
        model = TaskTimeEntry
        fields = ['task', 'date_logged', 'hours_spent', 'description', 'is_billable']
        
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
            'date_logged': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'hours_spent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '24'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the work done'
            }),
            'is_billable': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.fields['task'].queryset = Task.objects.filter(tenant_id=self.tenant.id)