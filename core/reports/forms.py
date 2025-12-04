from django import forms
from .models import Report, ReportSchedule, DashboardWidget

class ReportForm(forms.ModelForm):
    """
    Form for creating and updating reports.
    """
    class Meta:
        model = Report
        fields = ['name', 'description', 'report_type', 'config', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for config field
        self.fields['config'].help_text = """
        JSON configuration for the report. Example:
        {
            "entities": ["account", "opportunity"],
            "fields": ["name", "amount", "esg_score"],
            "filters": {"industry": "manufacturing"},
            "group_by": "owner",
            "sort_by": "amount"
        }
        """


class ReportScheduleForm(forms.ModelForm):
    """
    Form for creating and updating report schedules.
    """
    recipients = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'email1@example.com,email2@example.com'}),
        help_text="Comma-separated email addresses"
    )

    class Meta:
        model = ReportSchedule
        fields = ['report', 'frequency', 'recipients', 'export_format', 'is_active']
        widgets = {
            'report': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'export_format': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter reports to user's tenant
            self.fields['report'].queryset = Report.objects.filter(
                tenant_id=user.tenant_id
            )
        
        # Format recipients as comma-separated
        if self.instance.pk and self.instance.recipients:
            self.fields['recipients'].initial = ','.join(self.instance.recipients)

    def clean_recipients(self):
        recipients = self.cleaned_data['recipients']
        if recipients:
            # Convert comma-separated string to list
            return [email.strip() for email in recipients.split(',') if email.strip()]
        return []


class DashboardWidgetForm(forms.ModelForm):
    """
    Form for creating and updating dashboard widgets.
    """
    class Meta:
        model = DashboardWidget
        fields = ['name', 'widget_type', 'report', 'position', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'widget_type': forms.Select(attrs={'class': 'form-control'}),
            'report': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['report'].queryset = Report.objects.filter(
                tenant_id=user.tenant_id,
                is_active=True
            )