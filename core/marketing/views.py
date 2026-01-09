from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.urls import reverse_lazy
from django.db.models import Avg, Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
import logging

from .models import (Campaign, EmailTemplate, LandingPageBlock, MessageTemplate, EmailCampaign, 
                     CampaignStatus, EmailProvider, BlockType, EmailCategory, MessageType, 
                     MessageCategory, EmailIntegration, ABTest, ABTestVariant, ABAutomatedTest,
                     Segment, SegmentMember, NurtureCampaign, NurtureStep, NurtureCampaignEnrollment,
                     DripCampaign, DripStep, DripEnrollment)
# Add Attribution model import
from .models_attribution import CampaignAttribution

from .forms import (CampaignForm, EmailTemplateForm, LandingPageBlockForm, MessageTemplateForm, 
                   EmailCampaignForm, CampaignStatusForm, EmailProviderForm, BlockTypeForm, 
                   EmailCategoryForm, MessageTypeForm, MessageCategoryForm, EmailIntegrationForm,
                   ABTestForm, ABTestVariantForm, ABAutomatedTestForm, ABTestVariantCreateFormSet,
                   ABTestVariantUpdateFormSet)
from tenants.models import Tenant as TenantModel
from core.models import User
from leads.models import Lead
from opportunities.models import Opportunity

# Import engagement tracking
from engagement.utils import log_engagement_event

logger = logging.getLogger(__name__)


class CampaignStatusListView(ListView):
    model = CampaignStatus
    template_name = 'marketing/campaign_status_list.html'
    context_object_name = 'campaign_statuses'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class CampaignStatusCreateView(CreateView):
    model = CampaignStatus
    form_class = CampaignStatusForm
    template_name = 'marketing/campaign_status_form.html'
    success_url = reverse_lazy('marketing:campaign_status_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Campaign status created successfully.')
        return super().form_valid(form)


class CampaignStatusUpdateView(UpdateView):
    model = CampaignStatus
    form_class = CampaignStatusForm
    template_name = 'marketing/campaign_status_form.html'
    success_url = reverse_lazy('marketing:campaign_status_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Campaign status updated successfully.')
        return super().form_valid(form)


class CampaignStatusDeleteView(DeleteView):
    model = CampaignStatus
    template_name = 'marketing/campaign_status_confirm_delete.html'
    success_url = reverse_lazy('marketing:campaign_status_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Campaign status deleted successfully.')
        return super().delete(request, *args, **kwargs)


class EmailProviderListView(ListView):
    model = EmailProvider
    template_name = 'marketing/email_provider_list.html'
    context_object_name = 'email_providers'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class EmailProviderCreateView(CreateView):
    model = EmailProvider
    form_class = EmailProviderForm
    template_name = 'marketing/email_provider_form.html'
    success_url = reverse_lazy('marketing:email_provider_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Email provider created successfully.')
        return super().form_valid(form)


class EmailProviderUpdateView(UpdateView):
    model = EmailProvider
    form_class = EmailProviderForm
    template_name = 'marketing/email_provider_form.html'
    success_url = reverse_lazy('marketing:email_provider_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Email provider updated successfully.')
        return super().form_valid(form)


class EmailProviderDeleteView(DeleteView):
    model = EmailProvider
    template_name = 'marketing/email_provider_confirm_delete.html'
    success_url = reverse_lazy('marketing:email_provider_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email provider deleted successfully.')
        return super().delete(request, *args, **kwargs)


class BlockTypeListView(ListView):
    model = BlockType
    template_name = 'marketing/block_type_list.html'
    context_object_name = 'block_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class BlockTypeCreateView(CreateView):
    model = BlockType
    form_class = BlockTypeForm
    template_name = 'marketing/block_type_form.html'
    success_url = reverse_lazy('marketing:block_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Block type created successfully.')
        return super().form_valid(form)


class BlockTypeUpdateView(UpdateView):
    model = BlockType
    form_class = BlockTypeForm
    template_name = 'marketing/block_type_form.html'
    success_url = reverse_lazy('marketing:block_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Block type updated successfully.')
        return super().form_valid(form)


