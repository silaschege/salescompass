import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import EngagementEvent, EngagementStatus



class EngagementFeedConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time engagement feed."""
    
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user_id = self.scope["user"].id
        self.tenant_id = self.scope["user"].tenant_id
        self.feed_group_name = f"engagement_feed_{self.tenant_id}"
        self.alerts_group_name = f"engagement_alerts_{self.tenant_id}"
        
        # Add to feed group
        await self.channel_layer.group_add(
            self.feed_group_name,
            self.channel_name
        )
        
        # Add to alerts group
        await self.channel_layer.group_add(
            self.alerts_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial events
        events = await self.get_engagement_events()
        for event in events:
            await self.send(text_data=json.dumps({
                'type': 'engagement_event',
                'data': event
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.feed_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.alerts_group_name,
            self.channel_name
        )

    async def engagement_event(self, event):
        """Receive engagement event from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'engagement_event',
            'data': event["data"]
        }))

    async def engagement_alert(self, event):
        """Receive engagement alert from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'engagement_alert',
            'data': event["data"]
        }))

    @database_sync_to_async
    def get_engagement_events(self):
        from .models import EngagementEvent
        events = EngagementEvent.objects.filter(
            tenant_id=self.scope["user"].tenant_id
        ).order_by('-created_at')[:10]
        
        return [event.get_event_data_for_websocket() for event in events]


def broadcast_engagement_event(event):
    """Broadcast engagement event to WebSocket group."""
    
    channel_layer = get_channel_layer()
    
    # Broadcast to engagement feed
    async_to_sync(channel_layer.group_send)(
        f"engagement_feed_{event.tenant_id}",
        {
            "type": "engagement.event",
            "data": event.get_event_data_for_websocket()
        }
    )
    
    # Check for critical events to send alerts
    if event.is_important or event.engagement_score < 20 or event.event_type in ['nps_submitted', 'case_escalation_handled']:
        async_to_sync(channel_layer.group_send)(
            f"engagement_alerts_{event.tenant_id}",
            {
                "type": "engagement.alert",
                "data": {
                    "id": event.id,
                    "account_name": event.account.name if event.account else "Unknown",
                    "title": event.title or f'{event.get_event_type_display()} Event',
                    "event_type": event.get_event_type_display(),
                    "engagement_score": event.engagement_score,
                    "is_important": event.is_important,
                    "priority": event.priority,
                    "created_at": event.created_at.isoformat(),
                    "alert_type": "critical_event",
                    "message": f"Critical event: {event.title or event.get_event_type_display()} for {event.account.name if event.account else 'Unknown'}"
                }
            }
        )
    
    # Check for engagement drops
    if hasattr(event, 'account') and event.account:
        check_engagement_drop(event.account, event.tenant_id)


def check_engagement_drop(account, tenant_id):
    """Check if account has experienced a significant engagement drop."""
    try:
        status = EngagementStatus.objects.get(account=account)
        
        # If score dropped significantly, send alert
        if status.engagement_score < 30 and hasattr(status, '_previous_score') and status._previous_score >= 50:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"engagement_alerts_{tenant_id}",
                {
                    "type": "engagement.alert",
                    "data": {
                        "account_name": account.name,
                        "title": "Engagement Drop Detected",
                        "event_type": "engagement_drop",
                        "engagement_score": status.engagement_score,
                        "is_important": True,
                        "priority": "high",
                        "message": f"Engagement score for {account.name} dropped to {status.engagement_score}",
                        "alert_type": "engagement_drop",
                        "account_id": account.id
                    }
                }
            )
    except EngagementStatus.DoesNotExist:
        pass