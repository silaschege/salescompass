# apps/engagement/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import NpsAbTest, NpsAbVariant, NpsSurvey

class NpsAbTestForm(forms.ModelForm):
    """
    Form for creating and updating NPS A/B tests.
    """
    class Meta:
        model = NpsAbTest
        fields = [
            'survey', 
            'nps_abtest_name', 
            'nps_abtest_is_active', 
            'auto_winner', 
            'min_responses', 
            'confidence_level'
        ]
        widgets = {
            'survey': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select NPS survey to test'
            }),
            'nps_abtest_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Question Wording Test'
            }),
            'nps_abtest_is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'min_responses': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 10, 
                'max': 10000,
                'placeholder': 'Minimum responses per variant'
            }),
            'confidence_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.8, 
                'max': 0.99, 
                'step': 0.01,
                'placeholder': 'Statistical confidence (0.80-0.99)'
            }),
        }
        help_texts = {
            'survey': 'Select the NPS survey you want to A/B test',
            'nps_abtest_name': 'Give your A/B test a descriptive name',
            'nps_abtest_is_active': 'Enable this test to start sending variants',
            'auto_winner': 'Automatically select winner when statistical significance is reached',
            'min_responses': 'Minimum total responses needed before declaring a winner',
            'confidence_level': 'Statistical confidence level (95% = 0.95)'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter surveys to user's tenant and active surveys only
            self.fields['survey'].queryset = NpsSurvey.objects.filter(
                tenant_id=user.tenant_id,
                nps_survey_is_active=True
            )
        else:
            # If no user, show only active surveys
            self.fields['survey'].queryset = NpsSurvey.objects.filter(nps_survey_is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        min_responses = cleaned_data.get('min_responses')
        confidence_level = cleaned_data.get('confidence_level')
        
        if min_responses and min_responses < 10:
            raise ValidationError('Minimum responses must be at least 10.')
        
        if confidence_level and (confidence_level < 0.8 or confidence_level > 0.99):
            raise ValidationError('Confidence level must be between 0.80 and 0.99.')
        
        return cleaned_data

    def clean_survey(self):
        survey = self.cleaned_data['survey']
        if not survey.nps_survey_is_active:
            raise ValidationError('Selected survey must be active.')
        return survey


class NpsAbVariantForm(forms.ModelForm):
    """
    Form for individual A/B test variants.
    """
    class Meta:
        model = NpsAbVariant
        fields = [
            'variant', 
            'question_text', 
            'follow_up_question', 
            'delivery_delay_hours', 
            'assignment_rate'
        ]
        widgets = {
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'How likely are you to recommend us to a friend or colleague?'
            }),
            'follow_up_question': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "What's the most important reason for your score?"
            }),
            'delivery_delay_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 168,
                'placeholder': 'Delay in hours (0-168)'
            }),
            'assignment_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1,
                'step': 0.1,
                'placeholder': 'Assignment rate (0.0-1.0)'
            }),
        }
        help_texts = {
            'variant': 'Variant A or B',
            'question_text': 'NPS question text for this variant',
            'follow_up_question': 'Follow-up question for this variant',
            'delivery_delay_hours': 'Delay delivery by specified hours after trigger',
            'assignment_rate': 'Proportion of recipients to assign to this variant (0.0-1.0)'
        }

    def clean_assignment_rate(self):
        rate = self.cleaned_data['assignment_rate']
        if rate is not None and (rate < 0 or rate > 1):
            raise ValidationError('Assignment rate must be between 0 and 1.')
        return rate

    def clean_delivery_delay_hours(self):
        hours = self.cleaned_data['delivery_delay_hours']
        if hours is not None and (hours < 0 or hours > 168):
            raise ValidationError('Delivery delay must be between 0 and 168 hours (1 week).')
        return hours


# Create the formset for variants
NpsAbVariantFormSet = inlineformset_factory(
    NpsAbTest,
    NpsAbVariant,
    fk_name='ab_test',  # <--- CRITICAL FIX: Specifies which ForeignKey to use
    form=NpsAbVariantForm,
    fields=[
        'variant', 
        'question_text', 
        'follow_up_question', 
        'delivery_delay_hours', 
        'assignment_rate'
    ],
    extra=2,
    max_num=2,
    min_num=2,
    validate_min=True,
    can_delete=False,
    widgets={
        'variant': forms.Select(attrs={'class': 'form-select'}),
        'question_text': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        'follow_up_question': forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3
        }),
        'delivery_delay_hours': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'max': 168
        }),
        'assignment_rate': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'max': 1,
            'step': 0.1
        }),
    }
)


# Additional forms for other NPS functionality
class NpsSurveyForm(forms.ModelForm):
    """
    Form for creating and updating NPS surveys.
    """
    class Meta:
        model = NpsSurvey
        fields = [
            'nps_survey_name',
            'nps_survey_description', 
            'question_text', 
            'follow_up_question', 
            'delivery_method', 
            'trigger_event',
            'nps_survey_is_active'
        ]
        widgets = {
            'nps_survey_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nps_survey_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'follow_up_question': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_method': forms.Select(attrs={'class': 'form-select'}),
            'trigger_event': forms.Select(attrs={'class': 'form-select'}),
            'nps_survey_is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NpsResponseFilterForm(forms.Form):
    """
    Form for filtering NPS responses in the dashboard.
    """
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    score_type = forms.ChoiceField(
        choices=[
            ('', 'All Scores'),
            ('promoters', 'Promoters (9-10)'),
            ('passives', 'Passives (7-8)'),
            ('detractors', 'Detractors (0-6)')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    survey = forms.ModelChoiceField(
        queryset=NpsSurvey.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['survey'].queryset = NpsSurvey.objects.filter(tenant_id=user.tenant_id)