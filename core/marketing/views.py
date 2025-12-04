from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect,HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from core.permissions import ObjectPermissionRequiredMixin, PermissionRequiredMixin
from .models import (
    MarketingCampaign, EmailTemplate, LandingPage, CampaignRecipient, 
    CampaignPerformance, AbTest, AbVariant, Unsubscribe, EmailCampaign, LandingPageBlock, MessageTemplate,
    DripCampaign, DripStep, DripEnrollment
)
from django.http import  JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
import json
from .forms import (
    MarketingCampaignForm, EmailTemplateForm, LandingPageForm, 
    AbTestForm, AbVariantFormSet, UnsubscribeForm
)
from django.template import Template, Context
import json
from .utils import calculate_campaign_roi, send_campaign_email

class MarketingCampaignListView(ObjectPermissionRequiredMixin, ListView):
    model = MarketingCampaign
    template_name = 'marketing/marketing_campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20
    permission_action = 'view'

class MarketingCampaignDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = MarketingCampaign
    template_name = 'marketing/marketing_campaign_detail.html'
    context_object_name = 'campaign'
    permission_action = 'view'

class MarketingCampaignCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = MarketingCampaign
    form_class = MarketingCampaignForm
    template_name = 'marketing/marketing_campaign_form.html'
    success_url = reverse_lazy('marketing:list')
    permission_action = 'change'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f"Campaign '{form.instance.name}' created!")
        return super().form_valid(form)

class MarketingCampaignUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = MarketingCampaign
    form_class = MarketingCampaignForm
    template_name = 'marketing/marketing_campaign_form.html'
    success_url = reverse_lazy('marketing:list')
    permission_action = 'change'

class MarketingCampaignDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = MarketingCampaign
    template_name = 'marketing/marketing_campaign_confirm_delete.html'
    success_url = reverse_lazy('marketing:list')
    permission_action = 'delete'

    def delete(self, request, *args, **kwargs):
        campaign = self.get_object()
        messages.success(request, f"Campaign '{campaign.name}' deleted.")
        return super().delete(request, *args, **kwargs)


# Email Template Views
class EmailTemplateListView(PermissionRequiredMixin, ListView):
    model = EmailTemplate
    template_name = 'marketing/email_template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    required_permission = 'marketing:read'

