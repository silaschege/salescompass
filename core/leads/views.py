import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from datetime import date, timedelta
from core.permissions import ObjectPermissionRequiredMixin
from .models import Lead, WebToLeadForm, LeadSourceAnalytics, LeadStatus
from .forms import LeadForm, WebToLeadFormBuilder, WebToLeadSubmissionForm
from core.models import User, TenantModel
from accounts.models import Account
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from django.http import HttpResponse
from .utils import calculate_lead_score, create_lead_source_analytics, process_web_to_lead_submission


class LeadListView(ObjectPermissionRequiredMixin, ListView):
    """
    List all leads with filtering and search capabilities.
    """
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 25
    permission_action = 'view'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add filtering logic here
        return queryset.select_related('account', 'owner').order_by('-created_at')


class LeadDetailView(ObjectPermissionRequiredMixin, DetailView):
    """
    Display detailed lead information.
    """
    model = Lead
    template_name = 'leads/lead_detail.html'
    context_object_name = 'lead'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = self.object
        
        # Get scoring recommendations
        from .services import LeadScoringService
        context['scoring_recommendations'] = LeadScoringService.get_scoring_recommendations(lead)
        
        # Get related tasks
        from tasks.models import Task
        context['lead_tasks'] = Task.objects.filter(
            related_lead=lead,
            tenant_id=lead.tenant_id
        ).order_by('due_date')
        
        # Get all active statuses ordered by sequence
        context['statuses'] = LeadStatus.objects.filter(
            tenant_id=self.request.user.tenant_id,
            is_active=True
        ).order_by('order')
        
        return context


