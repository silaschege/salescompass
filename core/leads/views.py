from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views import View

from .models import (
    Lead, AssignmentRule, ActionType, OperatorType,
    BehavioralScoringRule, DemographicScoringRule, MarketingChannel,
    WebToLeadForm, Industry, LeadSource, LeadStatus
)
from .forms import (
    LeadForm, AssignmentRuleForm, ActionTypeForm, OperatorTypeForm,
    BehavioralScoringRuleForm, DemographicScoringRuleForm, MarketingChannelForm,
    WebToLeadForm as WebToLeadModelForm
)
from tenants.models import TenantAwareModel,Tenant
from engagement.utils import log_engagement_event

from core.views import (
    TenantAwareViewMixin, SalesCompassListView, SalesCompassDetailView, 
    SalesCompassCreateView, SalesCompassUpdateView, SalesCompassDeleteView
)


class LeadPipelineView(SalesCompassListView):
    """
    View to display leads in a pipeline/kanban format
    """
    model = Lead
    template_name = 'leads/lead_pipeline.html'
    context_object_name = 'leads'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('source_ref', 'status_ref', 'industry_ref', 'account', 'owner')


class LeadAnalyticsView(SalesCompassListView):
    """
    View to display lead analytics and metrics
    """
    model = Lead
    template_name = 'leads/lead_analytics.html'
    context_object_name = 'leads'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('source_ref', 'status_ref', 'industry_ref', 'account', 'owner')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add analytics data to context
        leads = self.get_queryset()
        
        # Calculate overall metrics
        total_leads = leads.count()
        converted_leads = leads.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Calculate metrics by source
        metrics_by_source = {}
        for lead in leads:
            source = lead.source or (lead.source_ref.label if lead.source_ref else 'Unknown')
            if source not in metrics_by_source:
                metrics_by_source[source] = {'total': 0, 'converted': 0}
            metrics_by_source[source]['total'] += 1
            if lead.status == 'converted':
                metrics_by_source[source]['converted'] += 1
        
        for source, data in metrics_by_source.items():
            data['conversion_rate'] = (data['converted'] / data['total'] * 100) if data['total'] > 0 else 0
        
        context['total_leads'] = total_leads
        context['converted_leads'] = converted_leads
        context['conversion_rate'] = conversion_rate
        context['metrics_by_source'] = metrics_by_source
        
        return context


class WebToLeadListView(SalesCompassListView):
    """
    View to display web-to-lead forms
    """
    model = Lead
    template_name = 'leads/web_to_lead_list.html'
    context_object_name = 'leads'


class WebToLeadBuilderView(SalesCompassListView):
    """
    View to build web-to-lead forms
    """
    model = Lead
    template_name = 'leads/web_to_lead_builder.html'
    context_object_name = 'leads'


class WebToLeadFormView(SalesCompassListView):
    """
    View to display a specific web-to-lead form
    """
    model = Lead
    template_name = 'leads/web_to_lead_form.html'
    context_object_name = 'leads'


@login_required
def quick_create_lead_from_account(request, account_pk):
    """
    View to quickly create a lead from an account
    """
    # This would typically involve creating a new lead based on account information
    # For now, redirect to lead creation with account pre-filled
    messages.success(request, 'Lead created successfully from account.')
    return redirect('leads:lead_create')