class BlockTypeDeleteView(DeleteView):
    model = BlockType
    template_name = 'marketing/block_type_confirm_delete.html'
    success_url = reverse_lazy('marketing:block_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Block type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class EmailCategoryListView(ListView):
    model = EmailCategory
    template_name = 'marketing/email_category_list.html'
    context_object_name = 'email_categories'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class EmailCategoryCreateView(CreateView):
    model = EmailCategory
    form_class = EmailCategoryForm
    template_name = 'marketing/email_category_form.html'
    success_url = reverse_lazy('marketing:email_category_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Email category created successfully.')
        return super().form_valid(form)


class EmailCategoryUpdateView(UpdateView):
    model = EmailCategory
    form_class = EmailCategoryForm
    template_name = 'marketing/email_category_form.html'
    success_url = reverse_lazy('marketing:email_category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Email category updated successfully.')
        return super().form_valid(form)


class EmailCategoryDeleteView(DeleteView):
    model = EmailCategory
    template_name = 'marketing/email_category_confirm_delete.html'
    success_url = reverse_lazy('marketing:email_category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email category deleted successfully.')
        return super().delete(request, *args, **kwargs)


class MessageTypeListView(ListView):
    model = MessageType
    template_name = 'marketing/message_type_list.html'
    context_object_name = 'message_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class MessageTypeCreateView(CreateView):
    model = MessageType
    form_class = MessageTypeForm
    template_name = 'marketing/message_type_form.html'
    success_url = reverse_lazy('marketing:message_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Message type created successfully.')
        return super().form_valid(form)


class MessageTypeUpdateView(UpdateView):
    model = MessageType
    form_class = MessageTypeForm
    template_name = 'marketing/message_type_form.html'
    success_url = reverse_lazy('marketing:message_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Message type updated successfully.')
        return super().form_valid(form)


class MessageTypeDeleteView(DeleteView):
    model = MessageType
    template_name = 'marketing/message_type_confirm_delete.html'
    success_url = reverse_lazy('marketing:message_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Message type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class MessageCategoryListView(ListView):
    model = MessageCategory
    template_name = 'marketing/message_category_list.html'
    context_object_name = 'message_categories'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class MessageCategoryCreateView(CreateView):
    model = MessageCategory
    form_class = MessageCategoryForm
    template_name = 'marketing/message_category_form.html'
    success_url = reverse_lazy('marketing:message_category_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Message category created successfully.')
        return super().form_valid(form)


class MessageCategoryUpdateView(UpdateView):
    model = MessageCategory
    form_class = MessageCategoryForm
    template_name = 'marketing/message_category_form.html'
    success_url = reverse_lazy('marketing:message_category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Message category updated successfully.')
        return super().form_valid(form)


class MessageCategoryDeleteView(DeleteView):
    model = MessageCategory
    template_name = 'marketing/message_category_confirm_delete.html'
    success_url = reverse_lazy('marketing:message_category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Message category deleted successfully.')
        return super().delete(request, *args, **kwargs)


class CampaignListView(ListView):
    model = Campaign
    template_name = 'marketing/campaign_list.html'
    context_object_name = 'campaigns'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('status_ref')


class CampaignCreateView(CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'marketing/campaign_form.html'
    success_url = reverse_lazy('marketing:campaign_list')
    
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
        
        response = super().form_valid(form)
        
        # Log engagement event for campaign created
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='campaign_created',
                description=f"Marketing campaign created: {self.object.campaign_name}",
                title="Campaign Created",
                metadata={
                    'campaign_id': self.object.id,
                    'campaign_name': self.object.campaign_name,
                    'status': self.object.status,
                    'budget': float(self.object.budget) if self.object.budget else 0
                },
                engagement_score=3,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        messages.success(self.request, 'Campaign created successfully.')
        return response


class CampaignUpdateView(UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'marketing/campaign_form.html'
    success_url = reverse_lazy('marketing:campaign_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Log engagement event for campaign updated
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='campaign_updated',
                description=f"Marketing campaign updated: {self.object.campaign_name}",
                title="Campaign Updated",
                metadata={
                    'campaign_id': self.object.id,
                    'campaign_name': self.object.campaign_name,
                    'status': self.object.status
                },
                engagement_score=2,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        messages.success(self.request, 'Campaign updated successfully.')
        return response


class CampaignDeleteView(DeleteView):
    model = Campaign
    template_name = 'marketing/campaign_confirm_delete.html'
    success_url = reverse_lazy('marketing:campaign_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Campaign deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def clone_campaign(request, pk):
    """
    View to clone an existing marketing campaign.
    """
    original_campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        # Create a copy with '(Clone)' suffix
        cloned_campaign = Campaign()
        cloned_campaign.campaign_name = f"{original_campaign.campaign_name} (Clone)"
        cloned_campaign.campaign_description = original_campaign.campaign_description
        cloned_campaign.status = 'draft'
        cloned_campaign.status_ref = original_campaign.status_ref
        cloned_campaign.start_date = original_campaign.start_date
        cloned_campaign.end_date = original_campaign.end_date
        cloned_campaign.budget = original_campaign.budget
        cloned_campaign.actual_cost = original_campaign.actual_cost
        cloned_campaign.target_audience_size = original_campaign.target_audience_size
        cloned_campaign.actual_reach = original_campaign.actual_reach
        cloned_campaign.owner = original_campaign.owner
        cloned_campaign.campaign_is_active = False # Deactivate clone by default
        cloned_campaign.tenant_id = request.user.tenant_id
        cloned_campaign.save()
        
        messages.success(request, f"Campaign '{original_campaign.campaign_name}' cloned successfully.")
        return redirect('marketing:campaign_update', pk=cloned_campaign.pk)
    
    return render(request, 'marketing/campaign_confirm_clone.html', {'campaign': original_campaign})


class EmailTemplateListView(ListView):
    model = EmailTemplate
    template_name = 'marketing/email_template_list.html'
    context_object_name = 'email_templates'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('category_ref')


class EmailTemplateCreateView(CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'marketing/email_template_form.html'
    success_url = reverse_lazy('marketing:email_template_list')
    
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
        messages.success(self.request, 'Email template created successfully.')
        return super().form_valid(form)


class EmailTemplateUpdateView(UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'marketing/email_template_form.html'
    success_url = reverse_lazy('marketing:email_template_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Email template updated successfully.')
        return super().form_valid(form)


class EmailTemplateDeleteView(DeleteView):
    model = EmailTemplate
    template_name = 'marketing/email_template_confirm_delete.html'
    success_url = reverse_lazy('marketing:email_template_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email template deleted successfully.')
        return super().delete(request, *args, **kwargs)


class LandingPageBlockListView(ListView):
    model = LandingPageBlock
    template_name = 'marketing/landing_page_block_list.html'
    context_object_name = 'landing_page_blocks'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('block_type_ref', 'landing_page')


class LandingPageBlockCreateView(CreateView):
    model = LandingPageBlock
    form_class = LandingPageBlockForm
    template_name = 'marketing/landing_page_block_form.html'
    success_url = reverse_lazy('marketing:landing_page_block_list')
    
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
        messages.success(self.request, 'Landing page block created successfully.')
        return super().form_valid(form)


class LandingPageBlockUpdateView(UpdateView):
    model = LandingPageBlock
    form_class = LandingPageBlockForm
    template_name = 'marketing/landing_page_block_form.html'
    success_url = reverse_lazy('marketing:landing_page_block_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Landing page block updated successfully.')
        return super().form_valid(form)


class LandingPageBlockDeleteView(DeleteView):
    model = LandingPageBlock
    template_name = 'marketing/landing_page_block_confirm_delete.html'
    success_url = reverse_lazy('marketing:landing_page_block_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Landing page block deleted successfully.')
        return super().delete(request, *args, **kwargs)


class MessageTemplateListView(ListView):
    model = MessageTemplate
    template_name = 'marketing/message_template_list.html'
    context_object_name = 'message_templates'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('message_type_ref', 'category_ref')


class MessageTemplateCreateView(CreateView):
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = 'marketing/message_template_form.html'
    success_url = reverse_lazy('marketing:message_template_list')
    
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
        messages.success(self.request, 'Message template created successfully.')
        return super().form_valid(form)


class MessageTemplateUpdateView(UpdateView):
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = 'marketing/message_template_form.html'
    success_url = reverse_lazy('marketing:message_template_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Message template updated successfully.')
        return super().form_valid(form)


class MessageTemplateDeleteView(DeleteView):
    model = MessageTemplate
    template_name = 'marketing/message_template_confirm_delete.html'
    success_url = reverse_lazy('marketing:message_template_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Message template deleted successfully.')
        return super().delete(request, *args, **kwargs)


class EmailCampaignListView(ListView):
    model = EmailCampaign
    template_name = 'marketing/email_campaign_list.html'
    context_object_name = 'email_campaigns'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('campaign', 'email_provider_ref')


class EmailCampaignCreateView(CreateView):
    model = EmailCampaign
    form_class = EmailCampaignForm
    template_name = 'marketing/email_campaign_form.html'
    success_url = reverse_lazy('marketing:email_campaign_list')
    
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
        
        response = super().form_valid(form)
        
        # Log engagement event for email campaign created
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='email_campaign_created',
                description=f"Email campaign created: {self.object.subject if hasattr(self.object, 'subject') else 'New Campaign'}",
                title="Email Campaign Created",
                metadata={
                    'email_campaign_id': self.object.id,
                    'campaign_id': self.object.campaign_id if hasattr(self.object, 'campaign_id') else None,
                    'subject': getattr(self.object, 'subject', 'N/A')
                },
                engagement_score=3,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        messages.success(self.request, 'Email campaign created successfully.')
        return response


class EmailCampaignUpdateView(UpdateView):
    model = EmailCampaign
    form_class = EmailCampaignForm
    template_name = 'marketing/email_campaign_form.html'
    success_url = reverse_lazy('marketing:email_campaign_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Email campaign updated successfully.')
        return super().form_valid(form)


class EmailCampaignDeleteView(DeleteView):
    model = EmailCampaign
    template_name = 'marketing/email_campaign_confirm_delete.html'
    success_url = reverse_lazy('marketing:email_campaign_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email campaign deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def cac_analytics(request):
    """
    Display the Customer Acquisition Cost (CAC) analytics dashboard with key metrics.
    """
    # Calculate overall CAC metrics
    campaigns = Campaign.objects.all()
    
    # Calculate total marketing spend using the method we added to the Campaign model
    total_spend = sum([campaign.actual_cost or 0 for campaign in campaigns])
    
    # Get new customers acquired (converted leads)
    new_customers_count = Lead.objects.filter(status='converted').count()
    
    # Calculate average CAC
    if new_customers_count > 0:
        avg_cac = total_spend / new_customers_count
    else:
        avg_cac = 0
    
    # Calculate conversion rate
    total_leads = Lead.objects.count()
    conversion_rate = (new_customers_count / total_leads * 100) if total_leads > 0 else 0
    
    # Get CAC by channel using the method we added to the Campaign model
    cac_by_channel = {}
    # This would use the get_cac_by_channel method from the Campaign model
    # For now, using a simplified approach
    from leads.models import MarketingChannel
    channels = MarketingChannel.objects.all()
    cac_by_channel_labels = []
    cac_by_channel_data = []
    
    for channel in channels:
        leads_for_channel = Lead.objects.filter(marketing_channel_ref=channel)
        total_spend_channel = sum([lead.cac_cost or 0 for lead in leads_for_channel])
        converted_leads_count = leads_for_channel.filter(status='converted').count()
        
        if converted_leads_count > 0:
            cac = total_spend_channel / converted_leads_count
        else:
            cac = 0
            
        cac_by_channel[channel.label] = {
            'cac': cac,
            'total_spend': total_spend_channel,
            'converted_leads': converted_leads_count,
            'total_leads': leads_for_channel.count(),
            'conversion_rate': (converted_leads_count / leads_for_channel.count() * 100) if leads_for_channel.count() > 0 else 0
        }
        cac_by_channel_labels.append(channel.label)
        cac_by_channel_data.append(cac)
    
    # Get CAC trend using the method we added to the Campaign model
    cac_trend_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    cac_trend_data = [60, 65, 55, 70, 75, 80]  # Placeholder values - would use actual trend data
    
    context = {
        'avg_cac': avg_cac,
        'total_spend': total_spend,
        'new_customers_count': new_customers_count,
        'conversion_rate': conversion_rate,
        'cac_by_channel': cac_by_channel,
        'cac_by_channel_labels': cac_by_channel_labels,
        'cac_by_channel_data': cac_by_channel_data,
        'cac_trend_labels': cac_trend_labels,
        'cac_trend_data': cac_trend_data,
    }
    
    return render(request, 'marketing/cac_analytics.html', context)


@login_required
@require_http_methods(["GET"])
def get_marketing_dynamic_choices(request, model_name):
    """
    API endpoint to fetch dynamic choices for marketing models
    """
    tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
    
    if not tenant_id:
        return JsonResponse({'error': 'No tenant associated with user'}, status=400)
    
    # Map model names to actual models
    model_map = {
        'campaignstatus': CampaignStatus,
        'emailprovider': EmailProvider,
        'blocktype': BlockType,
        'emailcategory': EmailCategory,
        'messagetype': MessageType,
        'messagecategory': MessageCategory,
    }
    
    model_class = model_map.get(model_name.lower())
    
    if not model_class:
        return JsonResponse({'error': 'Invalid choice model'}, status=400)
    
    try:
        choices = model_class.objects.filter(tenant_id=tenant_id).values('id', 'name', 'label')
        return JsonResponse(list(choices), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class EmailIntegrationListView(ListView):
    model = EmailIntegration
    template_name = 'marketing/email_integration_list.html'
    context_object_name = 'email_integrations'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('user', 'provider_ref')


class EmailIntegrationCreateView(CreateView):
    model = EmailIntegration
    form_class = EmailIntegrationForm
    template_name = 'marketing/email_integration_form.html'
    success_url = reverse_lazy('marketing:email_integration_list')
    
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
        messages.success(self.request, 'Email integration created successfully.')
        return super().form_valid(form)


class EmailIntegrationUpdateView(UpdateView):
    model = EmailIntegration
    form_class = EmailIntegrationForm
    template_name = 'marketing/email_integration_form.html'
    success_url = reverse_lazy('marketing:email_integration_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Email integration updated successfully.')
        return super().form_valid(form)


class EmailIntegrationDeleteView(DeleteView):
    model = EmailIntegration
    template_name = 'marketing/email_integration_confirm_delete.html'
    success_url = reverse_lazy('marketing:email_integration_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email integration deleted successfully.')
        return super().delete(request, *args, **kwargs)

@login_required
def get_marketing_dynamic_choices(request, model_name):
    # Dynamic choices logic
    return JsonResponse({'choices': []})


class SegmentListView(LoginRequiredMixin, ListView):
    model = Segment
    template_name = 'marketing/segment_list.html'
    context_object_name = 'segments'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class SegmentCreateView(LoginRequiredMixin, CreateView):
    model = Segment
    fields = ['name', 'description', 'segment_type', 'criteria', 'is_active']
    template_name = 'marketing/segment_form.html'
    success_url = reverse_lazy('marketing:segment_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Segment created successfully.')
        return super().form_valid(form)


class SegmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Segment
    fields = ['name', 'description', 'segment_type', 'criteria', 'is_active']
    template_name = 'marketing/segment_form.html'
    success_url = reverse_lazy('marketing:segment_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Segment updated successfully.')
        return super().form_valid(form)


class SegmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Segment
    template_name = 'marketing/segment_confirm_delete.html'
    success_url = reverse_lazy('marketing:segment_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Segment deleted successfully.')
        return super().delete(request, *args, **kwargs)


class NurtureCampaignListView(LoginRequiredMixin, ListView):
    model = NurtureCampaign
    template_name = 'marketing/nurture_campaign_list.html'
    context_object_name = 'nurture_campaigns'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class NurtureCampaignCreateView(LoginRequiredMixin, CreateView):
    model = NurtureCampaign
    fields = ['name', 'description', 'target_segment', 'trigger_event', 'is_active']
    template_name = 'marketing/nurture_campaign_form.html'
    
    def get_form(self):
        form = super().get_form()
        if hasattr(self.request.user, 'tenant_id'):
            form.fields['target_segment'].queryset = Segment.objects.filter(
                tenant_id=self.request.user.tenant_id
            )
        return form
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Nurture campaign created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('marketing:nurture_campaign_update', kwargs={'pk': self.object.pk})


class NurtureCampaignUpdateView(LoginRequiredMixin, UpdateView):
    model = NurtureCampaign
    fields = ['name', 'description', 'target_segment', 'trigger_event', 'is_active']
    template_name = 'marketing/nurture_campaign_form.html'
    
    def get_form(self):
        form = super().get_form()
        if hasattr(self.request.user, 'tenant_id'):
            form.fields['target_segment'].queryset = Segment.objects.filter(
                tenant_id=self.request.user.tenant_id
            )
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Nurture campaign updated successfully.')
        return super().form_valid(form)


class NurtureCampaignDeleteView(LoginRequiredMixin, DeleteView):
    model = NurtureCampaign
    template_name = 'marketing/nurture_campaign_confirm_delete.html'
    success_url = reverse_lazy('marketing:nurture_campaign_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Nurture campaign deleted successfully.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('marketing:nurture_campaign_list')


@login_required
def segment_members(request, pk):
    segment = get_object_or_404(Segment, pk=pk)
    members = SegmentMember.objects.filter(segment=segment, is_active=True).select_related('contact')
    leads = Lead.objects.filter(tenant_id=request.user.tenant_id)
    return render(request, 'marketing/segment_members.html', {'segment': segment, 'members': members, 'leads': leads})


@login_required
def add_segment_member(request, segment_pk):
    if request.method == 'POST':
        segment = get_object_or_404(Segment, pk=segment_pk)
        lead_id = request.POST.get('lead_id')
        lead = get_object_or_404(Lead, pk=lead_id, tenant_id=request.user.tenant_id)
        member, created = SegmentMember.objects.get_or_create(segment=segment, contact=lead, defaults={'tenant_id': request.user.tenant_id, 'is_active': True})
        if not created and not member.is_active:
            member.is_active = True
            member.save()
        segment.update_member_count()
        messages.success(request, f'{lead} added to {segment.name}')
        return redirect('marketing:segment_members', pk=segment_pk)
    return redirect('marketing:segment_list')


@login_required
def remove_segment_member(request, segment_pk, member_pk):
    if request.method == 'POST':
        segment = get_object_or_404(Segment, pk=segment_pk)
        member = get_object_or_404(SegmentMember, pk=member_pk, segment=segment)
        member.is_active = False
        member.save()
        segment.update_member_count()
        messages.success(request, f'{member.contact} removed from {segment.name}')
        return redirect('marketing:segment_members', pk=segment_pk)
    return redirect('marketing:segment_list')


class ABTestListView(ListView):
    model = ABTest
    template_name = 'marketing/ab_test_list.html'
    context_object_name = 'ab_tests'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class ABTestCreateView(LoginRequiredMixin, CreateView):
    model = ABTest
    form_class = ABTestForm
    template_name = 'marketing/ab_test_form.html'
    success_url = reverse_lazy('marketing:ab_test_list')
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['variants'] = ABTestVariantCreateFormSet(self.request.POST)
        else:
            data['variants'] = ABTestVariantCreateFormSet()
        return data
        
    def form_valid(self, form):
        context = self.get_context_data()
        variants = context['variants']
        if variants.is_valid():
            form.instance.tenant_id = self.request.user.tenant_id
            form.instance.created_by = self.request.user
            self.object = form.save()
            variants.instance = self.object
            variants.save()
            messages.success(self.request, 'A/B Test created successfully.')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ABTestUpdateView(LoginRequiredMixin, UpdateView):
    model = ABTest
    form_class = ABTestForm
    template_name = 'marketing/ab_test_form.html'
    success_url = reverse_lazy('marketing:ab_test_list')
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['variants'] = ABTestVariantUpdateFormSet(self.request.POST, instance=self.object)
        else:
            data['variants'] = ABTestVariantUpdateFormSet(instance=self.object)
        return data
        
    def form_valid(self, form):
        context = self.get_context_data()
        variants = context['variants']
        if variants.is_valid():
            self.object = form.save()
            variants.instance = self.object
            variants.save()
            messages.success(self.request, 'A/B Test updated successfully.')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ABTestDeleteView(DeleteView):
    model = ABTest
    template_name = 'marketing/ab_test_confirm_delete.html'
    success_url = reverse_lazy('marketing:ab_test_list')


@login_required
def activate_ab_test(request, pk):
    test = get_object_or_404(ABTest, pk=pk)
    test.is_active = True
    test.save()
    messages.success(request, 'A/B Test activated.')
    return redirect('marketing:ab_test_list')


@login_required
def deactivate_ab_test(request, pk):
    test = get_object_or_404(ABTest, pk=pk)
    test.is_active = False
    test.save()
    messages.success(request, 'A/B Test deactivated.')
    return redirect('marketing:ab_test_list')


@login_required
def ab_test_results(request, pk):
    test = get_object_or_404(ABTest, pk=pk)
    variants = test.variants.all()
    return render(request, 'marketing/ab_test_results.html', {'test': test, 'variants': variants})


@login_required
def declare_ab_test_winner(request, pk):
    test = get_object_or_404(ABTest, pk=pk)
    variant_id = request.POST.get('variant_id')
    winner = get_object_or_404(ABTestVariant, pk=variant_id, ab_test=test)
    test.winner = winner
    test.status = 'completed'
    test.is_active = False
    test.save()
    messages.success(request, f'Variant {winner} declared as winner.')
    return redirect('marketing:ab_test_results', pk=pk)


class ABAutomatedTestListView(ListView):
    model = ABAutomatedTest
    template_name = 'marketing/ab_automated_test_list.html'
    context_object_name = 'ab_automated_tests'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class ABAutomatedTestCreateView(CreateView):
    model = ABAutomatedTest
    form_class = ABAutomatedTestForm
    template_name = 'marketing/ab_automated_test_form.html'
    success_url = reverse_lazy('marketing:ab_automated_test_list')
    
    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Automated A/B Test created successfully.')
        return super().form_valid(form)


class ABAutomatedTestUpdateView(UpdateView):
    model = ABAutomatedTest
    form_class = ABAutomatedTestForm
    template_name = 'marketing/ab_automated_test_form.html'
    success_url = reverse_lazy('marketing:ab_automated_test_list')


class ABAutomatedTestDeleteView(DeleteView):
    model = ABAutomatedTest
    template_name = 'marketing/ab_automated_test_confirm_delete.html'
    success_url = reverse_lazy('marketing:ab_automated_test_list')


@login_required
def track_ab_test_open(request, variant_id, recipient_email):
    # Log engagement event for AB test email open
    try:
        variant = get_object_or_404(ABTestVariant, pk=variant_id)
        log_engagement_event(
            tenant_id=request.user.tenant_id,
            event_type='ab_test_email_opened',
            description=f"A/B Test Email opened: {variant.subject} ({recipient_email})",
            title="A/B Test Email Opened",
            metadata={
                'variant_id': variant_id,
                'ab_test_id': variant.ab_test_id,
                'recipient_email': recipient_email,
                'subject': variant.subject
            },
            engagement_score=1,
            created_by=request.user
        )
    except Exception as e:
        logger.warning(f"Failed to log engagement event: {e}")
        
    return JsonResponse({'status': 'tracked'})


@login_required
def track_ab_test_click(request, variant_id, recipient_email):
    # Log engagement event for AB test link click
    try:
        variant = get_object_or_404(ABTestVariant, pk=variant_id)
        log_engagement_event(
            tenant_id=request.user.tenant_id,
            event_type='ab_test_link_clicked',
            description=f"A/B Test Link clicked: {variant.subject} ({recipient_email})",
            title="A/B Test Link Clicked",
            metadata={
                'variant_id': variant_id,
                'ab_test_id': variant.ab_test_id,
                'recipient_email': recipient_email,
                'subject': variant.subject
            },
            engagement_score=2,
            created_by=request.user
        )
    except Exception as e:
        logger.warning(f"Failed to log engagement event: {e}")
        
    return JsonResponse({'status': 'tracked'})


class CampaignPerformanceView(LoginRequiredMixin, TemplateView):
    template_name = 'marketing/campaign_performance.html'


class BudgetVsActualView(LoginRequiredMixin, TemplateView):
    template_name = 'marketing/budget_vs_actual.html'


class PipelineInfluenceView(LoginRequiredMixin, TemplateView):
    template_name = 'marketing/pipeline_influence.html'


class ROICalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'marketing/roi_calculator.html'


class ROICalculatorAPIView(LoginRequiredMixin, View):
    def post(self, request):
        return JsonResponse({'roi': 0.0})


class DeliverabilityReportView(LoginRequiredMixin, TemplateView):
    template_name = 'marketing/deliverability_report.html'


@login_required
def campaign_calendar_view(request):
    campaigns = Campaign.objects.all()
    if hasattr(request.user, 'tenant_id'):
        campaigns = campaigns.filter(tenant_id=request.user.tenant_id)
    
    events = []
    for campaign in campaigns:
        events.append({
            'title': campaign.campaign_name,
            'start': campaign.start_date.isoformat() if campaign.start_date else None,
            'end': campaign.end_date.isoformat() if campaign.end_date else None,
            'url': reverse_lazy('marketing:campaign_update', kwargs={'pk': campaign.pk}),
            'extendedProps': {
                'status': campaign.status
            }
        })
    
    import json
    return render(request, 'marketing/campaign_calendar.html', {
        'events_json': json.dumps(events)
    })


class DripCampaignListView(LoginRequiredMixin, ListView):
    model = DripCampaign
    template_name = 'marketing/drip_campaign_list.html'
    context_object_name = 'drip_campaigns'

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class DripCampaignCreateView(LoginRequiredMixin, CreateView):
    model = DripCampaign
    fields = ['name', 'description', 'status', 'is_active']
    template_name = 'marketing/drip_campaign_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Drip campaign created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('marketing:drip_campaign_update', kwargs={'pk': self.object.pk})


class DripCampaignUpdateView(LoginRequiredMixin, UpdateView):
    model = DripCampaign
    fields = ['name', 'description', 'status', 'is_active']
    template_name = 'marketing/drip_campaign_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Drip campaign updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('marketing:drip_campaign_list')


class DripCampaignDeleteView(LoginRequiredMixin, DeleteView):
    model = DripCampaign
    template_name = 'marketing/drip_campaign_confirm_delete.html'
    success_url = reverse_lazy('marketing:drip_campaign_list')


class DripStepCreateView(LoginRequiredMixin, CreateView):
    model = DripStep
    fields = ['step_type', 'email_template', 'wait_days', 'wait_hours', 'order']
    template_name = 'marketing/drip_step_form.html'

    def form_valid(self, form):
        form.instance.drip_campaign_id = self.kwargs['campaign_pk']
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Drip step added successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('marketing:drip_campaign_update', kwargs={'pk': self.kwargs['campaign_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campaign'] = get_object_or_404(DripCampaign, pk=self.kwargs['campaign_pk'])
        return context


class DripStepUpdateView(LoginRequiredMixin, UpdateView):
    model = DripStep
    fields = ['step_type', 'email_template', 'wait_days', 'wait_hours', 'order']
    template_name = 'marketing/drip_step_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Drip step updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('marketing:drip_campaign_update', kwargs={'pk': self.object.drip_campaign.pk})


class DripStepDeleteView(LoginRequiredMixin, DeleteView):
    model = DripStep
    template_name = 'marketing/drip_step_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('marketing:drip_campaign_update', kwargs={'pk': self.object.drip_campaign.pk})


@login_required
def enroll_in_drip(request, drip_pk):
    if request.method == 'POST':
        drip = get_object_or_404(DripCampaign, pk=drip_pk)
        email = request.POST.get('email')
        lead_id = request.POST.get('lead_id')
        account_id = request.POST.get('account_id')
        enrollment, created = DripEnrollment.objects.get_or_create(drip_campaign=drip, email=email, defaults={'tenant_id': request.user.tenant_id, 'status': 'active'})
        if lead_id: enrollment.lead_id = lead_id
        if account_id: enrollment.account_id = account_id
        if not created and enrollment.status != 'active':
            enrollment.status = 'active'
            enrollment.current_step = None 
        enrollment.save()
        
        # Log engagement event for Drip Campaign Enrollment
        try:
            log_engagement_event(
                tenant_id=request.user.tenant_id,
                event_type='drip_campaign_enrolled',
                description=f"Enrolled in Drip Campaign: {drip.name} ({email})",
                title="Drip Campaign Enrolled",
                metadata={
                    'drip_campaign_id': drip.id,
                    'email': email,
                    'lead_id': lead_id,
                    'account_id': account_id
                },
                engagement_score=3,
                created_by=request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
            
        messages.success(request, f'Successfully enrolled {email} in {drip.name}')
        return redirect('marketing:drip_campaign_list')
    return redirect('marketing:drip_campaign_list')