class EmailTemplateCreateView(PermissionRequiredMixin, CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'marketing/email_template_form.html'
    success_url = reverse_lazy('marketing:template_list')
    required_permission = 'marketing:write'

class EmailTemplateUpdateView(PermissionRequiredMixin, UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'marketing/email_template_form.html'
    success_url = reverse_lazy('marketing:template_list')
    required_permission = 'marketing:write'

class EmailTemplatePreviewView(PermissionRequiredMixin, DetailView):
    model = EmailTemplate
    template_name = 'marketing/email_template_preview.html'
    context_object_name = 'template'
    required_permission = 'marketing:read'

    def render_to_response(self, context, **response_kwargs):
        # Return raw HTML for preview if requested via AJAX
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(self.object.html_content)
        return super().render_to_response(context, **response_kwargs)

class ActivateTemplateView(PermissionRequiredMixin, View):
    required_permission = 'marketing:write'

    def post(self, request, pk):
        template = get_object_or_404(EmailTemplate, pk=pk, tenant_id=request.user.tenant_id)
        template.is_active = True
        template.save(update_fields=['is_active'])
        messages.success(request, f"Template '{template.name}' activated successfully!")
        return redirect('marketing:template_list')

class DeactivateTemplateView(PermissionRequiredMixin, View):
    required_permission = 'marketing:write'

    def post(self, request, pk):
        template = get_object_or_404(EmailTemplate, pk=pk, tenant_id=request.user.tenant_id)
        template.is_active = False
        template.save(update_fields=['is_active'])
        messages.success(request, f"Template '{template.name}' deactivated successfully!")
        return redirect('marketing:template_list')

def track_email_open(request, recipient_id):
    """
    Track email open event for marketing campaigns.
    This is called when the tracking pixel is loaded in an email.
    """
    try:
        from .utils import track_email_open_event
        track_email_open_event(recipient_id)
        
        # Return 1x1 transparent pixel
        pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\x00\x00\x00\x00IEND\xaeB`\x82'
        return HttpResponse(pixel, content_type='image/png')
        
    except Exception as e:
        # Return empty response on error to avoid email client issues
        return HttpResponse('', content_type='image/png')


# Landing Page Views
class LandingPageListView(PermissionRequiredMixin, ListView):
    model = LandingPage
    template_name = 'marketing/landing_page_list.html'
    context_object_name = 'landing_pages'
    paginate_by = 20
    required_permission = 'marketing:read'

class LandingPageCreateView(PermissionRequiredMixin, CreateView):
    model = LandingPage
    form_class = LandingPageForm
    template_name = 'marketing/landing_page_form.html'
    success_url = reverse_lazy('marketing:landing_page_list')
    required_permission = 'marketing:write'

class LandingPageUpdateView(PermissionRequiredMixin, UpdateView):
    model = LandingPage
    form_class = LandingPageForm
    template_name = 'marketing/landing_page_form.html'
    success_url = reverse_lazy('marketing:landing_page_list')
    required_permission = 'marketing:write'

class LandingPageDeleteView(PermissionRequiredMixin, DeleteView):
    model = LandingPage
    template_name = 'marketing/landing_page_confirm_delete.html'
    success_url = reverse_lazy('marketing:landing_page_list')
    required_permission = 'marketing:delete'
def track_landing_page_visit(request, landing_page_id):
    """
    Track landing page visit for marketing campaigns.
    This is called when a landing page is loaded with lead tracking.
    """
    try:
        lead_id = request.GET.get('lead_id')
        from .utils import track_landing_page_visit_event
        track_landing_page_visit_event(landing_page_id, lead_id)
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





# A/B Test Views
class AbTestListView(PermissionRequiredMixin, ListView):
    model = AbTest
    template_name = 'marketing/ab_test_list.html'
    context_object_name = 'ab_tests'
    paginate_by = 20
    required_permission = 'marketing:read'

class AbTestCreateView(PermissionRequiredMixin, CreateView):
    model = AbTest
    form_class = AbTestForm
    template_name = 'marketing/ab_test_form.html'
    success_url = reverse_lazy('marketing:ab_test_list')
    required_permission = 'marketing:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['variants'] = AbVariantFormSet(self.request.POST)
        else:
            context['variants'] = AbVariantFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        variants = context['variants']
        
        if variants.is_valid():
            response = super().form_valid(form)
            variants.instance = self.object
            variants.save()
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))


# Campaign Recipient Views
class CampaignRecipientListView(ObjectPermissionRequiredMixin, ListView):
    model = CampaignRecipient
    template_name = 'marketing/campaign_recipient_list.html'
    context_object_name = 'recipients'
    paginate_by = 50
    permission_action = 'view'

    def get_queryset(self):
        campaign_id = self.kwargs.get('campaign_id')
        if campaign_id:
            return CampaignRecipient.objects.filter(campaign_id=campaign_id)
        return CampaignRecipient.objects.all()


# Send Campaign View
class SendCampaignView(ObjectPermissionRequiredMixin, UpdateView):
    permission_action = 'change'

    def post(self, request, pk):
        campaign = get_object_or_404(MarketingCampaign, pk=pk)
        
        # Permission check
        from core.object_permissions import MarketingCampaignObjectPolicy
        if not MarketingCampaignObjectPolicy.can_change(request.user, campaign):
            messages.error(request, "Permission denied.")
            return redirect('marketing:detail', pk=pk)
        
        # Update status
        campaign.status = 'sending'
        campaign.save(update_fields=['status'])
        
        # Send campaign asynchronously
        from .tasks import send_campaign_task
        send_campaign_task.delay(campaign.id)
        
        messages.success(request, f"Campaign '{campaign.name}' is now sending.")
        return redirect('marketing:detail', pk=pk)





# Track Link Click View
def track_link_click(request, recipient_id):
    """
    Track link click event for marketing campaigns.
    This is called when a tracked link is clicked in an email.
    """
    try:
        url = request.GET.get('url', '/')
        from .utils import track_link_click_event
        redirect_url = track_link_click_event(recipient_id, url)
        return redirect(redirect_url)
        
    except Exception:
        # Redirect to original URL on error
        url = request.GET.get('url', '/')
        return redirect(url)


# Unsubscribe View
class UnsubscribeView(ListView):
    def get(self, request, recipient_id):
        try:
            recipient = get_object_or_404(CampaignRecipient, id=recipient_id)
            context = {'recipient': recipient}
            return render(request, 'marketing/unsubscribe_confirm.html', context)
        except Exception:
            return render(request, 'marketing/unsubscribe_error.html')

    def post(self, request, recipient_id):
        try:
            recipient = get_object_or_404(CampaignRecipient, id=recipient_id)
            
            # Create unsubscribe record
            Unsubscribe.objects.get_or_create(
                email=recipient.email,
                tenant_id=recipient.tenant_id,
                defaults={'campaign': recipient.campaign}
            )
            
            # Update recipient status
            recipient.status = 'unsubscribed'
            recipient.save(update_fields=['status'])
            
            return render(request, 'marketing/unsubscribe_success.html')
        except Exception:
            return render(request, 'marketing/unsubscribe_error.html')


# Update Campaign Schedule View (for calendar drag-and-drop)
class UpdateCampaignScheduleView(ListView):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        try:
            data = json.loads(request.body)
            campaign_id = data.get('campaign_id')
            start_date = data.get('start')
            
            campaign = get_object_or_404(MarketingCampaign, id=campaign_id)
            
            # Permission check
            from core.object_permissions import MarketingCampaignObjectPolicy
            if not MarketingCampaignObjectPolicy.can_change(request.user, campaign):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Update schedule
            from django.utils.dateparse import parse_datetime
            campaign.send_date = parse_datetime(start_date)
            campaign.save(update_fields=['send_date'])
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# Complete Next Best Action View (from previous request)
class CompleteNextBestActionView(UpdateView):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        try:
            data = json.loads(request.body)
            action_id = data.get('action_id')
            
            from engagement.models import NextBestAction
            action = get_object_or_404(NextBestAction, id=action_id)
            
            # Permission check
            from core.object_permissions import AccountObjectPolicy
            if not AccountObjectPolicy.can_change(request.user, action.account):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            action.completed = True
            from django.utils import timezone
            action.completed_at = timezone.now()
            action.save(update_fields=['completed', 'completed_at'])
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, 
    DeleteView, TemplateView, FormView
)
from core.permissions import ObjectPermissionRequiredMixin, PermissionRequiredMixin
from .models import (
    CampaignPerformance, LandingPageBlock, LandingPage, 
    MarketingCampaign
)
from .forms import (
    CampaignPerformanceForm, LandingPageBlockForm, 
    CampaignPerformanceFilterForm
)
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta

class CampaignPerformanceListView(PermissionRequiredMixin, ListView):
    """
    List view for campaign performance records with filtering.
    """
    model = CampaignPerformance
    template_name = 'marketing/campaign_performance_list.html'
    context_object_name = 'performances'
    paginate_by = 25
    required_permission = 'marketing:read'

    def get_queryset(self):
        queryset = super().get_queryset()
        form = CampaignPerformanceFilterForm(self.request.GET, user=self.request.user)
        
        if form.is_valid():
            if form.cleaned_data.get('start_date'):
                queryset = queryset.filter(date__gte=form.cleaned_data['start_date'])
            if form.cleaned_data.get('end_date'):
                queryset = queryset.filter(date__lte=form.cleaned_data['end_date'])
            if form.cleaned_data.get('campaign'):
                queryset = queryset.filter(campaign=form.cleaned_data['campaign'])
        
        return queryset.select_related('campaign').order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = CampaignPerformanceFilterForm(
            self.request.GET, 
            user=self.request.user
        )
        return context


class CampaignPerformanceDetailView(PermissionRequiredMixin, DetailView):
    """
    Detail view for individual campaign performance records.
    """
    model = CampaignPerformance
    template_name = 'marketing/campaign_performance_detail.html'
    context_object_name = 'performance'
    required_permission = 'marketing:read'


class CampaignPerformanceCreateView(PermissionRequiredMixin, CreateView):
    """
    Create view for campaign performance records.
    """
    model = CampaignPerformance
    form_class = CampaignPerformanceForm
    template_name = 'marketing/campaign_performance_form.html'
    success_url = reverse_lazy('marketing:performance_list')
    required_permission = 'marketing:write'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Campaign performance record created successfully!")
        return super().form_valid(form)


class CampaignPerformanceUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update view for campaign performance records.
    """
    model = CampaignPerformance
    form_class = CampaignPerformanceForm
    template_name = 'marketing/campaign_performance_form.html'
    success_url = reverse_lazy('marketing:performance_list')
    required_permission = 'marketing:write'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
 
    def form_valid(self, form):
        messages.success(self.request, "Campaign performance record updated successfully!")
        return super().form_valid(form)


class CampaignPerformanceDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete view for campaign performance records.
    """
    model = CampaignPerformance
    template_name = 'marketing/campaign_performance_confirm_delete.html'
    success_url = reverse_lazy('marketing:performance_list')
    required_permission = 'marketing:delete'

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Campaign performance record deleted successfully!")
        return super().delete(request, *args, **kwargs)


class CampaignPerformanceAnalyticsView(PermissionRequiredMixin, TemplateView):
    """
    Analytics dashboard view for campaign performance with charts and KPIs.
    """
    template_name = 'marketing/campaign_performance_analytics.html'
    required_permission = 'marketing:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        
        # Date range (last 30 days by default)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Overall metrics
        performances = CampaignPerformance.objects.filter(
            date__range=[start_date, end_date],
            campaign__tenant_id=tenant_id
        )
        
        if performances.exists():
            total_revenue = performances.aggregate(total=Sum('revenue_generated'))['total'] or 0
            total_sent = performances.aggregate(total=Sum('total_sent'))['total'] or 0
            total_opened = performances.aggregate(total=Sum('total_opened'))['total'] or 0
            total_clicked = performances.aggregate(total=Sum('total_clicked'))['total'] or 0
            
            avg_open_rate = performances.aggregate(avg=Avg('open_rate'))['avg'] or 0
            avg_click_rate = performances.aggregate(avg=Avg('click_rate'))['avg'] or 0
            avg_conversion_rate = performances.aggregate(avg=Avg('conversion_rate'))['avg'] or 0
            
            # Campaign count
            campaign_count = performances.values('campaign').distinct().count()
        else:
            total_revenue = total_sent = total_opened = total_clicked = 0
            avg_open_rate = avg_click_rate = avg_conversion_rate = 0
            campaign_count = 0
        
        # Trend data for charts
        trend_data = []
        for i in range(30):
            date = end_date - timedelta(days=i)
            perf = performances.filter(date=date).aggregate(
                revenue=Sum('revenue_generated'),
                sent=Sum('total_sent'),
                opened=Sum('total_opened'),
                clicked=Sum('total_clicked'),
                open_rate=Avg('open_rate'),
                click_rate=Avg('click_rate')
            )
            trend_data.append({
                'date': date.isoformat(),
                'revenue': float(perf['revenue'] or 0),
                'sent': perf['sent'] or 0,
                'opened': perf['opened'] or 0,
                'clicked': perf['clicked'] or 0,
                'open_rate': float(perf['open_rate'] or 0),
                'click_rate': float(perf['click_rate'] or 0),
            })
        trend_data.reverse()
        
        # Top performing campaigns
        top_campaigns = performances.values('campaign__name').annotate(
            total_revenue=Sum('revenue_generated'),
            total_sent=Sum('total_sent'),
            avg_open_rate=Avg('open_rate')
        ).order_by('-total_revenue')[:5]
        
        context.update({
            'total_revenue': total_revenue,
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'avg_open_rate': round(avg_open_rate, 2),
            'avg_click_rate': round(avg_click_rate, 2),
            'avg_conversion_rate': round(avg_conversion_rate, 2),
            'campaign_count': campaign_count,
            'trend_data_json': trend_data,
            'top_campaigns': top_campaigns,
            'start_date': start_date,
            'end_date': end_date,
        })
        return context


# Landing Page Block Views
class LandingPageBlockListView(PermissionRequiredMixin, ListView):
    """
    List view for landing page blocks (typically accessed via AJAX in builder).
    """
    model = LandingPageBlock
    template_name = 'marketing/landing_page_block_list.html'
    context_object_name = 'blocks'
    required_permission = 'marketing:read'

    def get_queryset(self):
        landing_page_id = self.kwargs.get('landing_page_id')
        if landing_page_id:
            return LandingPageBlock.objects.filter(
                landing_page_id=landing_page_id,
                landing_page__tenant_id=getattr(self.request.user, 'tenant_id', None)
            ).order_by('order')
        return LandingPageBlock.objects.none()


class LandingPageBlockCreateView(PermissionRequiredMixin, CreateView):
    """
    Create view for landing page blocks (typically used via AJAX in builder).
    """
    model = LandingPageBlock
    form_class = LandingPageBlockForm
    template_name = 'marketing/landing_page_block_form.html'
    required_permission = 'marketing:write'

    def form_valid(self, form):
        landing_page_id = self.kwargs.get('landing_page_id')
        landing_page = get_object_or_404(LandingPage, id=landing_page_id)
        form.instance.landing_page = landing_page
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('marketing:landing_builder', kwargs={'pk': self.object.landing_page.pk})


class LandingPageBlockUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update view for landing page blocks (typically used via AJAX in builder).
    """
    model = LandingPageBlock
    form_class = LandingPageBlockForm
    template_name = 'marketing/landing_page_block_form.html'
    required_permission = 'marketing:write'

    def get_success_url(self):
        return reverse_lazy('marketing:landing_builder', kwargs={'pk': self.object.landing_page.pk})


class LandingPageBlockDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete view for landing page blocks.
    """
    model = LandingPageBlock
    template_name = 'marketing/landing_page_block_confirm_delete.html'
    required_permission = 'marketing:delete'

    def get_success_url(self):
        return reverse_lazy('marketing:landing_builder', kwargs={'pk': self.object.landing_page.pk})


# AJAX Views for Builder
class UpdateLandingPageBlocksView(PermissionRequiredMixin, UpdateView):
    """
    AJAX view to update multiple landing page blocks order and content.
    """
    permission_action = 'change'

    def post(self, request, landing_page_id):
        try:
            import json
            data = json.loads(request.body)
            blocks_data = data.get('blocks', [])
            
            landing_page = get_object_or_404(LandingPage, id=landing_page_id)
            
            # Permission check
            from core.object_permissions import LandingPageObjectPolicy
            if not LandingPageObjectPolicy.can_change(request.user, landing_page):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Update blocks
            for block_data in blocks_data:
                block_id = block_data.get('id')
                if block_id:
                    # Update existing block
                    block = get_object_or_404(LandingPageBlock, id=block_id, landing_page=landing_page)
                    block.order = block_data.get('order', block.order)
                    block.content = block_data.get('content', block.content)
                    block.is_active = block_data.get('is_active', block.is_active)
                    block.save()
                else:
                    # Create new block
                    LandingPageBlock.objects.create(
                        landing_page=landing_page,
                        block_type=block_data.get('block_type', 'text'),
                        title=block_data.get('title', ''),
                        content=block_data.get('content', {}),
                        order=block_data.get('order', 0),
                        is_active=block_data.get('is_active', True)
                    )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class GetLandingPageBlocksView(PermissionRequiredMixin, ListView):
    """
    AJAX view to get landing page blocks as JSON.
    """
    permission_action = 'view'

    def get(self, request, landing_page_id):
        try:
            landing_page = get_object_or_404(LandingPage, id=landing_page_id)
            
            # Permission check
            from core.object_permissions import LandingPageObjectPolicy
            if not LandingPageObjectPolicy.can_view(request.user, landing_page):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            blocks = landing_page.blocks.all().values(
                'id', 'block_type', 'title', 'content', 'order', 'is_active'
            )
            
            return JsonResponse({'blocks': list(blocks)})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class CampaignCalendarView(PermissionRequiredMixin, TemplateView):
    template_name = 'marketing/calendar.html'
    required_permission = 'marketing:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaigns = self.get_queryset()
        context['campaigns'] = campaigns
        context['status_choices'] = [
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('draft', 'Draft'),
        ]
        return context

    def get_queryset(self):
        from core.object_permissions import MarketingCampaignObjectPolicy
        return MarketingCampaignObjectPolicy.get_viewable_queryset(self.request.user, MarketingCampaign.objects.all())
    



@method_decorator(csrf_exempt, name='dispatch')
class TrackEngagementView(View):
    """
    API endpoint to track marketing engagement events.
    This handles all engagement tracking for the Marketing module.
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            event_type = data.get('event_type')
            lead_id = data.get('lead_id')
            campaign_id = data.get('campaign_id')
            recipient_id = data.get('recipient_id')
            points = data.get('points', 0)
            
            if not event_type:
                return JsonResponse({'error': 'event_type required'}, status=400)
            
            # Track the engagement event
            from .utils import track_marketing_engagement
            result = track_marketing_engagement(
                event_type=event_type,
                lead_id=lead_id,
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                points=points,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if result:
                return JsonResponse({
                    'success': True,
                    'message': f'Engagement tracked: {event_type}',
                    'lead_score_updated': result.get('lead_score_updated', False),
                    'new_score': result.get('new_score', 0)
                })
            else:
                return JsonResponse({'error': 'Failed to track engagement'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
# Template Builder Views
class TemplateBuilderView(PermissionRequiredMixin, TemplateView):
    """
    Visual template builder with Quill.js editor and merge tag helper.
    """
    template_name = 'marketing/template_builder.html'
    required_permission = 'marketing:write'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available merge tags (sample data for preview)
        merge_tags = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'company': 'Acme Corp',
            'account_name': 'Acme Corporation',
            'opportunity_name': 'Q4 Enterprise Deal',
            'task_title': 'Follow-up Call',
            'today': timezone.now().strftime('%B %d, %Y'),
        }
        
        context['merge_tags'] = merge_tags
        context['merge_tags_json'] = json.dumps(merge_tags)
        
        # Get existing templates for cloning
        context['existing_templates'] = EmailTemplate.objects.filter(
            tenant_id=self.request.user.tenant_id,
            is_active=True
        ).order_by('-usage_count')[:10]
        
        return context


class TemplatePreviewView(PermissionRequiredMixin, View):
    """
    AJAX endpoint for live template preview with merge tag rendering.
    """
    required_permission = 'marketing:read'
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            html_content = data.get('html_content', '')
            merge_tags = data.get('merge_tags', {})
            
            # Render template with merge tags
            template = Template(html_content)
            context = Context(merge_tags)
            rendered = template.render(context)
            
            return JsonResponse({
                'success': True,
                'rendered_html': rendered
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class MessageTemplateCreateView(PermissionRequiredMixin, CreateView):
    """Create view for MessageTemplate (SMS, in-app, etc.)"""
    model = MessageTemplate
    template_name = 'marketing/message_template_form.html'
    fields = ['name', 'message_type', 'content', 'category', 'description', 'is_shared', 'is_active']
    success_url = reverse_lazy('marketing:template_list')
    required_permission = 'marketing:write'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Message template '{form.instance.name}' created!")
        return super().form_valid(form)


# Drip Campaign Views
class DripCampaignListView(PermissionRequiredMixin, ListView):
    """List all drip campaigns."""
    model = DripCampaign
    template_name = 'marketing/drip_campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20
    required_permission = 'marketing:read'

    def get_queryset(self):
        from .models import DripCampaign
        return DripCampaign.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).prefetch_related('steps')


class DripCampaignDetailView(PermissionRequiredMixin, DetailView):
    """Detail view for a drip campaign with steps."""
    model = DripCampaign
    template_name = 'marketing/drip_campaign_detail.html'
    context_object_name = 'campaign'
    required_permission = 'marketing:read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['steps'] = self.object.steps.all().order_by('order')
        context['enrollments_count'] = self.object.enrollments.filter(status='active').count()
        return context


class DripCampaignCreateView(PermissionRequiredMixin, CreateView):
    """Create a new drip campaign."""
    model = DripCampaign
    template_name = 'marketing/drip_campaign_form.html'
    required_permission = 'marketing:write'
    
    def get_form_class(self):
        from .forms import DripCampaignForm
        return DripCampaignForm

    def get_success_url(self):
        return reverse('marketing:drip_campaign_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, f"Drip campaign '{form.instance.name}' created!")
        return super().form_valid(form)


class DripCampaignUpdateView(PermissionRequiredMixin, UpdateView):
    """Update a drip campaign."""
    model = DripCampaign
    template_name = 'marketing/drip_campaign_form.html'
    required_permission = 'marketing:write'
    
    def get_form_class(self):
        from .forms import DripCampaignForm
        return DripCampaignForm

    def get_success_url(self):
        return reverse('marketing:drip_campaign_detail', kwargs={'pk': self.object.pk})


class DripStepCreateView(PermissionRequiredMixin, CreateView):
    """Add a step to a drip campaign."""
    model = DripStep
    template_name = 'marketing/drip_step_form.html'
    required_permission = 'marketing:write'

    def get_form_class(self):
        from .forms import DripStepForm
        return DripStepForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['drip_campaign'] = get_object_or_404(DripCampaign, pk=self.kwargs['campaign_pk'])
        return kwargs

    def get_success_url(self):
        return reverse('marketing:drip_campaign_detail', kwargs={'pk': self.kwargs['campaign_pk']})

    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, "Step added successfully!")
        return super().form_valid(form)


class DripEnrollmentCreateView(PermissionRequiredMixin, CreateView):
    """Enroll an account in a drip campaign."""
    model = DripEnrollment
    template_name = 'marketing/drip_enrollment_form.html'
    required_permission = 'marketing:write'

    def get_form_class(self):
        from .forms import DripEnrollmentForm
        return DripEnrollmentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('marketing:drip_campaign_list')

    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        # Set initial next_execution_at to now to start immediately
        form.instance.next_execution_at = timezone.now()
        messages.success(self.request, f"Enrolled {form.instance.email} in {form.instance.drip_campaign.name}!")
        return super().form_valid(form)

