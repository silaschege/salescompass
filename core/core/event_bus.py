"""
Centralized Event Bus for SalesCompass CRM

This module provides a unified event system that:
- Routes events to automation, engagement, audit logs, and reports
- Handles async/sync processing based on Celery availability
- Provides consistent event schema and validation
- Enables cross-module communication without tight coupling
"""
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class EventSchema:
    """Standard event schema with required fields."""
    
    REQUIRED_FIELDS = ['event_type', 'tenant_id', 'timestamp']
    
    @classmethod
    def validate(cls, event: Dict[str, Any]) -> bool:
        """Validate event has required fields."""
        for field in cls.REQUIRED_FIELDS:
            if field not in event:
                logger.warning(f"Event missing required field: {field}")
                return False
        return True
    
    @classmethod
    def enrich(cls, event: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich event with standard metadata."""
        enriched = event.copy()
        if 'timestamp' not in enriched:
            enriched['timestamp'] = timezone.now().isoformat()
        if 'event_id' not in enriched:
            import uuid
            enriched['event_id'] = str(uuid.uuid4())
        return enriched


class EventBus:
    """
    Central event bus for cross-module communication.
    
    Usage:
        from core.event_bus import event_bus
        
        # Emit an event
        event_bus.emit('lead.created', {
            'lead_id': 123,
            'tenant_id': 'tenant_abc',
            'lead_score': 75,
        })
        
        # Register a handler
        @event_bus.subscribe('lead.created')
        def handle_lead_created(event):
            print(f"Lead {event['lead_id']} created!")
    """
    
    # Event categories for routing
    AUTOMATION_EVENTS = [
        'lead.created', 'lead.updated', 'lead.converted',
        'opportunity.created', 'opportunity.updated', 'opportunity.stage_changed', 'opportunity.won', 'opportunity.lost',
        'account.created', 'account.updated',
        'case.created', 'case.updated', 'case.closed', 'case.escalated',
        'task.created', 'task.completed', 'task.overdue',
        'proposal.created', 'proposal.sent', 'proposal.viewed', 'proposal.accepted', 'proposal.rejected',
        'email.sent', 'email.opened', 'email.clicked', 'email.bounced',
        'call.completed', 'call.missed',
        'meeting.scheduled', 'meeting.completed',
        'nps.submitted',
    ]
    
    ENGAGEMENT_EVENTS = [
        'email.opened', 'email.clicked', 'email.sent',
        'proposal.viewed', 'proposal.downloaded',
        'call.completed',
        'meeting.scheduled', 'meeting.completed',
        'website.visited', 'document.downloaded',
        'form.submitted',
    ]
    
    AUDIT_EVENTS = [
        'user.login', 'user.logout', 'user.password_changed', 'user.mfa_enabled',
        'user.created', 'user.updated', 'user.deleted',
        'role.created', 'role.updated', 'role.deleted',
        'tenant.created', 'tenant.updated', 'tenant.suspended',
        'subscription.created', 'subscription.cancelled', 'subscription.upgraded',
        'data.exported', 'data.imported', 'data.deleted',
        'settings.changed',
        'api_key.created', 'api_key.revoked',
    ]
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._middleware: List[Callable] = []
    
    def subscribe(self, event_type: str):
        """Decorator to subscribe a handler to an event type."""
        def decorator(func: Callable):
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(func)
            return func
        return decorator
    
    def add_middleware(self, middleware: Callable):
        """Add middleware that processes all events."""
        self._middleware.append(middleware)
    
    def emit(self, event_type: str, payload: Dict[str, Any], 
             async_execution: bool = None) -> None:
        """
        Emit an event to all registered handlers.
        
        Args:
            event_type: Type of event (e.g., 'lead.created')
            payload: Event data (must include tenant_id)
            async_execution: Override async setting (None = use settings)
        """
        event = {
            'event_type': event_type,
            **payload,
        }
        event = EventSchema.enrich(event)
        
        if not EventSchema.validate(event):
            logger.error(f"Invalid event schema for {event_type}")
            return
        
        for middleware in self._middleware:
            try:
                event = middleware(event)
                if event is None:
                    return
            except Exception as e:
                logger.error(f"Middleware error: {e}")
        
        should_async = async_execution if async_execution is not None else getattr(
            settings, 'EVENT_BUS_ASYNC', False
        )
        
        if should_async and not getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', True):
            self._emit_async(event)
        else:
            self._emit_sync(event)
    
    def _emit_sync(self, event: Dict[str, Any]) -> None:
        """Synchronously dispatch event to handlers."""
        event_type = event['event_type']
        
        self._dispatch_to_automation(event)
        self._dispatch_to_engagement(event)
        self._dispatch_to_audit_log(event)
        self._dispatch_to_handlers(event)
        
        logger.debug(f"Event emitted: {event_type}")
    
    def _emit_async(self, event: Dict[str, Any]) -> None:
        """Asynchronously dispatch event via Celery."""
        try:
            from core.tasks import process_event_task
            process_event_task.delay(event)
        except ImportError:
            logger.warning("Celery task not available, falling back to sync")
            self._emit_sync(event)
        except Exception as e:
            logger.error(f"Async event dispatch failed: {e}, falling back to sync")
            self._emit_sync(event)
    
    def _dispatch_to_automation(self, event: Dict[str, Any]) -> None:
        """Route event to automation engine if applicable."""
        event_type = event['event_type']
        if event_type in self.AUTOMATION_EVENTS:
            try:
                from automation.utils import emit_event as automation_emit
                automation_emit(event_type, event)
            except ImportError:
                logger.debug("Automation module not available")
            except Exception as e:
                logger.error(f"Automation dispatch error: {e}")
    
    def _dispatch_to_engagement(self, event: Dict[str, Any]) -> None:
        """Route event to engagement tracking if applicable."""
        event_type = event['event_type']
        if event_type in self.ENGAGEMENT_EVENTS:
            try:
                from engagement.utils import log_engagement_event
                log_engagement_event(
                    event_type=self._map_to_engagement_type(event_type),
                    tenant_id=event.get('tenant_id'),
                    account_id=event.get('account_id'),
                    contact_id=event.get('contact_id'),
                    metadata=event
                )
            except ImportError:
                logger.debug("Engagement module not available")
            except Exception as e:
                logger.error(f"Engagement dispatch error: {e}")
    
    def _dispatch_to_audit_log(self, event: Dict[str, Any]) -> None:
        """Route event to audit logging if applicable."""
        event_type = event['event_type']
        if event_type not in self.AUDIT_EVENTS:
            return
            
        try:
            from audit_logs.models import AuditLog
            
            severity = 'info'
            if 'deleted' in event_type or 'revoked' in event_type:
                severity = 'warning'
            if 'suspended' in event_type:
                severity = 'critical'
            
            parts = event_type.split('.', 1)
            resource_type = parts[0] if parts else 'unknown'
            action = parts[1] if len(parts) > 1 else 'unknown'
            
            AuditLog.log_action(
                user=event.get('user'),
                action_type=event_type.upper().replace('.', '_'),
                resource_type=resource_type.capitalize(),
                resource_id=str(event.get(f'{resource_type}_id', '')),
                description=event.get('description', f'{action} {resource_type}'),
                severity=severity,
                state_before=event.get('state_before'),
                state_after=event.get('state_after'),
                ip_address=event.get('ip_address', '0.0.0.0'),
                user_agent=event.get('user_agent', ''),
            )
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Audit log dispatch error (non-fatal): {e}")
    
    def _dispatch_to_handlers(self, event: Dict[str, Any]) -> None:
        """Dispatch to custom registered handlers."""
        event_type = event['event_type']
        handlers = self._handlers.get(event_type, [])
        
        wildcard_handlers = self._handlers.get('*', [])
        handlers = handlers + wildcard_handlers
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")
    
    def _map_to_engagement_type(self, event_type: str) -> str:
        """Map event type to engagement event type."""
        mapping = {
            'email.opened': 'email_open',
            'email.clicked': 'email_click',
            'email.sent': 'email_sent',
            'proposal.viewed': 'proposal_view',
            'proposal.downloaded': 'document_download',
            'call.completed': 'call',
            'meeting.scheduled': 'meeting_scheduled',
            'meeting.completed': 'meeting',
            'website.visited': 'website_visit',
            'document.downloaded': 'document_download',
            'form.submitted': 'form_submission',
        }
        return mapping.get(event_type, event_type)


event_bus = EventBus()


def emit(event_type: str, payload: Dict[str, Any], **kwargs) -> None:
    """Convenience function to emit events."""
    event_bus.emit(event_type, payload, **kwargs)
