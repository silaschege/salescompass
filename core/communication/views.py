from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.db.models import Q, Count
from .models import (
    NotificationTemplate, EmailSMSServiceConfiguration, CommunicationHistory,
    Email, SMS, CallLog, CustomerSupportTicket, FeedbackAndSurvey,
    SocialMediaPost, ChatMessage, EmailSignature
)
from .forms import (
    NotificationTemplateForm, EmailSMSServiceConfigurationForm, CommunicationHistoryForm,
    CustomerSupportTicketForm, FeedbackAndSurveyForm, EmailForm, SMSForm, CallLogForm,
    EmailSignatureForm
)
from itertools import chain
from django.db.models import Value, CharField
import logging

# Import engagement tracking
from engagement.utils import log_engagement_event

logger = logging.getLogger(__name__)


# ============================================================================
# NOTIFICATION TEMPLATE VIEWS
# ============================================================================

class NotificationTemplateListView(LoginRequiredMixin, ListView):
    """List all notification templates"""
    model = NotificationTemplate
    template_name = 'communication/notification_template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

    def get_queryset(self):
        queryset = NotificationTemplate.objects.filter(tenant=self.request.user.tenant)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(subject__icontains=search)
            )
        return queryset.order_by('-created_at')


class NotificationTemplateDetailView(LoginRequiredMixin, DetailView):
    """View notification template details"""
    model = NotificationTemplate
    template_name = 'communication/notification_template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        return NotificationTemplate.objects.filter(tenant=self.request.user.tenant)


class NotificationTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create new notification template"""
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'communication/notification_template_form.html'
    success_url = reverse_lazy('communication:template_list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Notification template created successfully!')
        return super().form_valid(form)


class NotificationTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Update notification template"""
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'communication/notification_template_form.html'
    success_url = reverse_lazy('communication:template_list')

    def get_queryset(self):
        return NotificationTemplate.objects.filter(tenant=self.request.user.tenant)

    def form_valid(self, form):
        messages.success(self.request, 'Notification template updated successfully!')
        return super().form_valid(form)


class NotificationTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete notification template"""
    model = NotificationTemplate
    template_name = 'communication/notification_template_confirm_delete.html'
    success_url = reverse_lazy('communication:template_list')

    def get_queryset(self):
        return NotificationTemplate.objects.filter(tenant=self.request.user.tenant)


# ============================================================================
# EMAIL/SMS SERVICE CONFIGURATION VIEWS
# ============================================================================

class EmailSMSConfigListView(LoginRequiredMixin, ListView):
    """List email/SMS service configurations"""
    model = EmailSMSServiceConfiguration
    template_name = 'communication/email_config_list.html'
    context_object_name = 'configs'

    def get_queryset(self):
        return EmailSMSServiceConfiguration.objects.filter(tenant=self.request.user.tenant)


class EmailSMSConfigCreateView(LoginRequiredMixin, CreateView):
    """Create email/SMS service configuration"""
    model = EmailSMSServiceConfiguration
    form_class = EmailSMSServiceConfigurationForm
    template_name = 'communication/email_config_form.html'
    success_url = reverse_lazy('communication:config_list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Service configuration created successfully!')
        return super().form_valid(form)


class EmailSMSConfigUpdateView(LoginRequiredMixin, UpdateView):
    """Update email/SMS service configuration"""
    model = EmailSMSServiceConfiguration
    form_class = EmailSMSServiceConfigurationForm
    template_name = 'communication/email_config_form.html'
    success_url = reverse_lazy('communication:config_list')

    def get_queryset(self):
        return EmailSMSServiceConfiguration.objects.filter(tenant=self.request.user.tenant)


# ============================================================================
# COMMUNICATION HISTORY VIEWS
# ============================================================================

class CommunicationHistoryListView(LoginRequiredMixin, ListView):
    """List communication history"""
    model = CommunicationHistory
    template_name = 'communication/history_list.html'
    context_object_name = 'history'
    paginate_by = 50

    def get_queryset(self):
        queryset = CommunicationHistory.objects.filter(tenant=self.request.user.tenant)
        
        # Filter by type
        comm_type = self.request.GET.get('type')
        if comm_type:
            queryset = queryset.filter(communication_type=comm_type)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')


class CommunicationHistoryDetailView(LoginRequiredMixin, DetailView):
    """View communication history detail"""
    model = CommunicationHistory
    template_name = 'communication/history_detail.html'
    context_object_name = 'history'

    def get_queryset(self):
        return CommunicationHistory.objects.filter(tenant=self.request.user.tenant)


# ============================================================================
# CUSTOMER SUPPORT TICKET VIEWS
# ============================================================================

class TicketListView(LoginRequiredMixin, ListView):
    """List support tickets"""
    model = CustomerSupportTicket
    template_name = 'communication/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 25

    def get_queryset(self):
        queryset = CustomerSupportTicket.objects.filter(tenant=self.request.user.tenant)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_counts'] = CustomerSupportTicket.objects.filter(
            tenant=self.request.user.tenant
        ).values('status').annotate(count=Count('id'))
        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    """View ticket details"""
    model = CustomerSupportTicket
    template_name = 'communication/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        return CustomerSupportTicket.objects.filter(tenant=self.request.user.tenant)


class TicketCreateView(LoginRequiredMixin, CreateView):
    """Create new support ticket"""
    model = CustomerSupportTicket
    form_class = CustomerSupportTicketForm
    template_name = 'communication/ticket_form.html'
    success_url = reverse_lazy('communication:ticket_list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.submitted_by = self.request.user
        
        response = super().form_valid(form)
        
        # Log engagement event for support ticket created
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='support_ticket_created',
                description=f"Support ticket created: {self.object.subject}",
                title="Support Ticket Created",
                metadata={
                    'ticket_id': self.object.id,
                    'subject': self.object.subject,
                    'priority': self.object.priority,
                    'status': self.object.status
                },
                engagement_score=1,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        messages.success(self.request, 'Support ticket created successfully!')
        return response


class TicketUpdateView(LoginRequiredMixin, UpdateView):
    """Update support ticket"""
    model = CustomerSupportTicket
    form_class = CustomerSupportTicketForm
    template_name = 'communication/ticket_form.html'
    success_url = reverse_lazy('communication:ticket_list')

    def get_queryset(self):
        return CustomerSupportTicket.objects.filter(tenant=self.request.user.tenant)


# ============================================================================
# FEEDBACK AND SURVEY VIEWS
# ============================================================================

class FeedbackListView(LoginRequiredMixin, ListView):
    """List feedback forms"""
    model = FeedbackAndSurvey
    template_name = 'communication/feedback_list.html'
    context_object_name = 'feedback_forms'

    def get_queryset(self):
        return FeedbackAndSurvey.objects.filter(tenant_target=self.request.user.tenant)


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    """Create feedback form"""
    model = FeedbackAndSurvey
    form_class = FeedbackAndSurveyForm
    template_name = 'communication/feedback_form.html'
    success_url = reverse_lazy('communication:feedback_list')

    def form_valid(self, form):
        form.instance.tenant_target = self.request.user.tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Feedback form created successfully!')
        return super().form_valid(form)


# ============================================================================
# EMAIL VIEWS
# ============================================================================

class EmailListView(LoginRequiredMixin, ListView):
    """List emails"""
    model = Email
    template_name = 'communication/email_list.html'
    context_object_name = 'emails'
    paginate_by = 50

    def get_queryset(self):
        return Email.objects.filter(tenant=self.request.user.tenant).order_by('-created_at')


class EmailComposeView(LoginRequiredMixin, CreateView):
    """Compose and send email"""
    model = Email
    form_class = EmailForm
    template_name = 'communication/email_compose.html'
    success_url = reverse_lazy('communication:email_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['signatures'] = EmailSignature.objects.filter(user=self.request.user, tenant=self.request.user.tenant)
        context['templates'] = NotificationTemplate.objects.filter(tenant=self.request.user.tenant, template_type='email')
        return context

    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.tenant = self.request.user.tenant
        form.instance.status = 'queued'
        response = super().form_valid(form)
        
        email = self.object
        if not email.send_at or email.send_at <= timezone.now():
            from .email_service import email_service
            email_service.send_model_email(email)
            messages.success(self.request, 'Email sent successfully!')
            
            # Log engagement event for email sent
            try:
                log_engagement_event(
                    tenant_id=self.request.user.tenant_id,
                    event_type='email_sent',
                    description=f"Email sent to {email.recipient}: {email.subject}",
                    title="Email Sent",
                    metadata={
                        'email_id': email.id,
                        'recipient': email.recipient,
                        'subject': email.subject
                    },
                    engagement_score=2,
                    created_by=self.request.user
                )
            except Exception as e:
                logger.warning(f"Failed to log engagement event: {e}")
        else:
            messages.success(self.request, 'Email scheduled for sending!')
            
        return response


# ============================================================================
# SMS VIEWS
# ============================================================================

class SMSListView(LoginRequiredMixin, ListView):
    """List SMS messages"""
    model = SMS
    template_name = 'communication/sms_list.html'
    context_object_name = 'sms_messages'
    paginate_by = 50

    def get_queryset(self):
        return SMS.objects.filter(tenant=self.request.user.tenant).order_by('-created_at')


class SMSSendView(LoginRequiredMixin, CreateView):
    """Send SMS message"""
    model = SMS
    form_class = SMSForm
    template_name = 'communication/sms_send.html'
    success_url = reverse_lazy('communication:sms_list')

    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.tenant = self.request.user.tenant
        form.instance.status = 'queued'
        response = super().form_valid(form)
        
        # Trigger sending
        from .sms_service import sms_service
        sms_service.send_model_sms(self.object)
        
        # Log engagement event for SMS sent
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='sms_sent',
                description=f"SMS sent to {self.object.recipient}",
                title="SMS Sent",
                metadata={
                    'sms_id': self.object.id,
                    'recipient': self.object.recipient,
                    'message_preview': self.object.message[:50] if self.object.message else ''
                },
                engagement_score=2,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        messages.success(self.request, 'SMS sent successfully!')
        return response


# ============================================================================
# CALL LOG VIEWS
# ============================================================================

class CallLogListView(LoginRequiredMixin, ListView):
    """List call logs"""
    model = CallLog
    template_name = 'communication/call_log_list.html'
    context_object_name = 'calls'
    paginate_by = 50

    def get_queryset(self):
        return CallLog.objects.filter(tenant=self.request.user.tenant).order_by('-call_started_at')


class CallLogCreateView(LoginRequiredMixin, CreateView):
    """Log a call"""
    model = CallLog
    form_class = CallLogForm
    template_name = 'communication/call_log_form.html'
    success_url = reverse_lazy('communication:call_log_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.tenant = self.request.user.tenant
        if not form.instance.call_started_at:
            form.instance.call_started_at = timezone.now()
        
        response = super().form_valid(form)
        
        # Log engagement event for call completed
        try:
            log_engagement_event(
                tenant_id=self.request.user.tenant_id,
                event_type='call_completed',
                description=f"Call with {self.object.phone_number} - {self.object.outcome}",
                title="Call Completed",
                metadata={
                    'call_id': self.object.id,
                    'phone_number': self.object.phone_number,
                    'duration': self.object.duration_seconds,
                    'outcome': self.object.outcome,
                    'direction': self.object.direction
                },
                engagement_score=3,
                created_by=self.request.user
            )
        except Exception as e:
            logger.warning(f"Failed to log engagement event: {e}")
        
        messages.success(self.request, 'Call logged successfully!')
        return response


class CallLogDetailView(LoginRequiredMixin, DetailView):
    """View call log details"""
    model = CallLog
    template_name = 'communication/call_log_detail.html'
    context_object_name = 'call'

    def get_queryset(self):
        return CallLog.objects.filter(tenant=self.request.user.tenant)


# ============================================================================
# DASHBOARD VIEW
# ============================================================================

class CommunicationDashboardView(LoginRequiredMixin, ListView):
    """Communication dashboard"""
    template_name = 'communication/dashboard.html'
    model = Email  # Just to satisfy ListView, we'll override context

    def get_queryset(self):
        return Email.objects.filter(tenant=self.request.user.tenant)[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get summary stats
        context['email_count'] = Email.objects.filter(tenant=tenant).count()
        context['sms_count'] = SMS.objects.filter(tenant=tenant).count()
        context['call_count'] = CallLog.objects.filter(tenant=tenant).count()
        context['ticket_count'] = CustomerSupportTicket.objects.filter(tenant=tenant).count()
        
        # Recent activity
        context['recent_emails'] = Email.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        context['recent_tickets'] = CustomerSupportTicket.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        context['recent_calls'] = CallLog.objects.filter(tenant=self.request.user.tenant).order_by('-call_started_at')[:5]
        return context


# ============================================================================
# UNIFIED INBOX VIEW
# ============================================================================

class UnifiedInboxView(LoginRequiredMixin, ListView):
    """Unified view for all communication types"""
    template_name = 'communication/unified_inbox.html'
    context_object_name = 'interactions'
    paginate_by = 50

    def get_queryset(self):
        tenant = self.request.user.tenant
        
        emails = Email.objects.filter(tenant=tenant).annotate(itype=Value('email', output_field=CharField()))
        sms_msgs = SMS.objects.filter(tenant=tenant).annotate(itype=Value('sms', output_field=CharField()))
        calls = CallLog.objects.filter(tenant=tenant).annotate(itype=Value('call', output_field=CharField()))
        chats = ChatMessage.objects.filter(tenant=tenant).annotate(itype=Value('chat', output_field=CharField()))
        posts = SocialMediaPost.objects.filter(tenant=tenant).annotate(itype=Value('social', output_field=CharField()))
        
        # Combine and sort by date
        combined = sorted(
            chain(emails, sms_msgs, calls, chats, posts),
            key=lambda x: (
                getattr(x, 'created_at', None) or 
                getattr(x, 'call_started_at', None) or 
                getattr(x, 'posted_at', None) or 
                getattr(x, 'received_at', None) or 
                timezone.now()
            ),
            reverse=True
        )
        return combined[:200]


# ============================================================================
# EMAIL SIGNATURE VIEWS
# ============================================================================

class EmailSignatureListView(LoginRequiredMixin, ListView):
    """List email signatures for the current user"""
    model = EmailSignature
    template_name = 'communication/signature_list.html'
    context_object_name = 'signatures'

    def get_queryset(self):
        return EmailSignature.objects.filter(user=self.request.user, tenant=self.request.user.tenant)


class EmailSignatureCreateView(LoginRequiredMixin, CreateView):
    """Create a new email signature"""
    model = EmailSignature
    form_class = EmailSignatureForm
    template_name = 'communication/signature_form.html'
    success_url = reverse_lazy('communication:signature_list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.user = self.request.user
        messages.success(self.request, 'Signature created successfully!')
        return super().form_valid(form)


class EmailSignatureUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing email signature"""
    model = EmailSignature
    form_class = EmailSignatureForm
    template_name = 'communication/signature_form.html'
    success_url = reverse_lazy('communication:signature_list')

    def get_queryset(self):
        return EmailSignature.objects.filter(user=self.request.user, tenant=self.request.user.tenant)


class EmailSignatureDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an email signature"""
    model = EmailSignature
    template_name = 'communication/signature_confirm_delete.html'
    success_url = reverse_lazy('communication:signature_list')

    def get_queryset(self):
        return EmailSignature.objects.filter(user=self.request.user, tenant=self.request.user.tenant)


from django.urls import reverse_lazy, reverse

# ============================================================================
# VOIP / CALL INTEGRATIONS
# ============================================================================

class InitiateCallView(LoginRequiredMixin, View):
    """API view to initiate a call via Wazo"""
    def post(self, request, *args, **kwargs):
        phone_number = request.POST.get('phone_number')
        if not phone_number:
            return JsonResponse({'success': False, 'error': 'Phone number required'}, status=400)
        
        try:
            from wazo import wazo_voice_service
            # We assume the user has a wazo_user_uuid set in their profile or settings
            user_uuid = getattr(request.user, 'wazo_user_uuid', None)
            
            if not user_uuid:
                # Mock for demo if not configured
                logger.warning(f"User {request.user} has no Wazo UUID. Mocking call to {phone_number}.")
                CallLog.objects.create(
                    tenant=request.user.tenant,
                    user=request.user,
                    phone_number=phone_number,
                    direction='outbound',
                    call_type='voip',
                    outcome='initiated',
                    call_started_at=timezone.now()
                )
                return JsonResponse({'success': True, 'msg': 'Simulation: Call initiated'})
            
            result = wazo_voice_service.initiate_call(user_uuid, phone_number)
            
            # Log the attempt
            CallLog.objects.create(
                tenant=request.user.tenant,
                user=request.user,
                phone_number=phone_number,
                direction='outbound',
                call_type='voip',
                outcome='initiated',
                call_started_at=timezone.now()
            )
            
            return JsonResponse({'success': True, 'call_id': result.get('uuid')})
        except Exception as e:
            logger.error(f"Failed to initiate call: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class CallRecordingView(LoginRequiredMixin, DetailView):
    """View to proxy/retrieve call recordings"""
    model = CallLog
    
    def get(self, request, *args, **kwargs):
        call_log = self.get_object()
        if not call_log.recording_id:
            return HttpResponse("No recording found", status=404)
            
        try:
            from wazo import wazo_voice_service
            recording_data = wazo_voice_service.get_call_recordings(call_log.recording_id)
            # In a real app, this would return the binary data or a signed URL
            return HttpResponse(recording_data, content_type="audio/mpeg")
        except Exception as e:
            return HttpResponse(f"Error retrieving recording: {e}", status=500)

from django.http import HttpResponse, HttpResponseRedirect
import base64

PIXEL_DATA = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')

class EmailOpenView(View):
    """Record email open event via tracking pixel"""
    def get(self, request, tracking_id):
        try:
            email = Email.objects.get(tracking_id=tracking_id)
            if not email.opened_at:
                email.opened_at = timezone.now()
                if email.status != 'opened':
                    email.status = 'opened'
                email.save()
                
                # Log engagement event for email opened
                try:
                    log_engagement_event(
                        tenant_id=email.tenant_id,
                        event_type='email_opened',
                        description=f"Email opened: {email.subject}",
                        title="Email Opened",
                        metadata={
                            'email_id': email.id,
                            'subject': email.subject,
                            'opened_at': email.opened_at.isoformat()
                        },
                        engagement_score=1,
                        created_by=email.sender
                    )
                except Exception as e:
                    logger.warning(f"Failed to log engagement event: {e}")
        except Email.DoesNotExist:
            pass
        return HttpResponse(PIXEL_DATA, content_type='image/gif')


class EmailClickView(View):
    """Record email click event and redirect to target URL"""
    def get(self, request, tracking_id):
        target_url = request.GET.get('url')
        try:
            email = Email.objects.get(tracking_id=tracking_id)
            if not email.clicked_at:
                email.clicked_at = timezone.now()
                email.save()
                
                # Log engagement event for link clicked
                try:
                    log_engagement_event(
                        tenant_id=email.tenant_id,
                        event_type='link_clicked',
                        description=f"Link clicked in email: {email.subject}",
                        title="Email Link Clicked",
                        metadata={
                            'email_id': email.id,
                            'subject': email.subject,
                            'target_url': target_url,
                            'clicked_at': email.clicked_at.isoformat()
                        },
                        engagement_score=2,
                        created_by=email.sender
                    )
                except Exception as e:
                    logger.warning(f"Failed to log engagement event: {e}")
        except Email.DoesNotExist:
            pass
        return HttpResponseRedirect(target_url or '/')


from django.db.models import Count, Sum, Avg

class CallAnalyticsView(LoginRequiredMixin, TemplateView):
    """View for call analytics dashboard"""
    template_name = 'communication/call_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Base QuerySet
        calls = CallLog.objects.filter(tenant=tenant)
        
        # Summary Stats
        context['total_calls'] = calls.count()
        context['total_duration'] = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        context['avg_duration'] = calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        
        # Breakdown by outcome
        context['outcome_breakdown'] = calls.values('outcome').annotate(count=Count('id')).order_by('-count')
        
        # Breakdown by call type
        context['type_breakdown'] = calls.values('call_type').annotate(count=Count('id')).order_by('-count')
        
        # Top Users
        context['top_users'] = calls.values('user__username', 'user__first_name', 'user__last_name').annotate(count=Count('id')).order_by('-count')[:5]
        
        # Recent calls for the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context['calls_over_time'] = calls.filter(call_started_at__gte=thirty_days_ago).extra(select={'day': "date(call_started_at)"}).values('day').annotate(count=Count('id')).order_by('day')
        
        return context


class WhatsAppSendView(LoginRequiredMixin, TemplateView):
    """View to send WhatsApp messages via Wazo with CRM entity linking."""
    template_name = 'communication/whatsapp_send.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Get WhatsApp numbers from configuration or mock
        from wazo import wazo_whatsapp_service
        context['wa_numbers'] = wazo_whatsapp_service.get_tenant_numbers(str(tenant.id))
        
        # Get contacts and leads for selection
        from accounts.models import Contact, Account
        from leads.models import Lead
        
        context['contacts'] = Contact.objects.filter(tenant=tenant).select_related('account')[:100]
        context['leads'] = Lead.objects.filter(tenant=tenant)[:100]
        context['accounts'] = Account.objects.filter(tenant=tenant)[:100]
        
        # Pre-select from query params
        context['selected_contact_id'] = self.request.GET.get('contact_id')
        context['selected_lead_id'] = self.request.GET.get('lead_id')
        context['selected_account_id'] = self.request.GET.get('account_id')
        context['prefill_number'] = self.request.GET.get('to')
        
        # Get templates for the tenant
        try:
            from .whatsapp_models import WhatsAppTemplate
            context['templates'] = WhatsAppTemplate.objects.filter(
                tenant=tenant, is_active=True, status='approved'
            )
        except Exception:
            context['templates'] = []
        
        return context

    def post(self, request, *args, **kwargs):
        from_number = request.POST.get('from_number')
        to_number = request.POST.get('to_number')
        message = request.POST.get('message')
        contact_id = request.POST.get('contact_id')
        lead_id = request.POST.get('lead_id')
        account_id = request.POST.get('account_id')
        template_name = request.POST.get('template_name')
        
        if not to_number or (not message and not template_name):
            messages.error(request, "Recipient and message (or template) are required.")
            return self.get(request, *args, **kwargs)
            
        try:
            from wazo import wazo_whatsapp_service
            from .whatsapp_models import WhatsAppMessage
            
            tenant_id = str(request.user.tenant_id)
            
            # Send message (text or template)
            if template_name:
                # Template message
                template_vars = request.POST.getlist('template_variables[]')
                result = wazo_whatsapp_service.send_template_message(
                    from_number=from_number,
                    to_number=to_number,
                    template_name=template_name,
                    template_variables=template_vars,
                    tenant_id=tenant_id
                )
            else:
                # Text message
                result = wazo_whatsapp_service.send_message(
                    from_number=from_number,
                    to_number=to_number,
                    body=message,
                    tenant_id=tenant_id
                )
            
            if result:
                # Update with CRM entity links
                try:
                    wa_message = WhatsAppMessage.objects.filter(
                        message_id=result.message_id
                    ).first()
                    
                    if wa_message:
                        if contact_id:
                            from accounts.models import Contact
                            contact = Contact.objects.filter(id=contact_id, tenant=request.user.tenant).first()
                            if contact:
                                wa_message.contact = contact
                                wa_message.account = contact.account
                        elif account_id:
                            from accounts.models import Account
                            account = Account.objects.filter(id=account_id, tenant=request.user.tenant).first()
                            if account:
                                wa_message.account = account
                        
                        if lead_id:
                            from leads.models import Lead
                            lead = Lead.objects.filter(id=lead_id, tenant=request.user.tenant).first()
                            if lead:
                                wa_message.lead = lead
                        
                        wa_message.user = request.user
                        wa_message.save()
                except Exception as e:
                    logger.warning(f"Failed to link CRM entities: {e}")
                
                # Also create ChatMessage for unified inbox compatibility
                chat_msg = ChatMessage.objects.create(
                    tenant=request.user.tenant,
                    channel='whatsapp',
                    sender_name='System / ' + request.user.username,
                    message=message or f"[Template: {template_name}]",
                    external_id=result.message_id,
                    contact_id=contact_id if contact_id else None,
                    account_id=account_id if account_id else None
                )
                
                # Log engagement event
                try:
                    log_engagement_event(
                        tenant_id=request.user.tenant_id,
                        event_type='whatsapp_sent',
                        description=f"WhatsApp message sent to {to_number}",
                        title="WhatsApp Message Sent",
                        metadata={
                            'message_id': result.message_id,
                            'to_number': to_number,
                            'from_number': from_number,
                            'message_preview': (message or template_name)[:50],
                            'contact_id': contact_id,
                            'lead_id': lead_id,
                            'account_id': account_id
                        },
                        engagement_score=2,
                        created_by=request.user
                    )
                except Exception as e:
                    logger.warning(f"Failed to log engagement event: {e}")
                
                messages.success(request, "WhatsApp message sent successfully!")
                return HttpResponseRedirect(reverse('communication:unified_inbox'))
            else:
                messages.error(request, "Failed to send WhatsApp message via Wazo.")
        except Exception as e:
            logger.error(f"WhatsApp Error: {e}")
            messages.error(request, f"WhatsApp Error: {e}")
            
        return self.get(request, *args, **kwargs)


class WhatsAppConversationView(LoginRequiredMixin, TemplateView):
    """View WhatsApp conversation thread with a contact or lead."""
    template_name = 'communication/whatsapp_conversation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        phone_number = self.kwargs.get('phone_number', self.request.GET.get('phone'))
        
        from .whatsapp_models import WhatsAppMessage
        
        # Get messages for this phone number
        messages_qs = WhatsAppMessage.objects.filter(tenant=tenant)
        
        if phone_number:
            messages_qs = messages_qs.filter(
                Q(from_number__icontains=phone_number) | 
                Q(to_number__icontains=phone_number)
            )
            context['phone_number'] = phone_number
        
        context['messages'] = messages_qs.order_by('created_at')[:100]
        
        # Try to find linked contact/lead
        if phone_number:
            normalized = phone_number[-10:] if len(phone_number) >= 10 else phone_number
            from accounts.models import Contact
            from leads.models import Lead
            
            context['contact'] = Contact.objects.filter(
                tenant=tenant, phone__icontains=normalized
            ).first()
            context['lead'] = Lead.objects.filter(
                tenant=tenant, phone__icontains=normalized
            ).first()
        
        # Get WhatsApp numbers for reply
        from wazo import wazo_whatsapp_service
        context['wa_numbers'] = wazo_whatsapp_service.get_tenant_numbers(str(tenant.id))
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Send reply message."""
        from_number = request.POST.get('from_number')
        to_number = request.POST.get('to_number')
        message = request.POST.get('message')
        
        if not to_number or not message:
            messages.error(request, "Message is required.")
            return self.get(request, *args, **kwargs)
        
        try:
            from wazo import wazo_whatsapp_service
            
            result = wazo_whatsapp_service.send_message(
                from_number=from_number,
                to_number=to_number,
                body=message,
                tenant_id=str(request.user.tenant_id)
            )
            
            if result:
                messages.success(request, "Reply sent!")
            else:
                messages.error(request, "Failed to send reply.")
                
        except Exception as e:
            logger.error(f"WhatsApp Reply Error: {e}")
            messages.error(request, f"Error: {e}")
        
        return redirect(request.path + f'?phone={to_number}')



