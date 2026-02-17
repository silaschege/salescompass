import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .bi_services import RealTimeProcessor, DataAggregationService, MetricsCalculationService
from django.utils import timezone
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BIDashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.tenant_id = self.scope['url_route']['kwargs']['tenant_id']
        self.room_group_name = f'bi_dashboard_{self.tenant_id}'
        
        # Validate tenant
        from tenants.models import Tenant
        try:
            self.tenant = await Tenant.objects.aget(id=self.tenant_id)
        except Tenant.DoesNotExist:
            await self.close()
            return
        import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .bi_services import RealTimeProcessor, DataAggregationService, MetricsCalculationService
from django.utils import timezone
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BIDashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.tenant_id = self.scope['url_route']['kwargs']['tenant_id']
        self.room_group_name = f'bi_dashboard_{self.tenant_id}'
        
        # Validate tenant
        from tenants.models import Tenant
        try:
            self.tenant = await Tenant.objects.aget(id=self.tenant_id)
        except Tenant.DoesNotExist:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()
        
        # Start periodic updates
        self.update_task = asyncio.create_task(self.send_periodic_updates())

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Cancel the update task
        if hasattr(self, 'update_task'):
            self.update_task.cancel()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'refresh':
                await self.send_initial_data()
            elif action == 'filter':
                # Handle filter updates
                await self.handle_filter_update(data)
            elif action == 'subscribe':
                # Subscribe to specific data streams
                await self.subscribe_to_streams(data)
            elif action == 'unsubscribe':
                # Unsubscribe from specific data streams
                await self.unsubscribe_from_streams(data)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket")
            await self.send_error("Invalid JSON format")

    async def send_initial_data(self):
        """Send initial dashboard data to the client"""
        try:
            # Initialize services
            realtime_processor = RealTimeProcessor(self.tenant)
            aggregator = DataAggregationService(self.tenant)
            metrics_calculator = MetricsCalculationService(self.tenant)
            
            # Fetch real data
            leads_summary = await self.async_call(aggregator.get_leads_summary, 30)
            opportunities_summary = await self.async_call(aggregator.get_opportunities_summary, 30)
            kpis = await self.async_call(metrics_calculator.get_all_kpis, 30)
            
            # Get live data
            live_data = await self.async_call(realtime_processor.get_live_metrics)
            
            initial_data = {
                'type': 'initial_data',
                'timestamp': timezone.now().isoformat(),
                'kpis': kpis,
                'leads': leads_summary,
                'opportunities': opportunities_summary,
                'live_data': live_data
            }
            
            await self.send(text_data=json.dumps(initial_data))
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            await self.send_error("Failed to load initial data")

    async def send_periodic_updates(self):
        """Send periodic updates to the client"""
        while True:
            try:
                # Initialize services
                realtime_processor = RealTimeProcessor(self.tenant)
                
                # Fetch live data
                live_data = await self.async_call(realtime_processor.get_streaming_data)
                
                update_data = {
                    'type': 'live_update',
                    'timestamp': timezone.now().isoformat(),
                    'data': live_data
                }
                
                await self.send(text_data=json.dumps(update_data))
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending periodic updates: {e}")
                break

    async def handle_filter_update(self, data):
        """Handle filter updates from the client"""
        try:
            # Extract filters
            filters = data.get('filters', {})
            
            # In a real implementation, this would update the data based on filters
            response = {
                'type': 'filter_response',
                'message': 'Filters applied successfully',
                'filters': filters,
                'timestamp': timezone.now().isoformat()
            }
            
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            logger.error(f"Error handling filter update: {e}")
            await self.send_error("Failed to apply filters")

    async def subscribe_to_streams(self, data):
        """Subscribe to specific real-time data streams"""
        try:
            streams = data.get('streams', [])
            
            response = {
                'type': 'subscription_response',
                'message': f'Subscribed to {len(streams)} streams',
                'streams': streams,
                'timestamp': timezone.now().isoformat()
            }
            
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            logger.error(f"Error subscribing to streams: {e}")
            await self.send_error("Failed to subscribe to streams")

    async def unsubscribe_from_streams(self, data):
        """Unsubscribe from specific real-time data streams"""
        try:
            streams = data.get('streams', [])
            
            response = {
                'type': 'unsubscription_response',
                'message': f'Unsubscribed from {len(streams)} streams',
                'streams': streams,
                'timestamp': timezone.now().isoformat()
            }
            
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            logger.error(f"Error unsubscribing from streams: {e}")
            await self.send_error("Failed to unsubscribe from streams")

    async def send_error(self, message):
        """Send error message to client"""
        error_data = {
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        await self.send(text_data=json.dumps(error_data))

    async def bi_dashboard_update(self, event):
        """Handler for bi_dashboard_update messages"""
        # Send the updated data to WebSocket
        await self.send(text_data=json.dumps(event['data']))

    async def async_call(self, func, *args, **kwargs):
        """Helper method to call synchronous functions asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()
        
        # Start periodic updates
        self.update_task = asyncio.create_task(self.send_periodic_updates())

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Cancel the update task
        if hasattr(self, 'update_task'):
            self.update_task.cancel()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'refresh':
                await self.send_initial_data()
            elif action == 'filter':
                # Handle filter updates
                await self.handle_filter_update(data)
            elif action == 'subscribe':
                # Subscribe to specific data streams
                await self.subscribe_to_streams(data)
            elif action == 'unsubscribe':
                # Unsubscribe from specific data streams
                await self.unsubscribe_from_streams(data)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket")
            await self.send_error("Invalid JSON format")

    async def send_initial_data(self):
        """Send initial dashboard data to the client"""
        try:
            # Initialize services
            realtime_processor = RealTimeProcessor(self.tenant)
            aggregator = DataAggregationService(self.tenant)
            metrics_calculator = MetricsCalculationService(self.tenant)
            
            # Fetch real data
            leads_summary = await self.async_call(aggregator.get_leads_summary, 30)
            opportunities_summary = await self.async_call(aggregator.get_opportunities_summary, 30)
            kpis = await self.async_call(metrics_calculator.get_all_kpis, 30)
            
            # Get live data
            live_data = await self.async_call(realtime_processor.get_live_metrics)
            
            initial_data = {
                'type': 'initial_data',
                'timestamp': timezone.now().isoformat(),
                'kpis': kpis,
                'leads': leads_summary,
                'opportunities': opportunities_summary,
                'live_data': live_data
            }
            
            await self.send(text_data=json.dumps(initial_data))
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            await self.send_error("Failed to load initial data")

    async def send_periodic_updates(self):
        """Send periodic updates to the client"""
        while True:
            try:
                # Initialize services
                realtime_processor = RealTimeProcessor(self.tenant)
                
                # Fetch live data
                live_data = await self.async_call(realtime_processor.get_streaming_data)
                
                update_data = {
                    'type': 'live_update',
                    'timestamp': timezone.now().isoformat(),
                    'data': live_data
                }
                
                await self.send(text_data=json.dumps(update_data))
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending periodic updates: {e}")
                break

    async def handle_filter_update(self, data):
        """Handle filter updates from the client"""
        try:
            # Extract filters
            filters = data.get('filters', {})
            
            # In a real implementation, this would update the data based on filters
            response = {
                'type': 'filter_response',
                'message': 'Filters applied successfully',
                'filters': filters,
                'timestamp': timezone.now().isoformat()
            }
            
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            logger.error(f"Error handling filter update: {e}")
            await self.send_error("Failed to apply filters")

    async def subscribe_to_streams(self, data):
        """Subscribe to specific real-time data streams"""
        try:
            streams = data.get('streams', [])
            
            response = {
                'type': 'subscription_response',
                'message': f'Subscribed to {len(streams)} streams',
                'streams': streams,
                'timestamp': timezone.now().isoformat()
            }
            
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            logger.error(f"Error subscribing to streams: {e}")
            await self.send_error("Failed to subscribe to streams")

    async def unsubscribe_from_streams(self, data):
        """Unsubscribe from specific real-time data streams"""
        try:
            streams = data.get('streams', [])
            
            response = {
                'type': 'unsubscription_response',
                'message': f'Unsubscribed from {len(streams)} streams',
                'streams': streams,
                'timestamp': timezone.now().isoformat()
            }
            
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            logger.error(f"Error unsubscribing from streams: {e}")
            await self.send_error("Failed to unsubscribe from streams")

    async def send_error(self, message):
        """Send error message to client"""
        error_data = {
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        await self.send(text_data=json.dumps(error_data))

    async def bi_dashboard_update(self, event):
        """Handler for bi_dashboard_update messages"""
        # Send the updated data to WebSocket
        await self.send(text_data=json.dumps(event['data']))

    async def async_call(self, func, *args, **kwargs):
        """Helper method to call synchronous functions asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))