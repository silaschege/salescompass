# apps/marketing/nps/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    NpsAbTest, NpsAbVariant, NpsSurvey, NpsConditionalFollowUp, 
    NpsEscalationRule, NpsEscalationRuleAction, NpsEscalationAction
)

# --- Survey & Conditional Follow-up ---

class NpsSurveyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['target_roles'].queryset = self.fields['target_roles'].queryset.filter(tenant_id=user.tenant_id)
            self.fields['target_territories'].queryset = self.fields['target_territories'].queryset.filter(tenant_id=user.tenant_id)

    class Meta:
        model = NpsSurvey
        fields = [
            'nps_survey_name', 'nps_survey_description', 'question_text', 
            'follow_up_question', 'delivery_method', 'trigger_event',
            'nps_survey_is_active', 'scheduled_start_date', 'scheduled_end_date',
            'enable_follow_up_logic', 'target_roles', 'target_territories'
        ]
        widgets = {
            'nps_survey_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nps_survey_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'follow_up_question': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_method': forms.Select(attrs={'class': 'form-select'}),
            'trigger_event': forms.Select(attrs={'class': 'form-select'}),
            'nps_survey_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scheduled_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'scheduled_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'enable_follow_up_logic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'target_roles': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'target_territories': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

NpsConditionalFollowUpFormSet = inlineformset_factory(
    NpsSurvey,
    NpsConditionalFollowUp,
    fields=['score_threshold', 'conditional_question_text'],
    extra=1,
    can_delete=True,
    widgets={
        'score_threshold': forms.Select(attrs={'class': 'form-select'}),
        'conditional_question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    }
)

# --- A/B Testing ---

class NpsAbTestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['survey'].queryset = NpsSurvey.objects.filter(tenant_id=user.tenant_id)

    class Meta:
        model = NpsAbTest
        fields = [
            'survey', 'nps_abtest_name', 'nps_abtest_is_active', 
            'auto_winner', 'min_responses', 'confidence_level'
        ]
        widgets = {
            'survey': forms.Select(attrs={'class': 'form-select'}),
            'nps_abtest_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nps_abtest_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_winner': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'min_responses': forms.NumberInput(attrs={'class': 'form-control'}),
            'confidence_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class NpsAbVariantForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = NpsAbVariant
        fields = ['variant', 'question_text', 'follow_up_question', 'delivery_delay_hours', 'assignment_rate']
        widgets = {
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'follow_up_question': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'delivery_delay_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'assignment_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

NpsAbVariantFormSet = inlineformset_factory(
    NpsAbTest,
    NpsAbVariant,
    form=NpsAbVariantForm,
    fk_name='ab_test',
    extra=2,
    max_num=2,
    min_num=2,
    validate_min=True,
    can_delete=False
)

# --- Escalation Rules ---

class NpsEscalationRuleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = NpsEscalationRule
        fields = ['name', 'is_active', 'response_type', 'min_score', 'max_score', 'requires_comment', 'auto_escalate_after_hours']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'response_type': forms.Select(attrs={'class': 'form-select'}),
            'min_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'requires_comment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_escalate_after_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class NpsEscalationActionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = NpsEscalationAction
        fields = ['name', 'description', 'action_type', 'is_active', 'action_parameters', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'action_parameters': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

NpsEscalationRuleActionFormSet = inlineformset_factory(
    NpsEscalationRule,
    NpsEscalationRuleAction,
    fields=['escalation_action', 'order'],
    extra=1,
    can_delete=True,
    widgets={
        'escalation_action': forms.Select(attrs={'class': 'form-select'}),
        'order': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)