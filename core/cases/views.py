from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from core.permissions import ObjectPermissionRequiredMixin
from .models import Case, CsatResponse, CsatDetractorAlert, AssignmentRule, CaseAttachment, CaseComment, SlaPolicy
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

from django.utils import timezone
from tenants.models import Tenant as TenantModel
from django.urls import reverse_lazy

class CaseListView(ObjectPermissionRequiredMixin, ListView):
    model = Case
    template_name = 'cases/case_list.html'
    context_object_name = 'cases'
    paginate_by = 20

class CaseDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Case
    template_name = 'cases/case_detail.html'


class CaseCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/case_form.html'
    success_url = reverse_lazy('cases:case_list')

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
    template_name = 'cases/case_form.html'
    success_url = reverse_lazy('cases:case_list')


class CaseDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Case
    template_name = 'cases/case_confirm_delete.html'
    success_url = reverse_lazy('cases:case_list')

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


# === Kanban View ===
class CaseKanbanView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'cases/case_kanban.html'
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


# === Assignment Rule Views ===
class AssignmentRuleDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = AssignmentRule
    template_name = 'cases/assignment_rule_detail.html'
    context_object_name = 'assignment_rule'


# === CSAT Response Views ===
class CsatResponseListView(ObjectPermissionRequiredMixin, ListView):
    model = CsatResponse
    template_name = 'cases/csat_response_list.html'
    context_object_name = 'csat_responses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('case')


class CsatResponseDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = CsatResponse
    template_name = 'cases/csat_response_detail.html'
    context_object_name = 'response'


# === Case Comment Views ===
class CaseCommentListView(ObjectPermissionRequiredMixin, ListView):
    model = CaseComment
    template_name = 'cases/case_comment_list.html'
    context_object_name = 'comments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('case', 'author')


class CaseCommentCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = CaseComment
    fields = ['case', 'content', 'is_internal']
    template_name = 'cases/case_comment_form.html'
    success_url = reverse_lazy('cases:case_comment_list')
    
    def form_valid(self, form):
        # Set author and tenant automatically
        form.instance.author = self.request.user
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Case comment created successfully.')
        return super().form_valid(form)


class CaseCommentUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = CaseComment
    fields = ['content', 'is_internal']
    template_name = 'cases/case_comment_form.html'
    success_url = reverse_lazy('cases:case_comment_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Case comment updated successfully.')
        return super().form_valid(form)


class CaseCommentDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = CaseComment
    template_name = 'cases/case_comment_confirm_delete.html'
    success_url = reverse_lazy('cases:case_comment_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Case comment deleted successfully.')
        return super().delete(request, *args, **kwargs)


# === Case Attachment Views ===
class CaseAttachmentListView(ObjectPermissionRequiredMixin, ListView):
    model = CaseAttachment
    template_name = 'cases/case_attachment_list.html'
    context_object_name = 'attachments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('case', 'uploaded_by')


class CaseAttachmentCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = CaseAttachment
    fields = ['case', 'file']
    template_name = 'cases/case_attachment_form.html'
    success_url = reverse_lazy('cases:case_attachment_list')
    
    def form_valid(self, form):
        # Set uploaded_by and tenant automatically
        form.instance.uploaded_by = self.request.user
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Case attachment created successfully.')
        return super().form_valid(form)


class CaseAttachmentUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = CaseAttachment
    fields = ['case', 'file']
    template_name = 'cases/case_attachment_form.html'
    success_url = reverse_lazy('cases:case_attachment_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Case attachment updated successfully.')
        return super().form_valid(form)


class CaseAttachmentDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = CaseAttachment
    template_name = 'cases/case_attachment_confirm_delete.html'
    success_url = reverse_lazy('cases:case_attachment_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Case attachment deleted successfully.')
        return super().delete(request, *args, **kwargs)


# === SLA Policy Views ===
class SlaPolicyListView(ObjectPermissionRequiredMixin, ListView):
    model = SlaPolicy
    template_name = 'cases/sla_policy_list.html'
    context_object_name = 'sla_policies'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class SlaPolicyCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = SlaPolicy
    fields = ['sla_policy_name', 'priority', 'response_hours', 'resolution_hours', 'business_hours_only']
    template_name = 'cases/sla_policy_form.html'
    success_url = reverse_lazy('cases:sla_policy_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'SLA policy created successfully.')
        return super().form_valid(form)


class SlaPolicyDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = SlaPolicy
    template_name = 'cases/sla_policy_detail.html'
    context_object_name = 'sla_policy'


class SlaPolicyUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = SlaPolicy
    fields = ['sla_policy_name', 'priority', 'response_hours', 'resolution_hours', 'business_hours_only']
    template_name = 'cases/sla_policy_form.html'
    success_url = reverse_lazy('cases:sla_policy_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'SLA policy updated successfully.')
        return super().form_valid(form)


class SlaPolicyDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = SlaPolicy
    template_name = 'cases/sla_policy_confirm_delete.html'
    success_url = reverse_lazy('cases:sla_policy_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'SLA policy deleted successfully.')
        return super().delete(request, *args, **kwargs)


