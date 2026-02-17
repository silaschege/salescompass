from celery import shared_task
from django.utils import timezone
from .models import DripEnrollment, DripStep
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)
 
@shared_task
def process_drip_enrollments():
    """
    Process all active drip enrollments that are due for execution.
    """
    now = timezone.now()
    enrollments = DripEnrollment.objects.filter(
        status='active',
        next_execution_at__lte=now
    ).select_related('current_step', 'drip_campaign', 'account')

    if enrollments.exists():
        logger.info(f"Processing {enrollments.count()} drip enrollments")

    for enrollment in enrollments:
        try:
            process_single_enrollment(enrollment)
        except Exception as e:
            logger.error(f"Error processing enrollment {enrollment.id}: {e}")

def process_single_enrollment(enrollment):
    step = enrollment.current_step
    
    # If no step assigned (just started), get first step
    if not step:
        first_step = enrollment.drip_campaign.steps.order_by('order').first()
        if not first_step:
            enrollment.status = 'completed'
            enrollment.save()
            return
        
        enrollment.current_step = first_step
        # If first step is wait, schedule it. If email, execute immediately.
        if first_step.step_type == 'wait':
            enrollment.next_execution_at = timezone.now() + timezone.timedelta(days=first_step.wait_days, hours=first_step.wait_hours)
            enrollment.save()
            return
        else:
            # Execute immediately
            step = first_step

    # Execute current step (if it's an action step like email)
    if step.step_type == 'email':
        # Send email
        if step.email_template:
            send_drip_email(enrollment, step)
            
        # Move to next step
        next_step = DripStep.objects.filter(
            drip_campaign=enrollment.drip_campaign,
            order__gt=step.order
        ).order_by('order').first()
        
        if next_step:
            enrollment.current_step = next_step
            if next_step.step_type == 'wait':
                enrollment.next_execution_at = timezone.now() + timezone.timedelta(days=next_step.wait_days, hours=next_step.wait_hours)
            else:
                enrollment.next_execution_at = timezone.now() # Execute next email immediately
        else:
            enrollment.status = 'completed'
            enrollment.next_execution_at = None
        
        enrollment.save()

    elif step.step_type == 'wait':
        # If we are here, it means the wait time has passed
        # So we just move to the next step
        next_step = DripStep.objects.filter(
            drip_campaign=enrollment.drip_campaign,
            order__gt=step.order
        ).order_by('order').first()
        
        if next_step:
            enrollment.current_step = next_step
            if next_step.step_type == 'wait':
                 enrollment.next_execution_at = timezone.now() + timezone.timedelta(days=next_step.wait_days, hours=next_step.wait_hours)
            else:
                enrollment.next_execution_at = timezone.now()
        else:
            enrollment.status = 'completed'
            enrollment.next_execution_at = None
            
        enrollment.save()

def send_drip_email(enrollment, step):
    """
    Send email for a drip step.
    """
    template = step.email_template
    if not template:
        return

    # Render content
    context = {
        'recipient_email': enrollment.email,
        'account': enrollment.account,
        'campaign': enrollment.drip_campaign,
        # Add unsubscribe link logic here if needed
    }
    
    try:
        html_content = render_to_string('marketing/email_wrapper.html', {
            'content': template.html_content,
            'context': context
        })
    except Exception:
        # Fallback if template wrapper doesn't exist or fails
        html_content = template.html_content
    
    try:
        send_mail(
            subject=template.subject_line,
            message=template.text_content,
            html_message=html_content,
            from_email='noreply@salescompass.com', # Should be configurable
            recipient_list=[enrollment.email]
        )
        logger.info(f"Sent drip email to {enrollment.email} for step {step.id}")
    except Exception as e:
        logger.error(f"Failed to send drip email to {enrollment.email}: {e}")
