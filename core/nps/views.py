from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from django.utils import timezone

import json
from uuid import UUID

from core.permissions import PermissionRequiredMixin
from core.object_permissions import AccountObjectPolicy
from tenants.models import TenantMember, TenantTerritory
from accounts.models import Account
from automation.utils import emit_event

from .forms import NpsSurveyForm, NpsConditionalFollowUpFormSet, NpsAbTestForm, NpsAbVariantFormSet, NpsEscalationRuleForm, NpsEscalationRuleActionFormSet, NpsEscalationActionForm
from .models import (
    NpsSurvey,
    NpsResponse,
    NpsDetractorAlert,
    NpsTrendSnapshot,
    NpsPromoterReferral,
    NpsAbVariant,
    NpsAbResponse,
    NpsConditionalFollowUp,
    NpsEscalationRule,
    NpsEscalationAction,
    NpsEscalationActionLog,
    NpsAbTest
)
from .utils import (
    calculate_nps_score, 
    get_nps_trend_data, 
    calculate_response_rate,
    get_detractor_resolution_time,
    get_nps_by_segment,
    identify_promoter_referral_opportunities
)


class NpsDashboardView(PermissionRequiredMixin, TemplateView):
    template_name = 'nps/nps_dashboard.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        
        # Get all surveys for the tenant
        surveys = NpsSurvey.objects.filter(tenant=tenant)
        
        # Get responses for active surveys
        responses = NpsResponse.objects.filter(tenant=tenant)
        
        # Calculate NPS score
        nps_score = calculate_nps_score(tenant_id=tenant.id if tenant else None)
        
        # Calculate response rate
        response_rate = calculate_response_rate(tenant_id=tenant.id if tenant else None)
        
        # Segment analysis
        role_segments = {}
        territory_segments = {}
        
        if tenant:
            # Get all roles and territories from organization members
            roles = TenantMember.objects.filter(tenant=tenant).values_list('role__name', flat=True).distinct()
            territories = TenantMember.objects.filter(tenant=tenant).values_list('territory__name', flat=True).distinct()
            
            # Role-based segmentation
            for role in roles:
                if role:
                    role_count = responses.filter(account__tenant_member__role__name=role).count()
                    if role_count > 0:
                        role_promoters = responses.filter(score__gte=9, account__tenant_member__role__name=role).count()
                        role_detractors = responses.filter(score__lte=6, account__tenant_member__role__name=role).count()
                        role_nps = ((role_promoters - role_detractors) / role_count) * 100
                        role_segments[role] = {
                            'count': role_count,
                            'nps': round(role_nps, 1),
                            'promoters': role_promoters,
                            'detractors': role_detractors,
                            'passives': role_count - role_promoters - role_detractors
                        }
            
            # Territory-based segmentation
            for territory in territories:
                if territory:
                    territory_count = responses.filter(account__tenant_member__territory__name=territory).count()
                    if territory_count > 0:
                        territory_promoters = responses.filter(score__gte=9, account__tenant_member__territory__name=territory).count()
                        territory_detractors = responses.filter(score__lte=6, account__tenant_member__territory__name=territory).count()
                        territory_nps = ((territory_promoters - territory_detractors) / territory_count) * 100
                        territory_segments[territory] = {
                            'count': territory_count,
                            'nps': round(territory_nps, 1),
                            'promoters': territory_promoters,
                            'detractors': territory_detractors,
                            'passives': territory_count - territory_promoters - territory_detractors
                        }
        
        # Benchmark data
        industry_benchmarks = {
            'technology': 45,
            'retail': 35,
            'healthcare': 52,
            'financial_services': 60,
            'telecommunications': 38,
        }
        
        # Recent responses
        recent_responses = responses.order_by('-id')[:10]
        
        # Survey stats
        active_surveys = surveys.filter(nps_survey_is_active=True).count()
        scheduled_surveys = surveys.filter(
            nps_survey_is_active=True,
            scheduled_start_date__gt=timezone.now()
        ).count()
        expired_surveys = surveys.filter(
            nps_survey_is_active=True,
            scheduled_end_date__lt=timezone.now()
        ).count()
        pending_surveys = scheduled_surveys  # For simplicity, treating scheduled as pending
        
        # Advanced analytics
        detractor_resolution_stats = get_detractor_resolution_time(tenant_id=tenant.id if tenant else None)
        
        # NPS by segment (using new utility function)
        nps_by_role = get_nps_by_segment('role', tenant_id=tenant.id if tenant else None)
        nps_by_territory = get_nps_by_segment('territory', tenant_id=tenant.id if tenant else None)
        
        context.update({
            'total_responses': responses.count(),
            'promoters': responses.filter(score__gte=9).count(),
            'passives': responses.filter(score__in=[7,8]).count(),
            'detractors': responses.filter(score__lte=6).count(),
            'nps_score': nps_score,
            'response_rate': response_rate,
            'recent_responses': recent_responses,
            'role_segments': role_segments,
            'territory_segments': territory_segments,
            'industry_benchmarks': industry_benchmarks,
            'active_surveys': active_surveys,
            'scheduled_surveys': scheduled_surveys,
            'expired_surveys': expired_surveys,
            'pending_surveys': pending_surveys,
            'surveys': surveys,
            'now': timezone.now(),
            'detractor_resolution_stats': detractor_resolution_stats,
            'nps_by_role': nps_by_role,
            'nps_by_territory': nps_by_territory
        })
        return context