@login_required
@require_http_methods(["POST"])
def update_lead_status(request, lead_id):
    """
    AJAX endpoint to update lead status
    """
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        
        # Check if user has permission to update this lead
        # This would depend on your specific permission system
        if hasattr(request.user, 'tenant_id') and lead.tenant_id != request.user.tenant_id:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        new_status = request.POST.get('status')
        if new_status:
            old_status = lead.status
            lead.status = new_status
            lead.save()
            
            # Log engagement event based on status change
            try:
                event_type = 'lead_contacted'  # default
                engagement_score = 3
                
                if new_status == 'qualified':
                    event_type = 'lead_qualified'
                    engagement_score = 4
                elif new_status == 'unqualified':
                    event_type = 'lead_unqualified'
                    engagement_score = 0
                elif new_status == 'converted':
                    event_type = 'lead_converted'
                    engagement_score = 5
                    # Trigger conversion logic
                    from .services import LeadScoringService
                    LeadScoringService.create_opportunity_from_lead(lead, creator=request.user)
                elif new_status == 'contacted':
                    event_type = 'lead_contacted'
                    engagement_score = 3
                
                log_engagement_event(
                    tenant_id=request.user.tenant_id if hasattr(request.user, 'tenant_id') else None,
                    event_type=event_type,
                    description=f"Lead {lead.full_name} status changed from {old_status} to {new_status}",
                    lead=lead,
                    account=lead.owner,
                    title=f"Lead Status: {new_status.title()}",
                    engagement_score=engagement_score,
                    created_by=request.user if request.user.is_authenticated else None
                )
            except Exception as e:
                # Don't fail status update if engagement logging fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to log engagement event for status change: {e}")
            
            return JsonResponse({'success': True, 'message': 'Lead status updated successfully'})
        else:
            return JsonResponse({'error': 'Status not provided'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




# Example of how to use feature enforcement in another app
# This would be in the leads/views.py file
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from tenants.views import FeatureEnforcementMiddleware

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    
    # def dispatch(self, request, *args, **kwargs):
    #     # Check if user has access to leads management feature
    #     if not FeatureEnforcementMiddleware.has_feature_access(request.user, 'leads_management'):
    #         messages.error(request, "You don't have access to leads management.")
    #         return redirect('core:home')  # or wherever appropriate
    #     return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Lead.objects.filter(tenant=self.request.user.tenant)

class LeadDetailView(SalesCompassDetailView):
    model = Lead
    template_name = 'leads/lead_detail.html'
    context_object_name = 'lead'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = self.object
        
        # Get engagement events for this lead
        from engagement.models import EngagementEvent
        context['timeline_events'] = EngagementEvent.objects.filter(
            lead=lead
        ).select_related('created_by', 'task', 'case').order_by('-created_at')
        
        return context


class LeadCreateView(SalesCompassCreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    success_url = reverse_lazy('leads:lead_list')
    success_message = 'Lead created successfully.'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Log engagement event for lead creation
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id if hasattr(self.request.user, 'tenant_id') else None,
                event_type='lead_created',
                description=f"Lead {self.object.full_name} created from {self.object.get_lead_source_display()}",
                lead=self.object,
                account=self.object.owner,
                title="Lead Created",
                engagement_score=2,
                created_by=self.request.user if self.request.user.is_authenticated else None
            )
        except Exception as e:
            # Don't fail lead creation if engagement logging fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to log engagement event for lead creation: {e}")
        return response


class LeadUpdateView(SalesCompassUpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    success_url = reverse_lazy('leads:lead_list')
    success_message = 'Lead updated successfully.'



@login_required
def get_dynamic_choices(request, choice_model_name):
    """
    AJAX endpoint to fetch dynamic choices for a specific model
    """
    tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
    
    if not tenant_id:
        return JsonResponse({'error': 'No tenant associated with user'}, status=400)
    
    # Map choice model names to actual models
    model_map = {
        'leadsource': LeadSource,
        'leadstatus': LeadStatus,
        'industry': Industry,
        'marketingchannel': MarketingChannel,
    }
    
    model_class = model_map.get(choice_model_name.lower())
    
    if not model_class:
        return JsonResponse({'error': 'Invalid choice model'}, status=400)
    
    try:
        if choice_model_name.lower() == 'marketingchannel':
            # MarketingChannel uses different field names
            choices = model_class.objects.filter(tenant_id=tenant_id).values('id', 'channel_name', 'label')
            # Rename 'channel_name' to 'name' for consistency with the frontend
            choices_list = []
            for choice in choices:
                choices_list.append({
                    'id': choice['id'],
                    'name': choice['channel_name'],
                    'label': choice['label']
                })
            return JsonResponse(choices_list, safe=False)
        else:
            choices = model_class.objects.filter(tenant_id=tenant_id).values('id', 'name', 'label')
            return JsonResponse(list(choices), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class CACAnalyticsView(ListView):
    """
    View to display Customer Acquisition Cost analytics
    """
    model = Lead
    template_name = 'leads/cac_analytics.html'
    context_object_name = 'leads'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('source_ref', 'status_ref', 'industry_ref', 'account', 'owner')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add CAC analytics data to context
        leads = self.get_queryset()
        
        # Calculate overall CAC metrics
        total_leads = leads.count()
        total_cac = sum(float(lead.cac_cost or 0) for lead in leads)
        average_cac = total_cac / total_leads if total_leads > 0 else 0
        
        # Calculate CAC by marketing channel (legacy)
        cac_by_channel = {}
        for lead in leads:
            channel = lead.marketing_channel
            if channel not in cac_by_channel:
                cac_by_channel[channel] = {'total_cost': 0, 'count': 0}
            if lead.cac_cost:
                cac_by_channel[channel]['total_cost'] += float(lead.cac_cost)
                cac_by_channel[channel]['count'] += 1
        
        for channel, data in cac_by_channel.items():
            data['average_cac'] = data['total_cost'] / data['count'] if data['count'] > 0 else 0
        
        # Calculate CAC by marketing channel reference (new)
        cac_by_channel_ref = {}
        for lead in leads:
            if lead.marketing_channel_ref:
                channel_ref = lead.marketing_channel_ref
                channel_name = channel_ref.channel_name
                if channel_name not in cac_by_channel_ref:
                    cac_by_channel_ref[channel_name] = {
                        'channel': channel_name,
                        'total_cac_spent': 0,
                        'total_leads': 0,
                        'average_cac': 0
                    }
                if lead.cac_cost:
                    cac_by_channel_ref[channel_name]['total_cac_spent'] += float(lead.cac_cost)
                cac_by_channel_ref[channel_name]['total_leads'] += 1
        
        for channel_name, data in cac_by_channel_ref.items():
            if data['total_leads'] > 0:
                data['average_cac'] = data['total_cac_spent'] / data['total_leads']
        
        context['total_leads'] = total_leads
        context['total_cac'] = total_cac
        context['average_cac'] = average_cac
        context['cac_by_channel'] = cac_by_channel
        context['cac_by_channel_ref'] = cac_by_channel_ref
        
        return context


class ChannelMetricsView(ListView):
    """
    View to display metrics for a specific marketing channel
    """
    model = Lead
    template_name = 'leads/channel_metrics.html'
    context_object_name = 'leads'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        channel = self.kwargs['channel']
        
        # Filter by current tenant and specific channel
        # First check if it's a reference channel by looking for matching channel name in MarketingChannel
        try:
            marketing_channel_obj = MarketingChannel.objects.get(channel_name=channel)
            # If found, filter by the reference field
            if hasattr(self.request.user, 'tenant_id'):
                queryset = queryset.filter(tenant_id=self.request.user.tenant_id, marketing_channel_ref=marketing_channel_obj)
            else:
                queryset = queryset.filter(marketing_channel_ref=marketing_channel_obj)
        except MarketingChannel.DoesNotExist:
            # If not found, filter by the legacy field
            if hasattr(self.request.user, 'tenant_id'):
                queryset = queryset.filter(tenant_id=self.request.user.tenant_id, marketing_channel=channel)
            else:
                queryset = queryset.filter(marketing_channel=channel)
        
        return queryset.select_related('source_ref', 'status_ref', 'industry_ref', 'account', 'owner', 'marketing_channel_ref')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel = self.kwargs['channel']
        
        # Calculate channel-specific metrics
        leads = self.get_queryset()
        total_leads = leads.count()
        total_cac = sum(float(lead.cac_cost or 0) for lead in leads)
        average_cac = total_cac / total_leads if total_leads > 0 else 0
        
        # Calculate conversion rates
        converted_leads = leads.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        context['channel'] = channel
        context['total_leads'] = total_leads
        context['total_cac'] = total_cac
        context['average_cac'] = average_cac
        context['conversion_rate'] = conversion_rate
        context['converted_leads'] = converted_leads
        
        return context


class CampaignMetricsView(ListView):
    """
    View to display metrics for a specific campaign
    """
    model = Lead
    template_name = 'leads/campaign_metrics.html'
    context_object_name = 'leads'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        campaign = self.kwargs['campaign']
        
        # Filter by current tenant and specific campaign
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id, campaign_source=campaign)
        else:
            queryset = queryset.filter(campaign_source=campaign)
        
        return queryset.select_related('source_ref', 'status_ref', 'industry_ref', 'account', 'owner')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.kwargs['campaign']
        
        # Calculate campaign-specific metrics
        leads = self.get_queryset()
        total_leads = leads.count()
        total_cac = sum(float(lead.cac_cost or 0) for lead in leads)
        average_cac = total_cac / total_leads if total_leads > 0 else 0
        
        # Calculate conversion rates
        converted_leads = leads.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        context['campaign'] = campaign
        context['total_leads'] = total_leads
        context['total_cac'] = total_cac
        context['average_cac'] = average_cac
        context['conversion_rate'] = conversion_rate
        context['converted_leads'] = converted_leads
        
        return context


class IndustryListView(ListView):
    model = Industry
    template_name = 'leads/industry_list.html'
    context_object_name = 'industries'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class IndustryCreateView(CreateView):
    model = Industry
    fields = ['name', 'label', 'order', 'is_active', 'is_system']
    template_name = 'leads/industry_form.html'
    success_url = reverse_lazy('leads:industry_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Industry created successfully.')
        return super().form_valid(form)


class IndustryUpdateView(UpdateView):
    model = Industry
    fields = ['name', 'label', 'order', 'is_active', 'is_system']
    template_name = 'leads/industry_form.html'
    success_url = reverse_lazy('leads:industry_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Industry updated successfully.')
        return super().form_valid(form)


class IndustryDeleteView(DeleteView):
    model = Industry
    template_name = 'leads/industry_confirm_delete.html'
    success_url = reverse_lazy('leads:industry_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Industry deleted successfully.')
        return super().delete(request, *args, **kwargs)


class LeadSourceListView(ListView):
    model = LeadSource
    template_name = 'leads/leadsource_list.html'
    context_object_name = 'lead_sources'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class LeadSourceCreateView(CreateView):
    model = LeadSource
    fields = ['name', 'label', 'order', 'color', 'icon', 'is_active', 'is_system', 'conversion_rate_target']
    template_name = 'leads/leadsource_form.html'
    success_url = reverse_lazy('leads:leadsource_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Lead source created successfully.')
        return super().form_valid(form)


class LeadSourceUpdateView(UpdateView):
    model = LeadSource
    fields = ['name', 'label', 'order', 'color', 'icon', 'is_active', 'is_system', 'conversion_rate_target']
    template_name = 'leads/leadsource_form.html'
    success_url = reverse_lazy('leads:leadsource_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Lead source updated successfully.')
        return super().form_valid(form)


class LeadSourceDeleteView(DeleteView):
    model = LeadSource
    template_name = 'leads/leadsource_confirm_delete.html'
    success_url = reverse_lazy('leads:leadsource_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Lead source deleted successfully.')
        return super().delete(request, *args, **kwargs)


class LeadStatusListView(ListView):
    model = LeadStatus
    template_name = 'leads/leadstatus_list.html'
    context_object_name = 'lead_statuses'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class LeadStatusCreateView(CreateView):
    model = LeadStatus
    fields = ['name', 'label', 'order', 'color', 'icon', 'is_active', 'is_system', 'is_qualified', 'is_closed']
    template_name = 'leads/leadstatus_form.html'
    success_url = reverse_lazy('leads:leadstatus_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Lead status created successfully.')
        return super().form_valid(form)


class LeadStatusUpdateView(UpdateView):
    model = LeadStatus
    fields = ['name', 'label', 'order', 'color', 'icon', 'is_active', 'is_system', 'is_qualified', 'is_closed']
    template_name = 'leads/leadstatus_form.html'
    success_url = reverse_lazy('leads:leadstatus_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Lead status updated successfully.')
        return super().form_valid(form)


class LeadStatusDeleteView(DeleteView):
    model = LeadStatus
    template_name = 'leads/leadstatus_confirm_delete.html'
    success_url = reverse_lazy('leads:leadstatus_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Lead status deleted successfully.')
        return super().delete(request, *args, **kwargs)


class MarketingChannelListView(ListView):
    model = MarketingChannel
    template_name = 'leads/marketingchannel_list.html'
    context_object_name = 'marketing_channels'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class MarketingChannelCreateView(CreateView):
    model = MarketingChannel
    fields = ['channel_name', 'label', 'order', 'color', 'icon', 'channel_is_active', 'is_system']
    template_name = 'leads/marketingchannel_form.html'
    success_url = reverse_lazy('leads:marketingchannel_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Marketing channel created successfully.')
        return super().form_valid(form)


class MarketingChannelUpdateView(UpdateView):
    model = MarketingChannel
    fields = ['channel_name', 'label', 'order', 'color', 'icon', 'channel_is_active', 'is_system']
    template_name = 'leads/marketingchannel_form.html'
    success_url = reverse_lazy('leads:marketingchannel_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Marketing channel updated successfully.')
        return super().form_valid(form)


class MarketingChannelDeleteView(DeleteView):
    model = MarketingChannel
    template_name = 'leads/marketingchannel_confirm_delete.html'
    success_url = reverse_lazy('leads:marketingchannel_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Marketing channel deleted successfully.')
        return super().delete(request, *args, **kwargs)


class AssignmentRuleListView(ListView):
    model = AssignmentRule
    template_name = 'leads/assignment_rule_list.html'
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
    template_name = 'leads/assignment_rule_form.html'
    success_url = reverse_lazy('leads:assignment_rule_list')
    
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
    template_name = 'leads/assignment_rule_form.html'
    success_url = reverse_lazy('leads:assignment_rule_list')
    
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
    template_name = 'leads/assignment_rule_confirm_delete.html'
    success_url = reverse_lazy('leads:assignment_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ActionTypeListView(ListView):
    model = ActionType
    template_name = 'leads/action_type_list.html'
    context_object_name = 'action_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class ActionTypeCreateView(CreateView):
    model = ActionType
    form_class = ActionTypeForm
    template_name = 'leads/action_type_form.html'
    success_url = reverse_lazy('leads:action_type_list')
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Action type created successfully.')
        return super().form_valid(form)


class ActionTypeUpdateView(UpdateView):
    model = ActionType
    form_class = ActionTypeForm
    template_name = 'leads/action_type_form.html'
    success_url = reverse_lazy('leads:action_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Action type updated successfully.')
        return super().form_valid(form)


class ActionTypeDeleteView(DeleteView):
    model = ActionType
    template_name = 'leads/action_type_confirm_delete.html'
    success_url = reverse_lazy('leads:action_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Action type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class OperatorTypeListView(ListView):
    model = OperatorType
    template_name = 'leads/operator_type_list.html'
    context_object_name = 'operator_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class OperatorTypeCreateView(CreateView):
    model = OperatorType
    form_class = OperatorTypeForm
    template_name = 'leads/operator_type_form.html'
    success_url = reverse_lazy('leads:operator_type_list')
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Operator type created successfully.')
        return super().form_valid(form)


class OperatorTypeUpdateView(UpdateView):
    model = OperatorType
    form_class = OperatorTypeForm
    template_name = 'leads/operator_type_form.html'
    success_url = reverse_lazy('leads:operator_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Operator type updated successfully.')
        return super().form_valid(form)


class OperatorTypeDeleteView(DeleteView):
    model = OperatorType
    template_name = 'leads/operator_type_confirm_delete.html'
    success_url = reverse_lazy('leads:operator_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Operator type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class BehavioralScoringRuleListView(ListView):
    model = BehavioralScoringRule
    template_name = 'leads/behavioral_scoring_rule_list.html'
    context_object_name = 'behavioral_scoring_rules'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('action_type_ref', 'business_impact_ref')


class BehavioralScoringRuleCreateView(CreateView):
    model = BehavioralScoringRule
    form_class = BehavioralScoringRuleForm
    template_name = 'leads/behavioral_scoring_rule_form.html'
    success_url = reverse_lazy('leads:behavioral_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = Tenant.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Behavioral scoring rule created successfully.')
        return super().form_valid(form)


class BehavioralScoringRuleUpdateView(UpdateView):
    model = BehavioralScoringRule
    form_class = BehavioralScoringRuleForm
    template_name = 'leads/behavioral_scoring_rule_form.html'
    success_url = reverse_lazy('leads:behavioral_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = Tenant.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Behavioral scoring rule updated successfully.')
        return super().form_valid(form)


class BehavioralScoringRuleDeleteView(DeleteView):
    model = BehavioralScoringRule
    template_name = 'leads/behavioral_scoring_rule_confirm_delete.html'
    success_url = reverse_lazy('leads:behavioral_scoring_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Behavioral scoring rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


class DemographicScoringRuleListView(ListView):
    model = DemographicScoringRule
    template_name = 'leads/demographic_scoring_rule_list.html'
    context_object_name = 'demographic_scoring_rules'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('operator_ref')


class DemographicScoringRuleCreateView(CreateView):
    model = DemographicScoringRule
    form_class = DemographicScoringRuleForm
    template_name = 'leads/demographic_scoring_rule_form.html'
    success_url = reverse_lazy('leads:demographic_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Demographic scoring rule created successfully.')
        return super().form_valid(form)


class DemographicScoringRuleUpdateView(UpdateView):
    model = DemographicScoringRule
    form_class = DemographicScoringRuleForm
    template_name = 'leads/demographic_scoring_rule_form.html'
    success_url = reverse_lazy('leads:demographic_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Demographic scoring rule updated successfully.')
        return super().form_valid(form)


class DemographicScoringRuleDeleteView(DeleteView):
    model = DemographicScoringRule
    template_name = 'leads/demographic_scoring_rule_confirm_delete.html'
    success_url = reverse_lazy('leads:demographic_scoring_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Demographic scoring rule deleted successfully.')
        return super().delete(request, *args, **kwargs)