class LeadCreateView(ObjectPermissionRequiredMixin, CreateView):
    """
    Create a new lead (general purpose).
    """
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    success_url = reverse_lazy('leads:leads_list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
 
    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.tenant_id = getattr(self.request.user, 'tenant_id', None)
        messages.success(self.request, f"Lead '{form.instance.full_name}' created successfully!")
        return super().form_valid(form)

class LeadUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    """
    Update an existing lead.
    """
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    success_url = reverse_lazy('leads:list')
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Lead '{form.instance.full_name}' updated successfully!")
        return super().form_valid(form)


class LeadDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    """
    Delete a lead.
    """
    model = Lead
    template_name = 'leads/lead_confirm_delete.html'
    success_url = reverse_lazy('leads:list')
    permission_action = 'delete'

    def delete(self, request, *args, **kwargs):
        lead = self.get_object()
        messages.success(request, f"Lead '{lead.full_name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)

def quick_create_lead_from_account(request, account_pk):
    """Quick create lead with minimal fields."""
    account = get_object_or_404(Account, pk=account_pk)
    
    if request.method == 'POST':
        # Get contact ID if provided
        contact_id = request.POST.get('contact_id')
        
        if contact_id:
            # Get contact details
            try:
                from accounts.models import Contact
                contact = Contact.objects.get(id=contact_id, account=account)
                first_name = contact.first_name
                last_name = contact.last_name
                email = contact.email
                phone = contact.phone
                job_title = contact.role
            except Contact.DoesNotExist:
                # Fallback to POST data if contact not found
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                email = request.POST.get('email', '')
        else:
            # Use POST data for new contact
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
        
        # Create lead
        lead = Lead.objects.create(
            first_name=first_name,
            last_name=last_name,
            company=account.name,
            email=email,
            account=account,
            phone =phone,
            industry=account.industry,
            job_title=job_title,
            lead_source=request.POST.get('lead_source', 'upsell'),
            status='new',
            owner=request.user,
            tenant_id=account.tenant_id

        )
        
        messages.success(request, "Quick lead created successfully!")
        return redirect('accounts:detail', pk=account_pk)
    
    return redirect('accounts:detail', pk=account_pk)




# === Lead Analytics View ===
class LeadAnalyticsView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'leads/analytics.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        from datetime import timedelta
        
        # Last 30 days analytics
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        analytics = LeadSourceAnalytics.objects.filter(
            date__gte=thirty_days_ago,
            tenant_id=self.request.user.tenant_id
        ).order_by('date')
        
        # Aggregate by source
        source_data = {}
        for record in analytics:
            if record.source not in source_data:
                source_data[record.source] = {
                    'dates': [], 'leads': [], 'conversions': [], 'scores': []
                }
            source_data[record.source]['dates'].append(record.date.isoformat())
            source_data[record.source]['leads'].append(record.lead_count)
            source_data[record.source]['conversions'].append(record.converted_count)
            source_data[record.source]['scores'].append(record.avg_lead_score)
        
        context['source_data_json'] = source_data
        context['total_leads'] = Lead.objects.filter(tenant_id=self.request.user.tenant_id).count()
        context['qualified_leads'] = Lead.objects.filter(
            tenant_id=self.request.user.tenant_id,
            status__in=['qualified', 'converted']
        ).count()
        context['conversion_rate'] = (
            (context['qualified_leads'] / context['total_leads'] * 100) if context['total_leads'] > 0 else 0
        )
        return context


# === Web-to-Lead Views ===
class WebToLeadBuilderView(ObjectPermissionRequiredMixin, CreateView):
    model = WebToLeadForm
    form_class = WebToLeadFormBuilder
    template_name = 'leads/web_to_lead_builder.html'
    success_url = '/leads/web-to-lead/'
    permission_action = 'write'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs


class WebToLeadFormView(FormView):
    template_name = 'leads/web_to_lead_form.html'
    success_url = '/thank-you/'  # Will be overridden

    def get_form(self, form_class=None):
        form_id = self.kwargs['form_id']
        form_config = get_object_or_404(WebToLeadForm, id=form_id, is_active=True)
        return WebToLeadSubmissionForm(form_config=form_config, **self.get_form_kwargs())

    def form_valid(self, form):
        form_id = self.kwargs['form_id']
        form_config = get_object_or_404(WebToLeadForm, id=form_id, is_active=True)
        
        # Process submission
        lead = process_web_to_lead_submission(form_config, form.cleaned_data)
        
        # Redirect to success URL
        self.success_url = form_config.success_redirect_url
        return super().form_valid(form)


# === Web-to-Lead List View ===
class WebToLeadListView(ObjectPermissionRequiredMixin, ListView):
    model = WebToLeadForm
    template_name = 'leads/web_to_lead_list.html'
    context_object_name = 'forms'
    permission_action = 'read'


# === Lead Pipeline Kanban View ===
class LeadPipelineView(ObjectPermissionRequiredMixin, TemplateView):
    """
    Kanban board view for lead pipeline.
    Shows leads organized by status with drag-and-drop functionality.
    """
    template_name = 'leads/pipeline_kanban.html'
    permission_action = 'view'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        
        # Get all statuses for this tenant
        statuses = LeadStatus.objects.filter(
            tenant_id=tenant_id,
            is_active=True
        ).order_by('order')
        
        # Get all leads for this tenant
        leads = Lead.objects.filter(
            tenant_id=tenant_id
        ).select_related('account', 'owner', 'status_ref')
        
        # Calculate overall stats
        total_count = leads.count()
        qualified_count = leads.filter(
            Q(status_ref__is_qualified=True) | Q(status='qualified')
        ).count()
        
        # New leads this week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        new_this_week = leads.filter(created_at__gte=week_start).count()
        
        # Organize leads by status
        status_data = []
        
        for status in statuses:
            # Filter leads by this status (using both old and new status fields)
            status_leads = leads.filter(
                Q(status_ref=status) | Q(status=status.name)
            )
            
            # Prepare lead data
            lead_list = []
            for lead in status_leads:
                lead_list.append({
                    'id': lead.id,
                    'name': lead.full_name,
                    'company': lead.company,
                    'source': lead.lead_source if hasattr(lead, 'lead_source') else None,
                    'score': lead.lead_score if hasattr(lead, 'lead_score') else 0
                })
            
            status_data.append({
                'id': status.id,
                'label': status.label,
                'name': status.name,
                'order': status.order,
                'color': status.color,
                'is_qualified': status.is_qualified,
                'is_closed': status.is_closed,
                'leads': lead_list,
                'lead_count': len(lead_list)
            })
        
        context['statuses'] = status_data
        context['total_count'] = total_count
        context['qualified_count'] = qualified_count
        context['new_this_week'] = new_this_week
        
        return context


# === AJAX Endpoint for Lead Status Updates ===
@require_POST
def update_lead_status(request, lead_id):
    """
    AJAX endpoint to update a lead's status.
    Updates the status and optionally the lead score.
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        new_status_id = data.get('status_id')
        
        if not new_status_id:
            return JsonResponse({
                'success': False,
                'message': 'Status ID is required'
            }, status=400)
        
        # Get the lead
        lead = Lead.objects.get(
            id=lead_id,
            tenant_id=request.user.tenant_id
        )
        
        # Get the new status
        new_status = LeadStatus.objects.get(
            id=new_status_id,
            tenant_id=request.user.tenant_id
        )
        
        # Update the lead
        old_status = lead.status_ref if lead.status_ref else None
        lead.status_ref = new_status
        lead.status = new_status.name  # Update legacy field too
        
        # Recalculate score if status is qualified
        if new_status.is_qualified and hasattr(lead, 'calculate_initial_score'):
            old_score = lead.lead_score
            lead.lead_score = min(lead.lead_score + 20, 100)  # Boost score for qualification
            new_score = lead.lead_score
        else:
            new_score = lead.lead_score if hasattr(lead, 'lead_score') else 0
        
        lead.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Moved to {new_status.label}',
            'old_status': old_status.name if old_status else None,
            'new_status': new_status.name,
            'new_score': new_score
        })
        
    except Lead.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Lead not found'
        }, status=404)
    
    except LeadStatus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Status not found'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)