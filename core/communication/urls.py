from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Dashboard
    path('', views.CommunicationDashboardView.as_view(), name='dashboard'),
    
    # Notification Templates
    path('templates/', views.NotificationTemplateListView.as_view(), name='template_list'),
    path('templates/<int:pk>/', views.NotificationTemplateDetailView.as_view(), name='template_detail'),
    path('templates/create/', views.NotificationTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.NotificationTemplateUpdateView.as_view(), name='template_edit'),
    path('templates/<int:pk>/delete/', views.NotificationTemplateDeleteView.as_view(), name='template_delete'),
    
    # Email/SMS Service Configuration
    path('config/', views.EmailSMSConfigListView.as_view(), name='config_list'),
    path('config/create/', views.EmailSMSConfigCreateView.as_view(), name='config_create'),
    path('config/<int:pk>/edit/', views.EmailSMSConfigUpdateView.as_view(), name='config_edit'),
    
    # Communication History
    path('history/', views.CommunicationHistoryListView.as_view(), name='history_list'),
    path('history/<int:pk>/', views.CommunicationHistoryDetailView.as_view(), name='history_detail'),
    
    # Support Tickets
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/create/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<int:pk>/edit/', views.TicketUpdateView.as_view(), name='ticket_edit'),
    
    # Feedback & Surveys
    path('feedback/', views.FeedbackListView.as_view(), name='feedback_list'),
    path('feedback/create/', views.FeedbackCreateView.as_view(), name='feedback_create'),
    
    # Emails
    path('emails/', views.EmailListView.as_view(), name='email_list'),
    path('emails/compose/', views.EmailComposeView.as_view(), name='email_compose'),
    
    # SMS
    path('sms/', views.SMSListView.as_view(), name='sms_list'),
    path('sms/send/', views.SMSSendView.as_view(), name='sms_send'),
    
    # Call Logs
    path('calls/', views.CallLogListView.as_view(), name='call_log_list'),
    path('calls/<int:pk>/', views.CallLogDetailView.as_view(), name='call_log_detail'),
    path('calls/log/', views.CallLogCreateView.as_view(), name='call_log_create'),
    path('calls/analytics/', views.CallAnalyticsView.as_view(), name='call_analytics'),
    path('calls/initiate/', views.InitiateCallView.as_view(), name='call_initiate'),
    path('calls/<int:pk>/recording/', views.CallRecordingView.as_view(), name='call_recording'),
    
    # Unified Inbox
    path('inbox/', views.UnifiedInboxView.as_view(), name='unified_inbox'),
    
    # Omni-Channel
    path('whatsapp/send/', views.WhatsAppSendView.as_view(), name='whatsapp_send'),
    path('whatsapp/conversation/', views.WhatsAppConversationView.as_view(), name='whatsapp_conversation'),
    # WhatsApp Templates
    path('whatsapp/templates/', views.WhatsAppTemplateListView.as_view(), name='whatsapp_template_list'),
    path('whatsapp/templates/create/', views.WhatsAppTemplateCreateView.as_view(), name='whatsapp_template_create'),
    path('whatsapp/templates/<int:pk>/edit/', views.WhatsAppTemplateUpdateView.as_view(), name='whatsapp_template_edit'),
    path('whatsapp/templates/<int:pk>/delete/', views.WhatsAppTemplateDeleteView.as_view(), name='whatsapp_template_delete'),
    
    path('linkedin/inmail/', views.LinkedInInMailView.as_view(), name='linkedin_inmail'),
    
    # Email Signatures
    path('signatures/', views.EmailSignatureListView.as_view(), name='signature_list'),
    path('signatures/create/', views.EmailSignatureCreateView.as_view(), name='signature_create'),
    path('signatures/<int:pk>/edit/', views.EmailSignatureUpdateView.as_view(), name='signature_edit'),
    path('signatures/<int:pk>/delete/', views.EmailSignatureDeleteView.as_view(), name='signature_delete'),

    # Tracking
    path('track/open/<str:tracking_id>/', views.EmailOpenView.as_view(), name='email_track_open'),
    path('track/click/<str:tracking_id>/', views.EmailClickView.as_view(), name='email_track_click'),
    
    # Twilio Webhooks
    path('webhooks/twilio/whatsapp/', 
         __import__('communication.twilio_webhooks', fromlist=['TwilioWhatsAppWebhookView']).TwilioWhatsAppWebhookView.as_view(), 
         name='twilio_whatsapp_webhook'),
]

