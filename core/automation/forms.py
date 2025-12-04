from django import forms
from .models import Automation, AutomationCondition, AutomationAction

class AutomationForm(forms.ModelForm):
    """
    Form for creating and updating automation rules.
    """
    class Meta:
        model = Automation
        fields = [
            'name', 
            'trigger_type', 
            'is_active', 
            'is_system', 
            'priority'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Account Onboarding Automation'
            }),
            'trigger_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_system': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'disabled': True  # System automations can only be created programmatically
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': 'Lower numbers = higher priority'
            })
        }
        help_texts = {
            'name': 'Descriptive name for this automation rule',
            'trigger_type': 'The event that will trigger this automation',
            'is_active': 'Inactive automations will not execute',
            'is_system': 'System automations cannot be deleted and are managed by the system',
            'priority': 'Determines execution order when multiple automations match the same trigger'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable the is_system field for editing
        if self.instance.pk:
            self.fields['is_system'].widget.attrs['disabled'] = True
            # If it's a system automation, disable name and trigger_type as well
            if self.instance.is_system:
                self.fields['name'].widget.attrs['readonly'] = True
                self.fields['trigger_type'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        is_system = cleaned_data.get('is_system', False)
        
        # System automations should have is_active=True by default
        if is_system and 'is_active' in cleaned_data and not cleaned_data['is_active']:
            raise forms.ValidationError("System automations must be active.")
        
        return cleaned_data


class AutomationConditionForm(forms.ModelForm):
    """
    Form for creating and updating automation conditions.
    """
    class Meta:
        model = AutomationCondition
        fields = [
            'field_path', 
            'operator', 
            'value'
        ]
        widgets = {
            'field_path': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., account.industry, opportunity.amount'
            }),
            'operator': forms.Select(attrs={
                'class': 'form-select'
            }),
            'value': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter value or JSON for complex conditions'
            })
        }
        help_texts = {
            'field_path': 'Dot notation path to the field (e.g., "account.industry", "opportunity.amount")',
            'operator': 'Comparison operator for the condition',
            'value': 'The value to compare against (can be JSON for complex values)'
        }

    def __init__(self, *args, **kwargs):
        automation = kwargs.pop('automation', None)
        super().__init__(*args, **kwargs)
        self.automation = automation
        
        if automation:
            # Add dynamic help text based on trigger type
            trigger_type = automation.trigger_type
            if trigger_type == 'account.created':
                self.fields['field_path'].help_text = 'Available fields: account.name, account.industry, account.tier, account.health_score'
            elif trigger_type == 'opportunity.created':
                self.fields['field_path'].help_text = 'Available fields: opportunity.name, opportunity.amount, opportunity.stage'

    def clean_value(self):
        value = self.cleaned_data['value']
        try:
            # Try to parse as JSON for complex values
            import json
            parsed_value = json.loads(value)
            return parsed_value
        except (ValueError, TypeError):
            # If it's not valid JSON, return as string
            return value

    def clean(self):
        cleaned_data = super().clean()
        field_path = cleaned_data.get('field_path')
        operator = cleaned_data.get('operator')
        value = cleaned_data.get('value')
        
        if not field_path:
            raise forms.ValidationError("Field path is required.")
        
        if not operator:
            raise forms.ValidationError("Operator is required.")
        
        # Validate value based on operator
        if operator in ['eq', 'ne'] and value is None:
            raise forms.ValidationError("Value is required for this operator.")
        
        return cleaned_data


class AutomationActionForm(forms.ModelForm):
    """
    Form for creating and updating automation actions.
    """
    class Meta:
        model = AutomationAction
        fields = [
            'action_type', 
            'config', 
            'order'
        ]
        widgets = {
            'action_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'config': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter action configuration as JSON'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Execution order (0 = first)'
            })
        }
        help_texts = {
            'action_type': 'The type of action to execute',
            'config': 'JSON configuration for the action (see examples below)',
            'order': 'Determines the execution order of actions within this automation'
        }

    def __init__(self, *args, **kwargs):
        automation = kwargs.pop('automation', None)
        super().__init__(*args, **kwargs)
        self.automation = automation
        
        if automation:
            # Add dynamic help text based on action type
            self.fields['config'].help_text = self.get_config_help_text()

    def get_config_help_text(self):
        """Return help text with examples based on action types."""
        examples = {
            'send_email': '''
                {
                    "subject": "Welcome to SalesCompass!",
                    "template": "welcome_email",
                    "to": "{{ account.primary_contact.email }}",
                    "from_email": "noreply@salescompass.com"
                }
            ''',
            'create_task': '''
                {
                    "title": "Follow up with {{ account.name }}",
                    "description": "Check in after account creation",
                    "assigned_to": "{{ account.owner.id }}",
                    "due_date": "7 days"
                }
            ''',
            'update_field': '''
                {
                    "model": "accounts.Account",
                    "instance_id": "{{ account.id }}",
                    "field_name": "health_score",
                    "new_value": 85
                }
            ''',
            'run_function': '''
                {
                    "function": "accounts.utils.send_welcome_email",
                    "args": {
                        "account_id": "{{ account.id }}"
                    }
                }
            ''',
            'create_case': '''
                {
                    "subject": "Welcome Case for {{ account.name }}",
                    "description": "Initial setup and onboarding",
                    "account_id": "{{ account.id }}",
                    "priority": "medium"
                }
            ''',
            'assign_owner': '''
                {
                    "model": "accounts.Account",
                    "instance_id": "{{ account.id }}",
                    "owner_id": "{{ user.id }}"
                }
            ''',
            'send_slack_message': '''
                {
                    "webhook_url": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
                    "message": "New account created: {{ account.name }}"
                }
            ''',
            'webhook': '''
                {
                    "url": "https://api.yourservice.com/webhook",
                    "headers": {
                        "Authorization": "Bearer your-token"
                    }
                }
            '''
        }
        
        help_text = "JSON configuration for the action. Available action types:<br>"
        for action_type, example in examples.items():
            help_text += f"<br><strong>{action_type}:</strong><br><pre>{example}</pre>"
        
        return help_text

    def clean_config(self):
        config = self.cleaned_data['config']
        try:
            # Validate that config is valid JSON
            import json
            parsed_config = json.loads(config)
            
            # Validate required fields based on action type
            action_type = self.cleaned_data.get('action_type')
            if action_type == 'send_email':
                required_fields = ['subject', 'to']
            elif action_type == 'create_task':
                required_fields = ['title', 'assigned_to']
            elif action_type == 'update_field':
                required_fields = ['model', 'instance_id', 'field_name', 'new_value']
            elif action_type == 'run_function':
                required_fields = ['function']
            elif action_type == 'create_case':
                required_fields = ['subject', 'account_id']
            elif action_type == 'assign_owner':
                required_fields = ['model', 'instance_id', 'owner_id']
            elif action_type == 'send_slack_message':
                required_fields = ['webhook_url', 'message']
            elif action_type == 'webhook':
                required_fields = ['url']
            else:
                required_fields = []
            
            for field in required_fields:
                if field not in parsed_config:
                    raise forms.ValidationError(f"Required field '{field}' missing for {action_type} action.")
            
            return parsed_config
            
        except ValueError as e:
            raise forms.ValidationError(f"Invalid JSON format: {str(e)}")

    def clean(self):
        cleaned_data = super().clean()
        action_type = cleaned_data.get('action_type')
        config = cleaned_data.get('config')
        
        if not action_type:
            raise forms.ValidationError("Action type is required.")
        
        if not config:
            raise forms.ValidationError("Configuration is required.")
        
        return cleaned_data