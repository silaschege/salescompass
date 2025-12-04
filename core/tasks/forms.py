from django import forms
from .models import Task, TaskComment, TaskAttachment, TaskTemplate, TaskPriority, TaskStatus
from accounts.models import Account
from opportunities.models import Opportunity
from leads.models import Lead
from cases.models import Case

class TaskForm(forms.ModelForm):
    """Form for creating and updating tasks."""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'account', 'opportunity',
            'related_lead', 'case', 'priority_ref', 'status_ref', 'task_type', 'due_date',
            'estimated_hours', 'tags', 'reminder_enabled', 'reminder_time',
            'is_recurring', 'recurrence_pattern', 'recurrence_end_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'opportunity': forms.Select(attrs={'class': 'form-select'}),
            'related_lead': forms.Select(attrs={'class': 'form-select'}),
            'case': forms.Select(attrs={'class': 'form-select'}),
            'priority_ref': forms.Select(attrs={'class': 'form-select'}),
            'status_ref': forms.Select(attrs={'class': 'form-select'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'reminder_time': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '1440'}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'priority_ref': 'Priority',
            'status_ref': 'Status',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            tenant_id = getattr(user, 'tenant_id', None)
            
            # Filter all related objects to user's tenant
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(
                tenant_id=tenant_id
            )
            self.fields['account'].queryset = Account.objects.filter(tenant_id=tenant_id)
            self.fields['opportunity'].queryset = Opportunity.objects.filter(tenant_id=tenant_id)
            self.fields['related_lead'].queryset = Lead.objects.filter(tenant_id=tenant_id)
            self.fields['case'].queryset = Case.objects.filter(tenant_id=tenant_id)
            
            # Filter dynamic configuration fields
            self.fields['priority_ref'].queryset = TaskPriority.objects.filter(
                tenant_id=tenant_id, is_active=True
            )
            self.fields['status_ref'].queryset = TaskStatus.objects.filter(
                tenant_id=tenant_id, is_active=True
            )
            
            # Set default assigned_to to current user
            self.fields['assigned_to'].initial = user
            
        # Set required fields
        self.fields['title'].required = True
        self.fields['due_date'].required = True
        self.fields['priority_ref'].required = True
        self.fields['status_ref'].required = True

    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure only one related object is selected
        related_objects = [
            cleaned_data.get('account'),
            cleaned_data.get('opportunity'), 
            cleaned_data.get('related_lead'),
            cleaned_data.get('case')
        ]
        related_count = sum(1 for obj in related_objects if obj is not None)
        
        if related_count > 1:
            raise forms.ValidationError("Please select only one related object (Account, Opportunity, Lead, or Case).")
        elif related_count == 0:
            raise forms.ValidationError("Please select a related object (Account, Opportunity, Lead, or Case).")
            
        return cleaned_data


class TaskCommentForm(forms.ModelForm):
    """Form for adding comments to tasks."""
    
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a comment...'})
        }


class TaskAttachmentForm(forms.ModelForm):
    """Form for uploading task attachments."""
    
    class Meta:
        model = TaskAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }


class TaskTemplateForm(forms.ModelForm):
    """Form for creating and updating task templates."""
    
    class Meta:
        model = TaskTemplate
        fields = ['name', 'description', 'task_type', 'priority', 'estimated_hours', 'default_due_offset', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'default_due_offset': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '365'}),
        }