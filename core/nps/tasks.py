from celery import shared_task
from .utils import send_nps_survey

@shared_task
def send_nps_survey_task(survey_id: int, account_id: int, contact_email: str = None):
    """Send NPS survey asynchronously."""
    send_nps_survey(survey_id, account_id, contact_email)  