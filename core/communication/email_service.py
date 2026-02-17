import logging
import re
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from urllib.parse import urlencode

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
    tracking_id: Optional[str] = None


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
            
            if message.tracking_id:
                if not message.custom_args:
                    message.custom_args = {}
                message.custom_args['tracking_id'] = message.tracking_id
            
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
    Unified email service with provider fallback, scheduling and tracking.
    """
    
    def __init__(self):
        self.sendgrid = SendGridProvider()
        self.smtp = SMTPProvider()
        self.base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    def get_active_provider(self) -> Optional[object]:
        """Get the first configured provider."""
        if self.sendgrid.is_configured():
            return self.sendgrid
        if self.smtp.is_configured():
            return self.smtp
        return None

    def _inject_tracking_pixel(self, html_content: str, tracking_id: str) -> str:
        """Inject an invisible image for open tracking."""
        pixel_url = f"{self.base_url}/communication/track/open/{tracking_id}/"
        pixel_img = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />'
        
        if '</body>' in html_content:
            return html_content.replace('</body>', f'{pixel_img}</body>')
        return html_content + pixel_img

    def _wrap_links(self, html_content: str, tracking_id: str) -> str:
        """Wrap all links for click tracking."""
        def replace_link(match):
            original_url = match.group(2)
            # Skip non-http links or already tracked links
            if not original_url.startswith('http') or '/track/click/' in original_url:
                return match.group(0)
            
            tracking_url = f"{self.base_url}/communication/track/click/{tracking_id}/?{urlencode({'url': original_url})}"
            return f'href="{tracking_url}"'

        return re.sub(r'href=(["\'])(.*?)\1', replace_link, html_content)

    def send_model_email(self, email_instance) -> EmailResult:
        """Send an email based on an Email model instance."""
        from .models import Email
        
        if email_instance.status == 'sent':
            return EmailResult(success=True, error='Email already sent')

        tracking_id = email_instance.tracking_id or str(uuid.uuid4())
        email_instance.tracking_id = tracking_id
        
        html_content = email_instance.content_html
        
        # Append signature if not present and available
        if email_instance.sender:
            from .models import EmailSignature
            default_sig = EmailSignature.objects.filter(user=email_instance.sender, is_default=True).first()
            if default_sig and default_sig.content_html not in html_content:
                html_content += f'<br><br>---<br>{default_sig.content_html}'

        if email_instance.tracking_enabled:
            html_content = self._inject_tracking_pixel(html_content, tracking_id)
            html_content = self._wrap_links(html_content, tracking_id)
        
        message = EmailMessage(
            to=email_instance.recipients,
            subject=email_instance.subject,
            html_content=html_content,
            text_content=email_instance.content_text or strip_tags(html_content),
            from_email=email_instance.sender.email if email_instance.sender else None,
            reply_to=email_instance.reply_to_email if email_instance.is_reply_to_different else None,
            cc=email_instance.cc,
            bcc=email_instance.bcc,
            tracking_id=tracking_id
        )
        
        email_instance.status = 'sending'
        email_instance.save()
        
        result = self.send_email_message(message)
        
        if result.success:
            email_instance.status = 'sent'
            email_instance.sent_at = timezone.now()
            email_instance.service_used = result.provider
            email_instance.save()
        else:
            email_instance.status = 'failed'
            email_instance.error_message = result.error
            email_instance.save()
            
        return result

    def send_email_message(self, message: EmailMessage) -> EmailResult:
        """Send an EmailMessage standardized object."""
        provider = self.get_active_provider()
        
        if not provider:
            logger.warning("No email provider configured, skipping send")
            return EmailResult(success=False, error='No email provider configured')
        
        result = provider.send(message)
        
        if not result.success and isinstance(provider, SendGridProvider):
            logger.info("SendGrid failed, falling back to SMTP")
            if self.smtp.is_configured():
                result = self.smtp.send(message)
        
        if result.success:
            self._log_email_sent(message, result)
        
        return result

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
        Legacy/Convenience method for sending emails.
        """
        if template:
            html_content = render_to_string(f'{template}.html', context or {})
        
        if not html_content:
            return EmailResult(success=False, error='No content provided')
        
        message = EmailMessage(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=strip_tags(html_content),
            **kwargs
        )
        
        return self.send_email_message(message)
    
    def _log_email_sent(self, message: EmailMessage, result: EmailResult) -> None:
        """Log successful email sends for tracking."""
        try:
            from core.event_bus import event_bus
            
            event_bus.emit('email.sent', {
                'to': message.to,
                'subject': message.subject,
                'message_id': result.message_id,
                'provider': result.provider,
                'tracking_id': message.tracking_id,
            })
        except Exception as e:
            logger.debug(f"Failed to emit email event: {e}")


email_service = EmailService()


def send_email(to: List[str], subject: str, **kwargs) -> EmailResult:
    """Convenience function for sending emails."""
    return email_service.send_email(to, subject, **kwargs)