class NpsTrendChartsView(PermissionRequiredMixin, TemplateView):
    template_name = 'nps/nps_trend_chart.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.request.GET.get('period', 'daily')
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        context['period'] = period
        context['trend_data_json'] = get_nps_trend_data(
            tenant_id=tenant.id if tenant else None,
            period=period
        )
        return context


class NpsResponsesView(PermissionRequiredMixin, ListView):
    model = NpsResponse
    template_name = 'nps/nps_responses.html'
    context_object_name = 'responses'
    paginate_by = 20
    required_permission = 'engagement:read'

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        return super().get_queryset().select_related('account', 'survey').filter(tenant=tenant)


class NpsSurveyCreateView(PermissionRequiredMixin, CreateView):
    model = NpsSurvey
    form_class = NpsSurveyForm
    template_name = 'nps/nps_survey_form.html'
    success_url = '/nps/nps/surveys/'
    required_permission = 'engagement:write'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['conditional_follow_up_formset'] = NpsConditionalFollowUpFormSet(self.request.POST)
        else:
            context['conditional_follow_up_formset'] = NpsConditionalFollowUpFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        conditional_follow_up_formset = context['conditional_follow_up_formset']
        
        # Set the tenant for the survey
        form.instance.tenant = self.request.user.tenant
        
        # Check if the formset is valid
        if conditional_follow_up_formset.is_valid():
            # Save the survey first
            self.object = form.save()
            
            # Save the conditional follow-ups
            conditional_follow_up_formset.instance = self.object
            conditional_follow_up_formset.save()
            
            # Emit event for automation
            emit_event('nps.survey_created', {
                'survey_id': self.object.id,
                'tenant_id': self.object.tenant.id,
            })
            
            return super().form_valid(form)
        else:
            # If formset is invalid, render the form again with errors
            return self.render_to_response(self.get_context_data(form=form))


