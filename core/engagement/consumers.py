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

        # Use tenant-based group for shared feed
        self.tenant_id = getattr(self.scope["user"], 'tenant_id', None)
        if not self.tenant_id:
            await self.close()
            return

        self.group_name = f"engagement_feed_tenant_{self.tenant_id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial events (async wrapper needed for ORM)
        await self.send_initial_events()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def engagement_event(self, event):
        """Receive engagement event from channel layer."""
        await self.send(text_data=json.dumps(event["data"]))

    async def send_initial_events(self):
        events_data = await self.get_engagement_events()
        for event_data in events_data:
            await self.send(text_data=json.dumps(event_data))

    @database_sync_to_async
    def get_engagement_events(self):
        from .models import EngagementEvent
        events = EngagementEvent.objects.filter(
            tenant_id=self.tenant_id
        ).order_by('-created_at')[:10]
        
        # We need to reverse so they append correctly in UI timeline usually, 
        # but let's stick to simple list for now.
        return [event.get_event_data_for_websocket() for event in reversed(events)]


def broadcast_engagement_event(event):
    """Broadcast engagement event to WebSocket group."""
    tenant_id = getattr(event, 'tenant_id', None)
    if not tenant_id:
        return

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"engagement_feed_tenant_{tenant_id}",
        {
            "type": "engagement.event",
            "data": event.get_event_data_for_websocket()
        }
    )