class LinkedInInMailView(LoginRequiredMixin, TemplateView):
    """View to track LinkedIn InMail interactions"""
    template_name = 'communication/linkedin_inmail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from leads.models import Lead
        context['related_leads'] = Lead.objects.filter(tenant=self.request.user.tenant)[:10]
        return context

    def post(self, request, *args, **kwargs):
        handle = request.POST.get('linkedin_handle')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        lead_id = request.POST.get('related_lead')
        
        if not handle or not message:
            messages.error(request, "LinkedIn handle and message content are required.")
            return self.get(request, *args, **kwargs)
            
        try:
            from wazo import wazo_linkedin_service
            result = wazo_linkedin_service.track_inmail(handle)
            
            if result:
                # Log to CRM as SocialMediaPost
                social_post = SocialMediaPost.objects.create(
                    tenant=request.user.tenant,
                    platform='linkedin',
                    post_id=result.inmail_id,
                    content=f"Subject: {subject}\n\n{message}",
                    url=handle,
                    is_inmail=True,
                    lead_id=lead_id if lead_id else None,
                    posted_at=timezone.now()
                )
                
                # Log engagement event for LinkedIn InMail tracked
                try:
                    log_engagement_event(
                        tenant_id=request.user.tenant_id,
                        event_type='linkedin_inmail_tracked',
                        description=f"LinkedIn InMail tracked: {subject}",
                        title="LinkedIn InMail Tracked",
                        metadata={
                            'post_id': social_post.id,
                            'linkedin_handle': handle,
                            'subject': subject,
                            'lead_id': lead_id
                        },
                        engagement_score=3,
                        created_by=request.user
                    )
                except Exception as e:
                    logger.warning(f"Failed to log engagement event: {e}")
                
                messages.success(request, "LinkedIn InMail tracked successfully!")
                return HttpResponseRedirect(reverse('communication:unified_inbox'))
        except Exception as e:
            logger.error(f"LinkedIn Error: {e}")
            messages.error(request, f"LinkedIn Error: {e}")

        return self.get(request, *args, **kwargs)