class DetractorKanbanView(PermissionRequiredMixin, TemplateView):
    template_name = 'nps/detractor_kanban.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        alerts = NpsDetractorAlert.objects.filter(
            tenant=tenant
        ).select_related('response__account', 'assigned_to').prefetch_related('response__survey')
        
        # Group alerts by status
        open_alerts = alerts.filter(status='open')
        in_progress_alerts = alerts.filter(status='in_progress')
        resolved_alerts = alerts.filter(status='resolved')
        
        # Add summary statistics
        total_alerts = alerts.count()
        open_count = open_alerts.count()
        in_progress_count = in_progress_alerts.count()
        resolved_count = resolved_alerts.count()
        
        # Add user assignment options
        team_members = TenantMember.objects.filter(tenant=tenant)
        
        context['alerts'] = alerts
        context['open_alerts'] = open_alerts
        context['in_progress_alerts'] = in_progress_alerts
        context['resolved_alerts'] = resolved_alerts
        context['status_choices'] = NpsDetractorAlert._meta.get_field('status').choices
        context['team_members'] = team_members
        context['total_alerts'] = total_alerts
        context['open_count'] = open_count
        context['in_progress_count'] = in_progress_count
        context['resolved_count'] = resolved_count
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
            
            alert = get_object_or_404(NpsDetractorAlert, id=alert_id)
            
            # Permission check - user should be able to view the account
            if not AccountObjectPolicy.can_change(request.user, alert.response.account):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            alert.status = new_status
            if new_status == 'resolved':
                alert.resolved_at = timezone.now()
            alert.save(update_fields=['status', 'resolved_at'])
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class SubmitNPSView(View):
    """Handle NPS survey submission from email link."""
    
    def get(self, request, survey_id):
        """Display the NPS survey form."""
        # Get survey with current tenant
        survey = get_object_or_404(NpsSurvey, id=survey_id)
        
        # Check if survey is active and within scheduling dates
        if not survey.is_currently_active:
            return render(request, 'nps/survey_inactive.html', {'survey': survey})
        
        # Get conditional follow-up questions
        conditional_questions = NpsConditionalFollowUp.objects.filter(survey=survey)
        
        context = {
            'survey': survey,
            'survey_id': survey_id,
            'conditional_questions': conditional_questions,
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
            if not (0 <= score <= 10):  # Standard NPS score range
                # Check if it's an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Invalid NPS score'}, status=400)
                return JsonResponse({'error': 'Invalid NPS score'}, status=400)
            
            # Get account and survey
            account = get_object_or_404(Account, id=account_id)
            survey = get_object_or_404(NpsSurvey, id=survey_id)
            
            # Check if survey is active
            if not survey.is_currently_active:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'This survey is not currently active'}, status=400)
                return JsonResponse({'error': 'This survey is not currently active'}, status=400)
            

            # Handle comments based on follow-up logic
            if survey.enable_follow_up_logic:
                # Try to get conditional comment first
                conditional_questions = NpsConditionalFollowUp.objects.filter(survey=survey).order_by('-score_threshold')
                for cq in conditional_questions:
                    if score >= cq.score_threshold:
                        comment_field_name = f"comment_{cq.score_threshold}"
                        comment = request.POST.get(comment_field_name, "")
                        break
                
                # If no conditional comment found, use default comment
                if not comment:
                    comment = request.POST.get('comment', '')
            
            # Create response
            response = NpsResponse.objects.create(
                account=account,
                contact_email=contact_email,
                survey=survey,
                score=score,
                comment=comment,
                tenant=account.tenant
            )
            
            # Create detractor alert if needed
            if response.is_detractor:
                NpsDetractorAlert.objects.create(
                    response=response,
                    status='open',
                    tenant=response.tenant
                )
            
            # Emit automation event
            emit_event('nps.submitted', {
                'response_id': response.id,
                'account_id': account.id,
                'score': score,
                'comment': comment,
                'tenant_id': account.tenant.id,
            })
            
            # Check if it's an AJAX request (from the widget)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            # Redirect to thank you page
            return HttpResponseRedirect(reverse('nps:nps_dashboard'))

            
        except Exception as e:
            # Log error and show generic error page
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"NPS submission error: {e}")
            
            # Check if it's an AJAX request (from the widget)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
                
            return HttpResponseRedirect(reverse('nps:nps_dashboard'))


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
        
        # Set tenant for the AB test
        form.instance.tenant = self.request.user.tenant
        
        if variants.is_valid():
            response = super().form_valid(form)
            
            # Save variants
            variants.instance = self.object
            variants.save()
            
            # Emit event for automation
            emit_event('nps.ab_test_created', {
                'ab_test_id': self.object.id,
                'survey_id': self.object.survey.id,
                'tenant_id': self.object.tenant.id,
            })
            
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class InAppNPSWidgetView(View):
    """
    Render the in-app NPS survey widget.
    This view can be embedded in other pages to show the NPS widget.
    """
    
    def get(self, request):
        # Check if user should receive NPS survey
        # In a real implementation, this would check various conditions
        # like last survey date, user activity, etc.
        
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        # Get active survey for the tenant
        survey = NpsSurvey.objects.filter(
            nps_survey_is_active=True,
            tenant=request.user.tenant
        ).first()
        
        if not survey:
            # Create a default survey if none exists
            survey = NpsSurvey.objects.create(
                nps_survey_name="Default In-App Survey",
                question_text="How likely are you to recommend us to a friend or colleague?",
                follow_up_question="What's the most important reason for your score?",
                nps_survey_is_active=True,
                tenant=request.user.tenant
            )
        
        context = {
            'survey': survey,
            'account': request.user,
        }
        
        return render(request, 'nps/in_app_widget.html', context)


