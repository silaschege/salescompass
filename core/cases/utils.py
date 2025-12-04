from django.utils import timezone
from datetime import timedelta
from .models import Case, SlaPolicy, CsatResponse, CsatDetractorAlert
 # Generate unique response URL
from uuid import uuid4
   # Emit event for automation and CSAT event
from automation.utils import emit_event
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db import models

def calculate_sla_due_date(priority: str) -> timezone.datetime:
    """Calculate SLA due date based on priority."""
    policy = SlaPolicy.objects.filter(priority=priority).first()
    if not policy:
        # Fallback policies
        hours = {'critical': 4, 'high': 24, 'medium': 72, 'low': 168}[priority]
    else:
        hours = policy.resolution_hours
    
    return timezone.now() + timedelta(hours=hours)


def escalate_case(case_id: int, level: str, escalated_by_id: int) -> None:
    """Escalate a case to a higher level."""
    case = Case.objects.select_for_update().get(id=case_id)
    case.escalation_level = level
    case.escalated_by_id = escalated_by_id
    case.save(update_fields=['escalation_level', 'escalated_by'])

 
    emit_event('case.escalated', {
        'case_id': case.id,
        'account_id': case.account_id,
        'new_level': level,
        'tenant_id': case.tenant_id,
    })


def close_case_with_csat(case_id: int, csat_score: int, csat_comment: str = "") -> None:
    """Close case and record CSAT."""
    case = Case.objects.select_for_update().get(id=case_id)
    case.status = 'closed'
    case.csat_score = csat_score
    case.csat_comment = csat_comment
    case.resolved_at = timezone.now()
    case.save(update_fields=['status', 'csat_score', 'csat_comment', 'resolved_at'])

    # Create CSAT response
    response = CsatResponse.objects.create(
        case=case,
        score=csat_score,
        comment=csat_comment,
        tenant_id=case.tenant_id
    )

    # Create detractor alert if score <= 3
    if csat_score <= 3:
        CsatDetractorAlert.objects.create(
            response=response,
            status='open'
        )


    emit_event('case.csat_submitted', {
        'case_id': case.id,
        'account_id': case.account_id,
        'csat_score': csat_score,
        'tenant_id': case.tenant_id,
    })


def get_overdue_cases(tenant_id: str = None) -> models.QuerySet:
    """Get all overdue cases."""
    queryset = Case.objects.filter(
        sla_due__lt=timezone.now(),
        status__in=['new', 'in_progress']
    )
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)
    return queryset


def send_csat_survey(case_id: int) -> None:
    """Send CSAT survey email after case resolution."""
  
    
    case = Case.objects.get(id=case_id)
    contact = case.contact or case.account.contacts.filter(is_primary=True).first()
    
    if not contact:
        return
    
   
    response_uuid = uuid4()
    
    html_content = render_to_string('cases/csat_survey.html', {
        'case': case,
        'contact': contact,
        'response_uuid': response_uuid,
    })
    
    send_mail(
        subject="How did we do? - SalesCompass Support",
        message="",
        html_message=html_content,
        from_email="support@salescompass.com",
        recipient_list=[contact.email]
    )