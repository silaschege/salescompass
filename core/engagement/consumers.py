import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync



class EngagementFeedConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time engagement feed."""
    
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user_id = self.scope["user"].id
        self.group_name = f"engagement_feed_{self.user_id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial events
        events = await self.get_engagement_events()
        for event in events:
            await self.send(text_data=json.dumps(event))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def engagement_event(self, event):
        """Receive engagement event from channel layer."""
        await self.send(text_data=json.dumps(event["data"]))

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
    async_to_sync(channel_layer.group_send)(
        f"engagement_feed_{event.user_id if event.user_id else 'all'}",
        {
            "type": "engagement.event",
            "data": {
                "id": event.id,
                "account_name": event.account.name,
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "created_at": event.created_at.isoformat(),
                "is_important": event.is_important,
                "engagement_score": event.engagement_score,
            }
        }
    )