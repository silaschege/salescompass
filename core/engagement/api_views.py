from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import EngagementEvent, NextBestAction, EngagementStatus, EngagementWebhook
from .serializers import (
    EngagementEventSerializer, 
    NextBestActionSerializer, 
    EngagementStatusSerializer,
    BulkEngagementEventSerializer,
    EngagementWebhookSerializer
)
from core.permissions import HasPermission


class EngagementEventListCreateAPIView(generics.ListCreateAPIView):
    """
    List all engagement events or create a new engagement event.
    """
    serializer_class = EngagementEventSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.view_engagementevent'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'account', 'priority', 'is_important']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'engagement_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return EngagementEvent.objects.filter(tenant_id=user.tenant_id)
        return EngagementEvent.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            serializer.save(tenant_id=user.tenant_id)


class EngagementEventDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an engagement event.
    """
    serializer_class = EngagementEventSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.view_engagementevent'
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return EngagementEvent.objects.filter(tenant_id=user.tenant_id)
        return EngagementEvent.objects.none()


class BulkEngagementEventCreateAPIView(APIView):
    """
    Create multiple engagement events in a single request.
    """
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.add_engagementevent'
    
    def post(self, request):
        serializer = BulkEngagementEventSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.create(serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return EngagementEvent.objects.filter(tenant_id=user.tenant_id)
        return EngagementEvent.objects.none()


class NextBestActionListCreateAPIView(generics.ListCreateAPIView):
    """
    List all next best actions or create a new next best action.
    """
    serializer_class = NextBestActionSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.view_nextbestaction'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'account', 'priority', 'completed']
    search_fields = ['description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-due_date']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return NextBestAction.objects.filter(tenant_id=user.tenant_id)
        return NextBestAction.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            serializer.save(tenant_id=user.tenant_id)


class NextBestActionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a next best action.
    """
    serializer_class = NextBestActionSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.view_nextbestaction'
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return NextBestAction.objects.filter(tenant_id=user.tenant_id)
        return NextBestAction.objects.none()


class EngagementStatusListAPIView(generics.ListAPIView):
    """
    List all engagement statuses.
    """
    serializer_class = EngagementStatusSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.view_engagementstatus'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['account__name']
    ordering_fields = ['engagement_score', 'last_engaged_at']
    ordering = ['-engagement_score']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return EngagementStatus.objects.filter(account__tenant_id=user.tenant_id)
        return EngagementStatus.objects.none()


class EngagementWebhookListCreateAPIView(generics.ListCreateAPIView):
    """
    List all engagement webhooks or create a new engagement webhook.
    """
    serializer_class = EngagementWebhookSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.view_engagementwebhook'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['engagement_webhook_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return EngagementWebhook.objects.filter(tenant_id=user.tenant_id)
        return EngagementWebhook.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            serializer.save(tenant_id=user.tenant_id)


class EngagementWebhookDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an engagement webhook.
    """
    serializer_class = EngagementWebhookSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = 'engagement.view_engagementwebhook'
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'tenant_id'):
            return EngagementWebhook.objects.filter(tenant_id=user.tenant_id)
        return EngagementWebhook.objects.none()
