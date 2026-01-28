from django import forms
from .models import LoyaltyProgram, LoyaltyTransaction

class LoyaltyProgramForm(forms.ModelForm):
    class Meta:
        model = LoyaltyProgram
        fields = ['program_name', 'description', 'points_per_currency', 'redemption_conversion_rate', 'min_redemption_points', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

class PointsAdjustmentForm(forms.ModelForm):
    class Meta:
        model = LoyaltyTransaction
        fields = ['points', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Reason for adjustment'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
    
    def clean_points(self):
        points = self.cleaned_data['points']
        if points == 0:
            raise forms.ValidationError("Points adjustment cannot be zero.")
        return points
