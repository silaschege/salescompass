from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from core.permissions import ObjectPermissionRequiredMixin
from .models import Proposal, ProposalEmail, ProposalPDF
from .forms import ProposalForm
from .utils import send_proposal_email, generate_proposal_pdf, track_email_open, track_link_click

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

    def form_valid(self, form):
        messages.success(self.request, f"Proposal '{form.instance.title}' created!")
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

class ProposalUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'proposals/form.html'
    success_url = '/proposals/'
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
    fields = []
    template_name = 'proposals/send_email.html'
    success_url = '/proposals/'

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


class GenerateProposalPDFView(ObjectPermissionRequiredMixin, TemplateView):
    def get(self, request, pk):
        try:
            pdf_record = generate_proposal_pdf(pk, request.user)
            return redirect('proposals:detail', pk=pk)
        except Exception as e:
            messages.error(request, f"Failed to generate PDF: {str(e)}")
            return redirect('proposals:detail', pk=pk)


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


# === Engagement Dashboard ===
class EngagementDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'proposals/engagement_dashboard.html'
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
            'email_open_rate': round(email_open_rate, 1),
            'email_click_rate': round(email_click_rate, 1),
            'recent_proposals': proposals.order_by('-created_at')[:10]
        })
        return context