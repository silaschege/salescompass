from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from core.permissions import ObjectPermissionRequiredMixin
from .models import Case, KnowledgeBaseArticle, CsatResponse, CsatDetractorAlert, AssignmentRule
from .forms import CaseForm, AssignmentRuleForm
from .utils import get_overdue_cases
from .utils import calculate_sla_due_date


from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from .models import CsatDetractorAlert
from core.object_permissions import CaseObjectPolicy
from core.object_permissions import CaseObjectPolicy
from django.utils import timezone
from tenants.models import Tenant as TenantModel
from django.urls import reverse_lazy

class CaseListView(ObjectPermissionRequiredMixin, ListView):
    model = Case
    template_name = 'cases/list.html'
    context_object_name = 'cases'
    paginate_by = 20

class CaseDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Case
    template_name = 'cases/detail.html'


class CaseCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/form.html'
    success_url = '/cases/'

    def form_valid(self, form):
        
        form.instance.sla_due = calculate_sla_due_date(form.instance.priority)
        messages.success(self.request, f"Case '{form.instance.subject}' created!")
        return super().form_valid(form)
    
    # In CaseCreateView
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs


class CaseUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/form.html'
    success_url = '/cases/'


class CaseDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Case
    template_name = 'cases/confirm_delete.html'
    success_url = '/cases/'

    def delete(self, request, *args, **kwargs):
        case = self.get_object()
        messages.success(request, f"Case '{case.subject}' deleted.")
        return super().delete(request, *args, **kwargs)


# === CSAT Views ===
class CsatSurveyView(TemplateView):
    template_name = 'cases/csat_survey.html'

    def post(self, request, *args, **kwargs):
        case_id = request.POST.get('case_id')
        score = int(request.POST.get('score', 0))
        comment = request.POST.get('comment', '')
        
        from .utils import close_case_with_csat
        close_case_with_csat(case_id, score, comment)
        
        return redirect('cases:csat_thank_you')


class CsatThankYouView(TemplateView):
    template_name = 'cases/csat_thank_you.html'


# === Knowledge Base Views ===
class KnowledgeBaseView(ListView):
    model = KnowledgeBaseArticle
    template_name = 'cases/knowledge_base.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return KnowledgeBaseArticle.objects.filter(is_published=True)


# === Kanban View ===
class CaseKanbanView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'cases/kanban.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases = self.get_queryset()
        context['cases'] = cases
        context['status_choices'] = Case._meta.get_field('status').choices
        return context

    def get_queryset(self):
        from core.object_permissions import CaseObjectPolicy
        return CaseObjectPolicy.get_viewable_queryset(self.request.user, Case.objects.all())


# === SLA Dashboard ===
class SlaDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'cases/sla_dashboard.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        
        overdue_cases = get_overdue_cases(getattr(self.request.user, 'tenant_id', None))
        total_cases = Case.objects.filter(status__in=['new', 'in_progress']).count()
        breach_rate = (overdue_cases.count() / total_cases * 100) if total_cases > 0 else 0
        
        context.update({
            'total_overdue': overdue_cases.count(),
            'breach_rate': round(breach_rate, 2),
            'overdue_cases': overdue_cases[:50],
        })
        return context


# === Detractor Kanban ===
class DetractorKanbanView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'cases/detractor_kanban.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alerts = CsatDetractorAlert.objects.all()
        context['alerts'] = alerts
        context['status_choices'] = CsatDetractorAlert._meta.get_field('status').choices
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
            
            
            alert = get_object_or_404(CsatDetractorAlert, id=alert_id)
            
            
            if not CaseObjectPolicy.can_change(request.user, alert.response.case):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            alert.status = new_status
            if new_status == 'resolved':
                
                alert.resolved_at = timezone.now()
            alert.save(update_fields=['status', 'resolved_at'])
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        


class UpdateCaseStatusView(View):
    """AJAX endpoint to update case status."""
    
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        try:
            data = json.loads(request.body)
            case_id = data.get('case_id')
            new_status = data.get('status')
            
            if new_status not in ['new', 'in_progress', 'resolved', 'closed']:
                return JsonResponse({'error': 'Invalid status'}, status=400)
            
            from .models import Case
            case = get_object_or_404(Case, id=case_id)
            
        
            if not CaseObjectPolicy.can_change(request.user, case):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            case.status = new_status
            case.save(update_fields=['status'])
            
            # If case is resolved/closed, trigger CSAT survey
            if new_status in ['resolved', 'closed'] and not case.csat_score:
                from .utils import send_csat_survey
                send_csat_survey(case.id)
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class AssignmentRuleListView(ListView):
    model = AssignmentRule
    template_name = 'cases/assignment_rule_list.html'
    context_object_name = 'assignment_rules'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('rule_type_ref', 'assigned_to')


class AssignmentRuleCreateView(CreateView):
    model = AssignmentRule
    form_class = AssignmentRuleForm
    template_name = 'cases/assignment_rule_form.html'
    success_url = reverse_lazy('cases:assignment_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Assignment rule created successfully.')
        return super().form_valid(form)


class AssignmentRuleUpdateView(UpdateView):
    model = AssignmentRule
    form_class = AssignmentRuleForm
    template_name = 'cases/assignment_rule_form.html'
    success_url = reverse_lazy('cases:assignment_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Assignment rule updated successfully.')
        return super().form_valid(form)


class AssignmentRuleDeleteView(DeleteView):
    model = AssignmentRule
    template_name = 'cases/assignment_rule_confirm_delete.html'
    success_url = reverse_lazy('cases:assignment_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment rule deleted successfully.')
        return super().delete(request, *args, **kwargs)