from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from core.permissions import PermissionRequiredMixin
from .models import NpsSurvey, NpsResponse, NpsDetractorAlert, NpsTrendSnapshot
from .utils import calculate_nps_score, get_nps_trend_data
# apps/engagement/views.py
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json
# apps/engagement/views.py
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from uuid import UUID
# apps/engagement/views.py
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from core.permissions import PermissionRequiredMixin
from .models import NpsAbTest, NpsAbVariant
from .forms import NpsAbTestForm, NpsAbVariantFormSet

class NpsDashboardView(PermissionRequiredMixin, TemplateView):
    template_name = 'nps/nps_dashboard.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        from .utils import calculate_nps_score
        tenant_id = getattr(user, 'tenant_id', None)
        
        # === Overall Metrics ===
        responses = NpsResponse.objects.filter(tenant_id=tenant_id)
        total_responses = responses.count()
        promoters = responses.filter(score__gte=9).count()
        passives = responses.filter(score__in=[7,8]).count()
        detractors = responses.filter(score__lte=6).count()
        
        nps_score = calculate_nps_score(tenant_id=tenant_id)
        context.update({
            'total_responses': total_responses,
            'promoters': promoters,
            'passives': passives,
            'detractors': detractors,
            'nps_score': nps_score,
        })
        return context


class NpsTrendChartsView(PermissionRequiredMixin, TemplateView):
    template_name = 'nps/nps_trend_chart.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.request.GET.get('period', 'daily')
        context['period'] = period
        context['trend_data_json'] = get_nps_trend_data(
            tenant_id=getattr(self.request.user, 'tenant_id', None),
            period=period
        )# In your NpsTrendChartsView.get_context_data()
#         context.update({
#     'period': period,  # 'daily', 'weekly', 'monthly', or 'yearly'
#     'trend_data_json': trend_data,  # List of {'date': '2023-01-01', 'nps': 42.5}
#     'current_nps_score': current_nps,  # Current NPS score
#     'previous_nps_score': previous_nps,  # Previous period NPS score
#     'promoters': promoters_count,
#     'passives': passives_count,
#     'detractors': detractors_count,
#     'promoters_percent': promoters_percent,
#     'passives_percent': passives_percent,
#     'detractors_percent': detractors_percent,
#     'trend_analysis': {  # Optional trend analysis object
#         'title': 'Improving Trend',
#         'description': 'NPS has improved by 5 points over the last 30 days',
#         'alert_type': 'success',  # 'success', 'warning', 'danger'
#         'period': '30 days'
#     },
#     'best_period': {'date': '2023-12-01', 'nps': 48.2},
#     'worst_period': {'date': '2023-09-01', 'nps': 32.1},
#     'trend_direction': 'up',  # 'up', 'down', or 'stable'
# })
        return context


class NpsResponsesView(PermissionRequiredMixin, ListView):
    model = NpsResponse
    template_name = 'nps/nps_responses.html'
    context_object_name = 'responses'
    paginate_by = 20
    required_permission = 'engagement:read'

    def get_queryset(self):
        return super().get_queryset().select_related('account', 'survey')


class NpsSurveyCreateView(PermissionRequiredMixin, CreateView):
    model = NpsSurvey
    fields = ['name', 'description', 'question_text', 'follow_up_question', 'delivery_method', 'trigger_event']
    template_name = 'nps/nps_survey_form.html'
    success_url = '/nps/nps/surveys/'
    required_permission = 'engagement:write'


class DetractorKanbanView(PermissionRequiredMixin, TemplateView):
    template_name = 'nps/detractor_kanban.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alerts = NpsDetractorAlert.objects.filter(
            tenant_id=getattr(self.request.user, 'tenant_id', None)
        ).select_related('response__account', 'assigned_to')
        context['alerts'] = alerts
        context['status_choices'] = NpsDetractorAlert._meta.get_field('status').choices
        return context



class UpdateDetractorStatusView(View):
    """AJAX endpoint to update detractor alert status."""
    
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        try:
            data = json.loads(request.body)
            alert_id = data.get('alert_id')
            new_status = data.get('status')
            
            if new_status not in ['open', 'in_progress', 'resolved']:
                return JsonResponse({'error': 'Invalid status'}, status=400)
            
            from .models import NpsDetractorAlert
            alert = get_object_or_404(NpsDetractorAlert, id=alert_id)
            
            # Permission check - user should be able to view the account
            from core.object_permissions import AccountObjectPolicy
            if not AccountObjectPolicy.can_change(request.user, alert.response.account):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            alert.status = new_status
            if new_status == 'resolved':
                from django.utils import timezone
                alert.resolved_at = timezone.now()
            alert.save(update_fields=['status', 'resolved_at'])
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



