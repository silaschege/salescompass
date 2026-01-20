from django.urls import path
from . import views

# No app_name namespace for legacy global URLs

urlpatterns = [
    # Legacy alias for Unified Inbox
    path('conversations/legacy/', views.UnifiedInboxView.as_view(), name='conversation_list'),
]
