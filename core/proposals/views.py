import datetime
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, 
    DeleteView, TemplateView, View
)
from django.utils import timezone

from core.permissions import ObjectPermissionRequiredMixin
from .models import Proposal, ProposalEmail, ProposalPDF, ProposalTemplate, ProposalEvent, ProposalSignature, PROPOSAL_STATUS_CHOICES,ApprovalTemplateStep
from .forms import (
    ProposalForm, ProposalTemplateForm, ProposalEmailForm, 
    ProposalPDFForm, ProposalEventForm, ProposalSignatureForm, 
    ApprovalStepForm, ProposalApprovalForm, ApprovalTemplateForm,
    ProposalLineFormSet
)
from .utils import (
    send_proposal_email, 
    generate_proposal_pdf, 
    track_email_open, 
    track_link_click, 
    record_proposal_view, 
    record_esg_view,
    record_proposal_acceptance,
    record_proposal_rejection
)

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import ApprovalStep, ProposalApproval, ApprovalTemplate
from django.forms import inlineformset_factory
from django.urls import reverse


from .forms import ProposalForm, ProposalTemplateForm, ProposalEmailForm, ProposalPDFForm, ProposalEventForm, ProposalSignatureForm, ApprovalStepForm, ProposalApprovalForm, ApprovalTemplateForm, ApprovalTemplateStepForm


ApprovalStepFormSet = inlineformset_factory(
    ApprovalTemplate, 
    ApprovalTemplateStep, 
    form=ApprovalTemplateStepForm,
    extra=1,
    can_delete=True
)






@csrf_exempt
@require_http_methods(["POST"])
def save_proposal_signature(request, pk):
    """View to save digital signature for a proposal."""
    try:
        data = json.loads(request.body)
        signature_data = data.get('signature')
        name = data.get('name')
        title = data.get('title')
        
        if not all([signature_data, name, title]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        # Get or update the signature
        try:
            proposal = Proposal.objects.get(pk=pk)
            signature, created = ProposalSignature.objects.update_or_create(
                proposal=proposal,
                defaults={
                    'signature_data': signature_data,
                    'signer_name': name,
                    'signer_title': title,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT')
                }
            )
            
            # Update proposal status to accepted
            if proposal.status != 'accepted':
                proposal.status = 'accepted'
                proposal.save()
            
            return JsonResponse({'success': True})
        except Proposal.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Proposal not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})




class ProposalSignView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'proposals/signature.html'
    permission_action = 'sign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proposal'] = get_object_or_404(Proposal, pk=kwargs['pk'])
        context['today'] = datetime.date.today()
        return context


class AcceptProposalView(ObjectPermissionRequiredMixin, View):
    """View to handle client acceptance of a proposal."""
    
    def post(self, request, pk):
        try:
            # Record proposal acceptance with IP and user agent
            record_proposal_acceptance(
                proposal_id=pk,
                ip=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            # Return success response
            return JsonResponse({'success': True, 'message': 'Proposal accepted successfully'})
        except Proposal.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Proposal not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class RejectProposalView(ObjectPermissionRequiredMixin, View):
    """View to handle client rejection of a proposal."""
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            reason = data.get('reason', '')
            
            # Record proposal rejection with reason, IP and user agent
            record_proposal_rejection(
                proposal_id=pk,
                reason=reason,
                ip=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            # Return success response
            return JsonResponse({'success': True, 'message': 'Proposal rejected successfully'})
        except Proposal.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Proposal not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})