class EmbedNPSWidgetView(TemplateView):
    """
    Example view showing how to embed the NPS widget in another page.
    This would typically be part of another app's view.
    """
    template_name = 'nps/embed_example.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any context needed for the page that will embed the widget
        return context


class PromoterAdvocacyView(PermissionRequiredMixin, TemplateView):
    template_name = 'nps/promoter_advocacy.html'
    required_permission = 'engagement:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        
        # Get promoters (scores 9-10)
        promoters = NpsResponse.objects.filter(
            tenant=tenant,
            score__gte=9
        ).select_related('account', 'survey')
        
        # Add segmentation data
        role_segments = {}
        roles = TenantMember.objects.filter(tenant=tenant).values_list('role__name', flat=True).distinct()
        for role in roles:
            if role:  # Skip None values
                role_promoters = promoters.filter(account__tenant_member__role__name=role)
                role_count = role_promoters.count()
                if role_count > 0:
                    role_segments[role] = {
                        'count': role_count,
                        'percentage': round((role_count / promoters.count()) * 100, 1) if promoters.count() > 0 else 0
                    }
        
        # By territory
        territory_segments = {}
        territories = TenantMember.objects.filter(tenant=tenant).values_list('territory__name', flat=True).distinct()
        for territory in territories:
            if territory:  # Skip None values
                territory_promoters = promoters.filter(account__tenant_member__territory__name=territory)
                territory_count = territory_promoters.count()
                if territory_count > 0:
                    territory_segments[territory] = {
                        'count': territory_count,
                        'percentage': round((territory_count / promoters.count()) * 100, 1) if promoters.count() > 0 else 0
                    }
        
        # Get referral opportunities
        referral_opportunities = identify_promoter_referral_opportunities(
            tenant_id=tenant.id if tenant else None
        )
        
        context.update({
            'promoters': promoters,
            'total_promoters': promoters.count(),
            'role_segments': role_segments,
            'territory_segments': territory_segments,
            'referral_opportunities': referral_opportunities,
            'referral_opportunities_count': len(referral_opportunities)
        })
        return context


class PromoterReferralListView(PermissionRequiredMixin, ListView):
    model = NpsPromoterReferral
    template_name = 'nps/promoter_referral_list.html'
    context_object_name = 'referrals'
    required_permission = 'engagement:read'
    
    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        return NpsPromoterReferral.objects.filter(
            tenant=tenant
        ).select_related(
            'promoter_response__account',
            'promoter_response__survey',
            'assigned_to'
        ).order_by('-created_at')


class PromoterReferralUpdateView(PermissionRequiredMixin, UpdateView):
    model = NpsPromoterReferral
    template_name = 'nps/promoter_referral_form.html'
    fields = [
        'referred_contact_name',
        'referred_contact_email', 
        'referred_contact_phone',
        'referred_company_name',
        'referred_company_domain',
        'status',
        'assigned_to',
        'deal_value',
        'notes'
    ]
    required_permission = 'engagement:update'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Emit event for automation
        referral = self.object
        emit_event('nps.promoter_referral_updated', {
            'referral_id': referral.id,
            'account_id': referral.promoter_response.account_id,
            'status': referral.status,
            'tenant_id': referral.tenant_id,
        })
        
        return response
    
    def get_success_url(self):
        return reverse('nps:promoter_referrals')


