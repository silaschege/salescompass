from rest_framework import serializers
from .models import EngagementEvent, NextBestAction, EngagementStatus, EngagementWebhook
from core.models import User as Account
from opportunities.models import Opportunity
from accounts.models import Contact
from cases.models import Case
from nps.models import NpsResponse

 
class EngagementEventSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    opportunity_name = serializers.CharField(source='opportunity.name', read_only=True)
    contact_name = serializers.CharField(source='contact.get_full_name', read_only=True)
    
    class Meta:
        model = EngagementEvent
        fields = '__all__'
        read_only_fields = ('tenant_id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        # Set tenant_id from context
        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'tenant_id'):
            validated_data['tenant_id'] = request.user.tenant_id
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Ensure tenant_id is not changed
        validated_data.pop('tenant_id', None)
        return super().update(instance, validated_data)


class NextBestActionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    opportunity_name = serializers.CharField(source='opportunity.name', read_only=True)
    contact_name = serializers.CharField(source='contact.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = NextBestAction
        fields = '__all__'
        read_only_fields = ('tenant_id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        # Set tenant_id from context
        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'tenant_id'):
            validated_data['tenant_id'] = request.user.tenant_id
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Ensure tenant_id is not changed
        validated_data.pop('tenant_id', None)
        return super().update(instance, validated_data)


class EngagementStatusSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = EngagementStatus
        fields = '__all__'
        read_only_fields = ('tenant_id', 'created_at', 'updated_at')


class BulkEngagementEventSerializer(serializers.Serializer):
    events = EngagementEventSerializer(many=True)
    
    def create(self, validated_data):
        events_data = validated_data.get('events', [])
        events = []
        for event_data in events_data:
            serializer = EngagementEventSerializer(data=event_data, context=self.context)
            if serializer.is_valid():
                event = serializer.save()
                events.append(event)
        return {'events': events}


class EngagementWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngagementWebhook
        fields = '__all__'
        read_only_fields = ('tenant_id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        # Set tenant_id from context
        request = self.context.get('request')
        if request and hasattr(request, 'user') and hasattr(request.user, 'tenant_id'):
            validated_data['tenant_id'] = request.user.tenant_id
        return super().create(validated_data)