class SubmitNPSView(View):
    """Handle NPS survey submission from email link."""
    
    def get(self, request, survey_id):
        """Display the NPS survey form."""
        # In production, you'd validate the UUID and get the survey
        # For now, we'll show a generic form
        from .models import NpsSurvey
        survey = NpsSurvey.objects.filter(is_active=True).first()
        if not survey:
            survey = NpsSurvey.objects.create(
                name="Default Survey",
                question_text="How likely are you to recommend us?",
                follow_up_question="What's the most important reason for your score?"
            )
        
        context = {
            'survey': survey,
            'survey_id': survey_id,
        }
        return render(request, 'nps/nps_survey.html', context)
    
    def post(self, request, survey_id):
        """Process NPS survey submission."""
        try:
            # Get form data
            account_id = request.POST.get('account_id')
            contact_email = request.POST.get('contact_email')
            survey_id = request.POST.get('survey_id')
            score = int(request.POST.get('score', 0))
            comment = request.POST.get('comment', '')
            
            # Validate score
            if not (-10 <= score <= 10):
                return JsonResponse({'error': 'Invalid NPS score'}, status=400)
            
            # Get account and survey
            from accounts.models import Account
            from .models import NpsSurvey, NpsResponse, NpsDetractorAlert
            
            account = get_object_or_404(Account, id=account_id)
            survey = get_object_or_404(NpsSurvey, id=survey_id)
            
            # Create response
            response = NpsResponse.objects.create(
                account=account,
                contact_email=contact_email,
                survey=survey,
                score=score,
                comment=comment,
                tenant_id=account.tenant_id
            )
            
            # Create detractor alert if needed
            if response.is_detractor:
                NpsDetractorAlert.objects.create(
                    response=response,
                    status='open'
                )
            
            # Emit automation event
            from automation.utils import emit_event
            emit_event('nps.submitted', {
                'response_id': response.id,
                'account_id': account.id,
                'score': score,
                'tenant_id': account.tenant_id,
            })
            
            # Redirect to thank you page
            return HttpResponseRedirect(reverse('engagement:nps_thank_you'))
            
        except Exception as e:
            # Log error and show generic error page
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"NPS submission error: {e}")
            return HttpResponseRedirect(reverse('engagement:nps_thank_you'))



class CreateNpsAbTestView(PermissionRequiredMixin, CreateView):
    """
    Create a new NPS A/B test with variants.
    """
    model = NpsAbTest
    form_class = NpsAbTestForm
    template_name = 'nps/nps_ab_test.html'
    success_url = reverse_lazy('nps:nps_dashboard')
    required_permission = 'nps:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['variants'] = NpsAbVariantFormSet(self.request.POST)
        else:
            context['variants'] = NpsAbVariantFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        variants = context['variants']
        
        if variants.is_valid():
            response = super().form_valid(form)
            
            # Save variants
            variants.instance = self.object
            variants.save()
            
            # Emit event for automation
            from automation.utils import emit_event
            emit_event('nps.ab_test_created', {
                'ab_test_id': self.object.id,
                'survey_id': self.object.survey.id,
                'tenant_id': self.object.tenant_id,
            })
            
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


# Supporting Form and FormSet
# apps/engagement/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import NpsAbTest, NpsAbVariant

class NpsAbTestForm(forms.ModelForm):
    class Meta:
        model = NpsAbTest
        fields = ['survey', 'name', 'is_active', 'auto_winner', 'min_responses', 'confidence_level']
        widgets = {
            'min_responses': forms.NumberInput(attrs={'min': 10, 'max': 10000}),
            'confidence_level': forms.NumberInput(attrs={'min': 0.8, 'max': 0.99, 'step': 0.01}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter surveys to user's tenant
            self.fields['survey'].queryset = self.fields['survey'].queryset.filter(
                tenant_id=user.tenant_id
            )


NpsAbVariantFormSet = inlineformset_factory(
    NpsAbTest,
    NpsAbVariant,
    fields=['variant', 'question_text', 'follow_up_question', 'delivery_delay_hours', 'assignment_rate'],
    extra=2,
    max_num=2,
    min_num=2,
    validate_min=True,
    widgets={
        'question_text': forms.Textarea(attrs={'rows': 2}),
        'follow_up_question': forms.Textarea(attrs={'rows': 2}),
        'delivery_delay_hours': forms.NumberInput(attrs={'min': 0, 'max': 168}),
        'assignment_rate': forms.NumberInput(attrs={'min': 0, 'max': 1, 'step': 0.1}),
    }
)