class NpsEscalationRuleListView(PermissionRequiredMixin, ListView):
    model = NpsEscalationRule
    template_name = 'nps/escalation_rule_list.html'
    context_object_name = 'rules'
    required_permission = 'engagement:read'
    
    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        return NpsEscalationRule.objects.filter(tenant=tenant).order_by('-is_active', 'name')


class NpsEscalationRuleCreateView(PermissionRequiredMixin, CreateView):
    model = NpsEscalationRule
    form_class = NpsEscalationRuleForm
    template_name = 'nps/escalation_rule_form.html'
    required_permission = 'engagement:create'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['action_formset'] = NpsEscalationRuleActionFormSet(self.request.POST)
        else:
            context['action_formset'] = NpsEscalationRuleActionFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        action_formset = context['action_formset']
        
        # Set the tenant for the rule
        form.instance.tenant = self.request.user.tenant
        
        # Check if the formset is valid
        if action_formset.is_valid():
            # Save the rule first
            self.object = form.save()
            
            # Save the actions
            action_formset.instance = self.object
            action_formset.save()
            
            return super().form_valid(form)
        else:
            # If formset is invalid, render the form again with errors
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return reverse('nps:escalation_rules')


class NpsEscalationRuleUpdateView(PermissionRequiredMixin, UpdateView):
    model = NpsEscalationRule
    form_class = NpsEscalationRuleForm
    template_name = 'nps/escalation_rule_form.html'
    required_permission = 'engagement:update'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['action_formset'] = NpsEscalationRuleActionFormSet(self.request.POST, instance=self.object)
        else:
            context['action_formset'] = NpsEscalationRuleActionFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        action_formset = context['action_formset']
        
        # Check if the formset is valid
        if action_formset.is_valid():
            # Save the rule
            self.object = form.save()
            
            # Save the actions
            action_formset.instance = self.object
            action_formset.save()
            
            return super().form_valid(form)
        else:
            # If formset is invalid, render the form again with errors
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return reverse('nps:escalation_rules')




class NpsEscalationActionListView(PermissionRequiredMixin, ListView):
    model = NpsEscalationAction
    template_name = 'nps/escalation_action_list.html'
    context_object_name = 'actions'
    required_permission = 'engagement:read'
    
    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        return NpsEscalationAction.objects.filter(tenant=tenant).order_by('order', 'name')


class NpsEscalationActionCreateView(PermissionRequiredMixin, CreateView):
    model = NpsEscalationAction
    form_class = NpsEscalationActionForm
    template_name = 'nps/escalation_action_form.html'
    required_permission = 'engagement:create'
    
    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('nps:escalation_actions')


class NpsEscalationActionUpdateView(PermissionRequiredMixin, UpdateView):
    model = NpsEscalationAction
    form_class = NpsEscalationActionForm
    template_name = 'nps/escalation_action_form.html'
    required_permission = 'engagement:update'
    
    def get_success_url(self):
        return reverse('nps:escalation_actions')

class NpsEscalationActionLogListView(PermissionRequiredMixin, ListView):
    model = NpsEscalationActionLog
    template_name = 'nps/escalation_action_log_list.html'
    context_object_name = 'action_logs'
    required_permission = 'engagement:read'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        return NpsEscalationActionLog.objects.filter(
            tenant=tenant
        ).select_related(
            'escalation_rule',
            'action',
            'nps_response__account',
            'nps_response__survey'
        ).order_by('-created_at')

class NpsTrendSnapshotListView(PermissionRequiredMixin, ListView):
    model = NpsTrendSnapshot
    template_name = 'nps/trend_snapshot_list.html'
    context_object_name = 'snapshots'
    required_permission = 'engagement:read'
    paginate_by = 30
    
    def get_queryset(self):
        user = self.request.user
        tenant = getattr(user, 'tenant', None)
        return NpsTrendSnapshot.objects.filter(
            tenant=tenant
        ).order_by('-date')