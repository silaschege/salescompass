"""
Microsoft Teams Service for SalesCompass CRM

Provides integration with Microsoft Teams for:
- Sending notifications via webhooks
- Channel messaging
- Adaptive Card support

Usage:
    from communication.teams_service import teams_service
    
    result = teams_service.send_message(
        webhook_url='https://outlook.office.com/webhook/...',
        title='New Lead Created',
        message='A new lead has been submitted.',
        facts={'Name': 'John Doe', 'Email': 'john@example.com'}
    )
"""

import logging
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class TeamsMessageResult:
    """Result of a Teams message send operation."""
    success: bool
    error: Optional[str] = None
    
    def __bool__(self):
        return self.success


class TeamsService:
    """
    Microsoft Teams webhook integration service.
    
    Supports both simple text messages and rich Adaptive Cards.
    """
    
    def __init__(self):
        self.default_webhook_url = getattr(settings, 'TEAMS_WEBHOOK_URL', None)
        self.timeout = getattr(settings, 'TEAMS_WEBHOOK_TIMEOUT', 10)
    
    def is_configured(self) -> bool:
        """Check if Teams is configured with a default webhook URL."""
        return bool(self.default_webhook_url)
    
    def send_message(
        self,
        webhook_url: str = None,
        title: str = None,
        message: str = None,
        facts: Dict[str, str] = None,
        theme_color: str = "0076D7",  # Default blue
        sections: List[Dict] = None,
        potential_action: List[Dict] = None,
    ) -> TeamsMessageResult:
        """
        Send a message to Microsoft Teams via webhook.
        
        Args:
            webhook_url: Teams webhook URL (uses default if not provided)
            title: Card title
            message: Main message text
            facts: Key-value pairs to display as facts
            theme_color: Hex color for the card accent
            sections: Additional card sections
            potential_action: Action buttons (OpenUri, etc.)
        
        Returns:
            TeamsMessageResult with success status
        """
        url = webhook_url or self.default_webhook_url
        
        if not url:
            logger.error("No Teams webhook URL provided")
            return TeamsMessageResult(success=False, error="No webhook URL configured")
        
        try:
            # Build the message card
            card = self._build_message_card(
                title=title,
                message=message,
                facts=facts,
                theme_color=theme_color,
                sections=sections,
                potential_action=potential_action
            )
            
            response = requests.post(
                url,
                json=card,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Teams message sent successfully: {title}")
                return TeamsMessageResult(success=True)
            else:
                error_msg = f"Teams webhook returned {response.status_code}: {response.text}"
                logger.error(error_msg)
                return TeamsMessageResult(success=False, error=error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Teams webhook request timed out"
            logger.error(error_msg)
            return TeamsMessageResult(success=False, error=error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Teams webhook request failed: {str(e)}"
            logger.error(error_msg)
            return TeamsMessageResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error sending Teams message: {str(e)}"
            logger.error(error_msg)
            return TeamsMessageResult(success=False, error=error_msg)
    
    def _build_message_card(
        self,
        title: str = None,
        message: str = None,
        facts: Dict[str, str] = None,
        theme_color: str = "0076D7",
        sections: List[Dict] = None,
        potential_action: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Build a MessageCard format payload for Teams."""
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title or message or "SalesCompass Notification",
        }
        
        if title:
            card["title"] = title
        
        if message or facts:
            section = {}
            if message:
                section["activityTitle"] = message
            if facts:
                section["facts"] = [
                    {"name": k, "value": str(v)} 
                    for k, v in facts.items()
                ]
            card["sections"] = [section]
        
        if sections:
            card["sections"] = card.get("sections", []) + sections
        
        if potential_action:
            card["potentialAction"] = potential_action
        
        return card
    
    def send_adaptive_card(
        self,
        webhook_url: str = None,
        card_body: List[Dict] = None,
        card_actions: List[Dict] = None,
    ) -> TeamsMessageResult:
        """
        Send an Adaptive Card to Microsoft Teams.
        
        Args:
            webhook_url: Teams webhook URL
            card_body: Adaptive Card body elements
            card_actions: Adaptive Card action buttons
        
        Returns:
            TeamsMessageResult with success status
        """
        url = webhook_url or self.default_webhook_url
        
        if not url:
            return TeamsMessageResult(success=False, error="No webhook URL configured")
        
        try:
            payload = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "contentUrl": None,
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.4",
                            "body": card_body or [],
                            "actions": card_actions or []
                        }
                    }
                ]
            }
            
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return TeamsMessageResult(success=True)
            else:
                error_msg = f"Teams webhook returned {response.status_code}"
                return TeamsMessageResult(success=False, error=error_msg)
                
        except Exception as e:
            return TeamsMessageResult(success=False, error=str(e))
    
    def send_workflow_notification(
        self,
        webhook_url: str,
        workflow_name: str,
        event_type: str,
        details: Dict[str, Any] = None,
        status: str = "info",
    ) -> TeamsMessageResult:
        """
        Send a workflow-specific notification to Teams.
        
        Args:
            webhook_url: Teams webhook URL
            workflow_name: Name of the workflow
            event_type: Type of event (e.g., 'execution_completed', 'approval_required')
            details: Additional details to include
            status: 'info', 'success', 'warning', or 'error'
        """
        status_colors = {
            "info": "0076D7",     # Blue
            "success": "00C853",  # Green
            "warning": "FFB300",  # Amber
            "error": "D32F2F",    # Red
        }
        
        theme_color = status_colors.get(status, "0076D7")
        
        facts = {"Event": event_type}
        if details:
            facts.update({k: str(v) for k, v in details.items()})
        
        return self.send_message(
            webhook_url=webhook_url,
            title=f"SalesCompass: {workflow_name}",
            message=f"Workflow event: {event_type}",
            facts=facts,
            theme_color=theme_color,
        )


# Singleton instance
teams_service = TeamsService()


def send_teams_message(webhook_url: str, title: str, message: str, **kwargs) -> TeamsMessageResult:
    """Convenience function for sending Teams messages."""
    return teams_service.send_message(
        webhook_url=webhook_url,
        title=title,
        message=message,
        **kwargs
    )
