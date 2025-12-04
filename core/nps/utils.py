from django.utils import timezone
from datetime import timedelta
from .models import NpsResponse, NpsDetractorAlert, NpsTrendSnapshot, NpsSurvey
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta

def calculate_nps_score(account_id: int = None, tenant_id: str = None) -> float:
    """
    Calculate Net Promoter Score: % Promoters - % Detractors.
    Returns score from -100 to +100.
    """
    responses = NpsResponse.objects.all()
    if account_id:
        responses = responses.filter(account_id=account_id)
    if tenant_id:
        responses = responses.filter(tenant_id=tenant_id)
    
    if not responses.exists():
        return 0.0
    
    total = responses.count()
    promoters = responses.filter(score__gte=9).count()
    detractors = responses.filter(score__lte=6).count()
    
    nps = ((promoters - detractors) / total) * 100
    return round(nps, 1)


def create_detractor_alert(response_id: int) -> None:
    """Create alert for NPS detractor."""
    response = NpsResponse.objects.get(id=response_id)
    if response.is_detractor:
        alert, created = NpsDetractorAlert.objects.get_or_create(
            response=response,
            defaults={'status': 'open'}
        )
        
        # Emit event for automation
        from automation.utils import emit_event
        emit_event('nps.detractor_alert', {
            'response_id': response.id,
            'account_id': response.account_id,
            'score': response.score,
            'tenant_id': response.tenant_id,
        })


def create_nps_trend_snapshot(tenant_id: str = None) -> NpsTrendSnapshot:
    """Create daily NPS snapshot."""
    today = timezone.now().date()
    responses = NpsResponse.objects.filter(created_at__date=today)
    if tenant_id:
        responses = responses.filter(tenant_id=tenant_id)
    
    total = responses.count()
    if total == 0:
        return None
    
    promoters = responses.filter(score__gte=9).count()
    passives = responses.filter(score__in=[7,8]).count()
    detractors = responses.filter(score__lte=6).count()
    nps_score = ((promoters - detractors) / total) * 100
    
    snapshot, created = NpsTrendSnapshot.objects.update_or_create(
        date=today,
        tenant_id=tenant_id,
        defaults={
            'nps_score': round(nps_score, 1),
            'total_responses': total,
            'promoters': promoters,
            'passives': passives,
            'detractors': detractors,
        }
    )
    return snapshot


def send_nps_survey(survey_id: int, account_id: int, contact_email: str = None) -> bool:
    """Send NPS survey via email."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    survey = NpsSurvey.objects.get(id=survey_id)
    account = Account.objects.get(id=account_id)
    
    if not contact_email:
        contact = account.contacts.filter(is_primary=True).first()
        if not contact:
            return False
        contact_email = contact.email
    
    # Generate unique response URL
    from uuid import uuid4
    response_uuid = uuid4()
    
    # In production, store in a PendingNpsResponse model
    html_content = render_to_string('engagement/nps_survey.html', {
        'survey': survey,
        'account': account,
        'contact_email': contact_email,
        'response_uuid': response_uuid,
    })
    
    send_mail(
        subject="We'd love your feedback!",
        message="",
        html_message=html_content,
        from_email="feedback@salescompass.com",
        recipient_list=[contact_email]
    )
    return True


def get_nps_trend_data(tenant_id: str = None, period: str = 'daily') -> list:
    """Get NPS trend data for charting."""

    
    # Determine date range
    if period == 'yearly':
        start_date = timezone.now().date() - timedelta(days=365*2)
        date_field = 'date__year'
    elif period == 'monthly':
        start_date = timezone.now().date() - timedelta(days=365)
        date_field = 'date__month'
    elif period == 'weekly':
        start_date = timezone.now().date() - timedelta(days=90)
        date_field = 'date__week'
    else:  # daily
        start_date = timezone.now().date() - timedelta(days=30)
        date_field = 'date'
    
    snapshots = NpsTrendSnapshot.objects.filter(
        date__gte=start_date
    )
    if tenant_id:
        snapshots = snapshots.filter(tenant_id=tenant_id)
    
    # Group by period
    if period == 'yearly':
        data = snapshots.values('date__year').annotate(
            avg_nps=Avg('nps_score'),
            total=Sum('total_responses')
        ).order_by('date__year')
        return [{'date': f"{item['date__year']}", 'nps': item['avg_nps']} for item in data]
    elif period == 'monthly':
        data = snapshots.values('date__year', 'date__month').annotate(
            avg_nps=Avg('nps_score')
        ).order_by('date__year', 'date__month')
        return [{'date': f"{item['date__year']}-{item['date__month']:02d}", 'nps': item['avg_nps']} for item in data]
    elif period == 'weekly':
        data = snapshots.extra(select={'week': "strftime('%%Y-%%W', date)"}).values('week').annotate(
            avg_nps=Avg('nps_score')
        ).order_by('week')
        return [{'date': item['week'], 'nps': item['avg_nps']} for item in data]
    else:  # daily
        data = snapshots.order_by('date')
        return [{'date': item.date.isoformat(), 'nps': item.nps_score} for item in data]