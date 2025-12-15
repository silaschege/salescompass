from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Avg, Sum, Count
from .models import Campaign, EmailTemplate, LandingPageBlock, MessageTemplate, EmailCampaign, CampaignStatus, EmailProvider, BlockType, EmailCategory, MessageType, MessageCategory, EmailIntegration
from .forms import CampaignForm, EmailTemplateForm, LandingPageBlockForm, MessageTemplateForm, EmailCampaignForm, CampaignStatusForm, EmailProviderForm, BlockTypeForm, EmailCategoryForm, MessageTypeForm, MessageCategoryForm, EmailIntegrationForm
from tenants.models import Tenant as TenantModel
from core.models import User
from leads.models import Lead
from opportunities.models import Opportunity


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
        messages.success(self.request, 'Campaign created successfully.')
        return super().form_valid(form)


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
        messages.success(self.request, 'Campaign updated successfully.')
        return super().form_valid(form)


class CampaignDeleteView(DeleteView):
    model = Campaign
    template_name = 'marketing/campaign_confirm_delete.html'
    success_url = reverse_lazy('marketing:campaign_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Campaign deleted successfully.')
        return super().delete(request, *args, **kwargs)


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
        messages.success(self.request, 'Email campaign created successfully.')
        return super().form_valid(form)


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
