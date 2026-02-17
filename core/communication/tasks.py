import logging
from celery import shared_task
from django.utils import timezone
from .models import Email
from .email_service import email_service

logger = logging.getLogger(__name__)

@shared_task
def send_scheduled_emails():
    """
    Task to send emails that were scheduled and are due.
    """
    due_emails = Email.objects.filter(
        status='queued',
        send_at__lte=timezone.now()
    )
    
    count = due_emails.count()
    if count > 0:
        logger.info(f"Processing {count} scheduled emails")
        for email in due_emails:
            try:
                # We'll implement a method in email_service to handle the actual sending
                # given an Email model instance.
                email_service.send_model_email(email)
            except Exception as e:
                logger.error(f"Failed to send scheduled email {email.id}: {e}")
    return f"Processed {count} emails"
