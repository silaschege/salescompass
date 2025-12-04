"""
Email Service for SalesCompass CRM

Provides unified email sending through multiple providers:
- SendGrid (primary)
- Django SMTP (fallback)

Supports:
- Transactional emails
- Marketing campaigns
- Drip sequences
- Template-based emails
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailProvider(Enum):
    SENDGRID = 'sendgrid'
    SMTP = 'smtp'


@dataclass
class EmailMessage:
    """Standardized email message structure."""
    to: List[str]
    subject: str
    html_content: str
    text_content: Optional[str] = None
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict]] = None
    categories: Optional[List[str]] = None
    custom_args: Optional[Dict[str, str]] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


class EmailResult:
    """Result of an email send operation."""
    
    def __init__(self, success: bool, message_id: str = None, 
                 error: str = None, provider: str = None):
        self.success = success
        self.message_id = message_id
        self.error = error
        self.provider = provider
    
    def __bool__(self):
        return self.success


class SendGridProvider:
    """SendGrid email provider."""
    
    def __init__(self):
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salescompass.io')
    
    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured."""
        return bool(self.api_key)
    
    def send(self, message: EmailMessage) -> EmailResult:
        """Send email via SendGrid API."""
        if not self.is_configured():
            return EmailResult(
                success=False,
                error='SendGrid API key not configured',
                provider='sendgrid'
            )
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import (
                Mail, Email, To, Content, Attachment, 
                Category, CustomArg, TemplateId
            )
            
            sg = SendGridAPIClient(self.api_key)
            
            mail = Mail(
                from_email=Email(message.from_email or self.from_email),
                to_emails=[To(addr) for addr in message.to],
                subject=message.subject,
            )
            
            if message.template_id:
                mail.template_id = TemplateId(message.template_id)
                if message.template_data:
                    mail.dynamic_template_data = message.template_data
            else:
                mail.add_content(Content("text/html", message.html_content))
                if message.text_content:
                    mail.add_content(Content("text/plain", message.text_content))
            
            if message.reply_to:
                mail.reply_to = Email(message.reply_to)
            
            if message.categories:
                for cat in message.categories:
                    mail.add_category(Category(cat))
            
            if message.custom_args:
                for key, value in message.custom_args.items():
                    mail.add_custom_arg(CustomArg(key, value))
            
            response = sg.send(mail)
            
            message_id = response.headers.get('X-Message-Id', '')
            
            return EmailResult(
                success=response.status_code in [200, 201, 202],
                message_id=message_id,
                provider='sendgrid'
            )
            
        except ImportError:
            return EmailResult(
                success=False,
                error='SendGrid library not installed',
                provider='sendgrid'
            )
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return EmailResult(
                success=False,
                error=str(e),
                provider='sendgrid'
            )


class SMTPProvider:
    """Django SMTP email provider (fallback)."""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salescompass.io')
    
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(getattr(settings, 'EMAIL_HOST', None))
    
    def send(self, message: EmailMessage) -> EmailResult:
        """Send email via Django SMTP."""
        try:
            text_content = message.text_content or strip_tags(message.html_content)
            
            email = EmailMultiAlternatives(
                subject=message.subject,
                body=text_content,
                from_email=message.from_email or self.from_email,
                to=message.to,
                cc=message.cc or [],
                bcc=message.bcc or [],
                reply_to=[message.reply_to] if message.reply_to else [],
            )
            
            email.attach_alternative(message.html_content, "text/html")
            
            if message.attachments:
                for attachment in message.attachments:
                    email.attach(
                        attachment['filename'],
                        attachment['content'],
                        attachment.get('mimetype', 'application/octet-stream')
                    )
            
            email.send(fail_silently=False)
            
            return EmailResult(
                success=True,
                provider='smtp'
            )
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return EmailResult(
                success=False,
                error=str(e),
                provider='smtp'
            )


class EmailService:
    """
    Unified email service with provider fallback.
    
    Usage:
        from communication.email_service import EmailService
        
        service = EmailService()
        result = service.send_email(
            to=['user@example.com'],
            subject='Welcome!',
            template='welcome_email',
            context={'name': 'John'}
        )
        
        if result.success:
            print(f"Email sent via {result.provider}")
    """
    
    def __init__(self):
        self.sendgrid = SendGridProvider()
        self.smtp = SMTPProvider()
    
    def get_active_provider(self) -> Optional[object]:
        """Get the first configured provider."""
        if self.sendgrid.is_configured():
            return self.sendgrid
        if self.smtp.is_configured():
            return self.smtp
        return None
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        template: str = None,
        html_content: str = None,
        context: Dict[str, Any] = None,
        **kwargs
    ) -> EmailResult:
        """
        Send an email using the best available provider.
        
        Args:
            to: List of recipient emails
            subject: Email subject
            template: Django template name (without extension)
            html_content: Raw HTML content (if not using template)
            context: Template context variables
            **kwargs: Additional EmailMessage fields
        
        Returns:
            EmailResult with success status and details
        """
        if template:
            html_content = render_to_string(f'{template}.html', context or {})
        
        if not html_content:
            return EmailResult(
                success=False,
                error='No content provided (template or html_content required)'
            )
        
        message = EmailMessage(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=strip_tags(html_content),
            **kwargs
        )
        
        provider = self.get_active_provider()
        
        if not provider:
            logger.warning("No email provider configured, skipping send")
            return EmailResult(
                success=False,
                error='No email provider configured'
            )
        
        result = provider.send(message)
        
        if not result.success and isinstance(provider, SendGridProvider):
            logger.info("SendGrid failed, falling back to SMTP")
            if self.smtp.is_configured():
                result = self.smtp.send(message)
        
        if result.success:
            self._log_email_sent(message, result)
        
        return result
    
    def send_template_email(
        self,
        to: List[str],
        template_id: str,
        template_data: Dict[str, Any],
        **kwargs
    ) -> EmailResult:
        """
        Send email using a SendGrid dynamic template.
        
        Args:
            to: List of recipient emails
            template_id: SendGrid template ID
            template_data: Dynamic template variables
        """
        if not self.sendgrid.is_configured():
            return EmailResult(
                success=False,
                error='SendGrid required for template emails'
            )
        
        message = EmailMessage(
            to=to,
            subject='',
            html_content='',
            template_id=template_id,
            template_data=template_data,
            **kwargs
        )
        
        return self.sendgrid.send(message)
    
    def _log_email_sent(self, message: EmailMessage, result: EmailResult) -> None:
        """Log successful email sends for tracking."""
        try:
            from core.event_bus import emit
            
            emit('email.sent', {
                'to': message.to,
                'subject': message.subject,
                'message_id': result.message_id,
                'provider': result.provider,
                'categories': message.categories or [],
                'tenant_id': message.custom_args.get('tenant_id') if message.custom_args else None,
            })
        except Exception as e:
            logger.debug(f"Failed to emit email event: {e}")


email_service = EmailService()


def send_email(to: List[str], subject: str, **kwargs) -> EmailResult:
    """Convenience function for sending emails."""
    return email_service.send_email(to, subject, **kwargs)