# === Tracking Views ===
def track_email_open_view(request, token):
    """View to track email opens via 1x1 pixel."""
    track_email_open(token)
    
    # Return 1x1 transparent PNG
    pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\x00\x00\x00\x00IEND\xaeB`\x82'
    return HttpResponse(pixel, content_type='image/png')


def track_link_click_view(request, token):
    """View to track link clicks and redirect."""
    url = request.GET.get('url', '/')
    track_link_click(token, url)
    return redirect(url)


class TrackProposalView(ObjectPermissionRequiredMixin, View):
    """View to track when a proposal is viewed directly."""
    
    def get(self, request, pk):
        # Record proposal view with IP and user agent
        record_proposal_view(
            proposal_id=pk, 
            ip=request.META.get('REMOTE_ADDR'), 
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        # Return the proposal content for client viewing
        proposal = get_object_or_404(Proposal, pk=pk)
        return render(request, 'proposals/client_view.html', {'proposal': proposal})


class TrackESGSectionView(ObjectPermissionRequiredMixin, View):
    """View to track when the ESG section is specifically viewed."""
    
    def post(self, request, pk):
        record_esg_view(proposal_id=pk)
        return JsonResponse({'success': True})


# === Proposal CRUD Views ===
class ProposalListView(ObjectPermissionRequiredMixin, ListView):
    model = Proposal
    template_name = 'proposals/list.html'
    context_object_name = 'proposals'
    paginate_by = 20


class ProposalDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Proposal
    template_name = 'proposals/detail.html'
    context_object_name = 'proposal'

class ProposalCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'proposals/form.html'
    success_url = '/proposals/'
    permission_action = 'create'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = ProposalLineFormSet(self.request.POST)
        else:
            context['lines'] = ProposalLineFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            self.object = form.save()
            lines.instance = self.object
            lines.save()
            
            # Apply CPQ rules
            from .services import ConfiguratorService
            ConfiguratorService.apply_auto_rules(self.object)
            
            messages.success(self.request, f"Proposal '{self.object.title}' created with CPQ rules applied.")
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs


class ProposalUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'proposals/form.html'
    success_url = '/proposals/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['lines'] = ProposalLineFormSet(self.request.POST, instance=self.object)
        else:
            context['lines'] = ProposalLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            form.save()
            lines.save()

            # Apply CPQ rules
            from .services import ConfiguratorService
            ConfiguratorService.apply_auto_rules(self.object)

            messages.success(self.request, f"Proposal '{self.object.title}' updated and CPQ rules applied.")
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs


class ProposalDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Proposal
    template_name = 'proposals/confirm_delete.html'
    success_url = '/proposals/'

    def delete(self, request, *args, **kwargs):
        proposal = self.get_object()
        messages.success(request, f"Proposal '{proposal.title}' deleted.")
        return super().delete(request, *args, **kwargs)


# === Email and PDF Views ===
class SendProposalEmailView(ObjectPermissionRequiredMixin, CreateView):
    model = ProposalEmail
    form_class = ProposalEmailForm
    template_name = 'proposals/send_email.html'
    success_url = '/proposals/'

    def form_valid(self, form):
        messages.success(self.request, f"Proposal email prepared for {form.instance.recipient_email}!")
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        proposal_id = self.kwargs['pk']
        recipient_email = request.POST.get('recipient_email')
        
        if not recipient_email:
            messages.error(request, "Recipient email is required.")
            return redirect('proposals:detail', pk=proposal_id)
        
        try:
            send_proposal_email(proposal_id, recipient_email, request.user)
            messages.success(request, f"Proposal email sent to {recipient_email}!")
        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")
        
        return redirect('proposals:detail', pk=proposal_id)


class GenerateProposalPDFView(ObjectPermissionRequiredMixin, CreateView):
    model = ProposalPDF
    form_class = ProposalPDFForm
    template_name = 'proposals/generate_pdf.html'
    
    def get_success_url(self):
        return f"/proposals/{self.kwargs['pk']}/"
    
    def form_valid(self, form):
        messages.success(self.request, "Proposal PDF generated successfully!")
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs
    
    def get(self, request, pk):
        try:
            pdf_record = generate_proposal_pdf(pk, request.user)
            return redirect('proposals:detail', pk=pk)
        except Exception as e:
            messages.error(request, f"Failed to generate PDF: {str(e)}")
            return redirect('proposals:detail', pk=pk)


# === Template Management Views ===
class ProposalTemplateListView(ObjectPermissionRequiredMixin, ListView):
    model = ProposalTemplate
    template_name = 'proposals/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20


class ProposalTemplateCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = ProposalTemplate
    form_class = ProposalTemplateForm
    template_name = 'proposals/template_form.html'
    success_url = '/proposals/templates/'

    def form_valid(self, form):
        messages.success(self.request, f"Template '{form.instance.email_template_name}' created!")
        return super().form_valid(form)


class ProposalTemplateUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = ProposalTemplate
    form_class = ProposalTemplateForm
    template_name = 'proposals/template_form.html'
    success_url = '/proposals/templates/'

    def form_valid(self, form):
        messages.success(self.request, f"Template '{form.instance.email_template_name}' updated!")
        return super().form_valid(form)


class ProposalTemplateDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = ProposalTemplate
    template_name = 'proposals/template_confirm_delete.html'
    success_url = '/proposals/templates/'

    def delete(self, request, *args, **kwargs):
        template = self.get_object()
        messages.success(request, f"Template '{template.email_template_name}' deleted.")
        return super().delete(request, *args, **kwargs)


# === Analytics and Events Views ===
class ProposalEventsView(ObjectPermissionRequiredMixin, ListView):
    model = ProposalEvent
    form_class = ProposalEventForm
    template_name = 'proposals/events.html'
    context_object_name = 'events'
    paginate_by = 50

    def get_queryset(self):
        user = self.request.user
        from core.object_permissions import ProposalObjectPolicy
        proposals = ProposalObjectPolicy.get_viewable_queryset(user, Proposal.objects.all())
        return ProposalEvent.objects.filter(proposal__in=proposals).select_related('proposal').order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's proposals
        from core.object_permissions import ProposalObjectPolicy
        proposals = ProposalObjectPolicy.get_viewable_queryset(user, Proposal.objects.all())
        
        # Event statistics
        event_stats = ProposalEvent.objects.filter(proposal__in=proposals).values('event_type').annotate(count=models.Count('event_type'))
        
        context.update({
            'event_stats': event_stats,
            'total_events': ProposalEvent.objects.filter(proposal__in=proposals).count()
        })
        return context


class ProposalAnalyticsView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'proposals/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's proposals
        from core.object_permissions import ProposalObjectPolicy
        proposals = ProposalObjectPolicy.get_viewable_queryset(user, Proposal.objects.all())
        
        # Get proposals with engagement scores and sort them in Python
        proposals_with_scores = []
        for proposal in proposals:
            # Only include proposals with engagement scores > 0
            if proposal.engagement_score > 0:
                proposals_with_scores.append(proposal)
        
        # Sort by engagement score in descending order
        top_proposals = sorted(proposals_with_scores, key=lambda p: p.engagement_score, reverse=True)[:10]
        
        # Status distribution
        status_distribution = proposals.values('status').annotate(count=models.Count('status'))
        
        # Email tracking stats
        total_emails = ProposalEmail.objects.filter(proposal__in=proposals).count()
        opened_emails = ProposalEmail.objects.filter(proposal__in=proposals, opened_count__gt=0).count()
        clicked_emails = ProposalEmail.objects.filter(proposal__in=proposals, clicked_count__gt=0).count()
        
        # Acceptance/rejection stats
        accepted_proposals = proposals.filter(status='accepted').count()
        rejected_proposals = proposals.filter(status='rejected').count()
        
        context.update({
            'top_proposals': top_proposals,
            'status_distribution': status_distribution,
            'total_emails': total_emails,
            'opened_emails': opened_emails,
            'clicked_emails': clicked_emails,
            'open_rate': round((opened_emails / total_emails * 100) if total_emails > 0 else 0, 1),
            'click_rate': round((clicked_emails / total_emails * 100) if total_emails > 0 else 0, 1),
            'accepted_proposals': accepted_proposals,
            'rejected_proposals': rejected_proposals,
            'acceptance_rate': round((accepted_proposals / proposals.count() * 100) if proposals.count() > 0 else 0, 1)
        })
        return context


# === Engagement Dashboard ===
class ProposalDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'proposals/proposal_dashboard.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's proposals
        from core.object_permissions import ProposalObjectPolicy
        proposals = ProposalObjectPolicy.get_viewable_queryset(user, Proposal.objects.all())
        
        # Engagement stats
        total_proposals = proposals.count()
        sent_proposals = proposals.filter(status='sent').count()
        viewed_proposals = proposals.filter(status='viewed').count()
        accepted_proposals = proposals.filter(status='accepted').count()
        rejected_proposals = proposals.filter(status='rejected').count()
        
        # Email stats
        email_open_rate = 0
        email_click_rate = 0
        if sent_proposals > 0:
            emails = ProposalEmail.objects.filter(proposal__in=proposals)
            opened_emails = emails.filter(opened_count__gt=0).count()
            clicked_emails = emails.filter(clicked_count__gt=0).count()
            email_open_rate = (opened_emails / emails.count() * 100) if emails.count() > 0 else 0
            email_click_rate = (clicked_emails / emails.count() * 100) if emails.count() > 0 else 0
        
        context.update({
            'total_proposals': total_proposals,
            'sent_proposals': sent_proposals,
            'viewed_proposals': viewed_proposals,
            'accepted_proposals': accepted_proposals,
            'rejected_proposals': rejected_proposals,
            'email_open_rate': round(email_open_rate, 1),
            'email_click_rate': round(email_click_rate, 1),
            'recent_proposals': proposals.order_by('-id')[:10]  # Fixed: using id instead of created_at
        })
        return context
    




class ProposalWithApprovalsForm(ProposalForm):
    class Meta(ProposalForm.Meta):
        fields = ProposalForm.Meta.fields + ['approval_template']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs and kwargs['instance']:
            # Limit approval template choices to active templates
            self.fields['approval_template'].queryset = ApprovalTemplate.objects.filter(is_active=True)





class ProposalApprovalsView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'proposals/approvals_dashboard.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's proposals
        from core.object_permissions import ProposalObjectPolicy
        proposals = ProposalObjectPolicy.get_viewable_queryset(user, Proposal.objects.all())
        
        # Get proposals needing approval
        proposals_needing_approval = []
        for proposal in proposals:
            # Get pending approvals for this proposal
            pending_approvals = proposal.approvals.filter(
                is_approved__isnull=True,
                approved_by=user
            )
            if pending_approvals.exists():
                proposals_needing_approval.append({
                    'proposal': proposal,
                    'approvals': pending_approvals
                })
        
        # Get recently approved proposals
        recently_approved = ProposalApproval.objects.filter(
            approved_by=user,
            is_approved=True,
            approved_at__isnull=False
        ).order_by('-approved_at')[:10]
        
        context.update({
            'proposals_needing_approval': proposals_needing_approval,
            'recently_approved': recently_approved,
            'pending_approvals_count': len(proposals_needing_approval),
        })
        return context

class ProposalApprovalDashboardView(ObjectPermissionRequiredMixin, DetailView):
    model = Proposal
    template_name = 'proposals/proposal_approval.html'
    context_object_name = 'proposal'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposal = self.get_object()
        
        # Get all approvals for this proposal
        context['approvals'] = proposal.approvals.select_related(
            'step', 'step__approvalstep', 'approved_by'
        ).all()
        
        # Get current user's approval permissions
        user = self.request.user
        user_steps = proposal.approval_template.steps.all() if proposal.approval_template else []
        context['user_can_approve'] = user_steps.filter(
            approvalstep__approved_by=user
        ).exists() if user_steps else False
        
        return context

class StartApprovalView(ObjectPermissionRequiredMixin, View):
    permission_action = 'approve'
    
    def post(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk)
        
        if not proposal.approval_template:
            messages.error(request, "Cannot start approval: No approval template assigned to this proposal.")
            return redirect('proposals:detail', pk=pk)
        
        # Check if any approvals already exist
        if proposal.approvals.exists():
            messages.warning(request, "Approval process has already started for this proposal.")
            return redirect('proposals:detail', pk=pk)
        
        # Create approval records based on the template
        for template_step in proposal.approval_template.approvaltemplatetemplates.all():
            ProposalApproval.objects.create(
                proposal=proposal,
                step=template_step.step,
                approved_by=template_step.step.approved_by,
                is_approved=None
            )
        
        messages.success(request, "Approval process started for this proposal.")
        return redirect('proposals:proposal_approval', pk=pk)

class SubmitApprovalView(ObjectPermissionRequiredMixin, View):
    permission_action = 'approve'
    
    def post(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk)
        
        step_id = request.POST.get('step_id')
        is_approved = request.POST.get('is_approved') == 'true'
        comments = request.POST.get('comments', '')
        
        try:
            approval = proposal.approvals.get(pk=step_id)
            
            # Check if user is authorized to approve this step
            if approval.approved_by != request.user:
                messages.error(request, "You are not authorized to approve this step.")
                return redirect('proposals:proposal_approval', pk=pk)
            
            # Check if this step has already been completed
            if approval.is_approved is not None:
                messages.warning(request, "This step has already been completed.")
                return redirect('proposals:proposal_approval', pk=pk)
            
            # Update the approval
            approval.is_approved = is_approved
            approval.comments = comments
            approval.approved_at = timezone.now()
            approval.save()
            
            # Check if all required steps are complete
            all_steps = proposal.approvals.filter(step__is_required=True)
            completed_steps = all_steps.filter(is_approved__isnull=False)
            
            if all_steps.count() == completed_steps.filter(is_approved=True).count():
                # All required steps are approved
                proposal.status = 'approved'
                proposal.save()
                messages.success(request, "All approvals completed. Proposal is now ready to send.")
            elif completed_steps.filter(is_approved=False).exists():
                # Any rejection stops the process
                proposal.status = 'rejected'
                proposal.save()
                messages.error(request, "Proposal has been rejected.")
            else:
                messages.info(request, "Your approval has been recorded.")
                
            return redirect('proposals:proposal_approval', pk=pk)
            
        except ProposalApproval.DoesNotExist:
            messages.error(request, "Approval step not found.")
            return redirect('proposals:proposal_approval', pk=pk)

class ManageApprovalTemplateView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'proposals/approval_template_manage.html'
    permission_action = 'manage_approval_templates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = ApprovalTemplate.objects.filter(is_active=True)
        context['steps'] = ApprovalStep.objects.all()
        return context

class ApprovalTemplateDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = ApprovalTemplate
    template_name = 'proposals/approval_template_detail.html'
    context_object_name = 'template'
    permission_action = 'read'

class ApprovalTemplateCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = ApprovalTemplate
    form_class = ApprovalTemplateForm
    template_name = 'proposals/approval_template_form.html'
    success_url = '/proposals/approval-templates/'
    permission_action = 'create'

    def form_valid(self, form):
        messages.success(self.request, f"Approval template '{form.instance.name}' created!")
        return super().form_valid(form)

class ApprovalTemplateUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = ApprovalTemplate
    form_class = ApprovalTemplateForm
    template_name = 'proposals/approval_template_form.html'
    success_url = '/proposals/approval-templates/'
    permission_action = 'update'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ApprovalTemplateForm(self.request.POST, instance=self.object)
        else:
            context['formset'] =ApprovalTemplateForm(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            form.save()
            formset.save()
            messages.success(self.request, f"Approval template '{form.instance.name}' updated!")
            return redirect('proposals:approval_template_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('proposals:approval_template_detail', args=[str(self.object.id)])

class ApprovalTemplateListView(ObjectPermissionRequiredMixin, ListView):
    model = ApprovalTemplate
    template_name = 'proposals/approval_template_list.html'
    context_object_name = 'templates'
    permission_action = 'read'
    paginate_by = 20

    def get_queryset(self):
        return ApprovalTemplate.objects.all().order_by('name')

class ProposalSetTemplateView(ObjectPermissionRequiredMixin, View):
    permission_action = 'update'
    
    def post(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk)
        template_id = request.POST.get('template_id')
        
        if template_id:
            try:
                template = ApprovalTemplate.objects.get(pk=template_id, is_active=True)
                proposal.approval_template = template
                proposal.status = 'under_review'  # Update status to reflect review process
                proposal.save()
                messages.success(request, f"Approval template '{template.name}' applied to proposal.")
            except ApprovalTemplate.DoesNotExist:
                messages.error(request, "Selected approval template does not exist or is not active.")
        else:
            messages.error(request, "No template selected.")
        
        return redirect('proposals:detail', pk=pk)