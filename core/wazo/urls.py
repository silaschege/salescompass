"""
Wazo URL Configuration for SalesCompass CRM.
"""
from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'wazo'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='wazo:status', permanent=False), name='index'),
    # Status
    path('status/', views.WazoStatusView.as_view(), name='status'),
    
    # Voice/Calls
    path('call/', views.InitiateCallView.as_view(), name='initiate_call'),
    path('call/<str:call_id>/hangup/', views.HangupCallView.as_view(), name='hangup_call'),
    path('calls/', views.CallHistoryView.as_view(), name='call_history'),
    
    # SMS
    path('sms/', views.SendSMSView.as_view(), name='send_sms'),
    path('sms/history/', views.SMSHistoryView.as_view(), name='sms_history'),
    
    # Webhooks (from Wazo Platform)
    path('webhooks/', views.WazoWebhookView.as_view(), name='webhooks'),
]
