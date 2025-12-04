"""
Celery configuration for SalesCompass
"""
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')

app = Celery('salescompass')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Check for SLA breaches every 5 minutes
    'check-sla-breaches': {
        'task': 'cases.tasks.check_sla_breaches',
        'schedule': crontab(minute='*/5'),
    },
    # Sync emails every 15 minutes
    'sync-emails': {
        'task': 'communication.tasks.sync_emails',
        'schedule': crontab(minute='*/15'),
    },
    # Check for due drip emails every hour
    'send-drip-emails': {
        'task': 'engagement.tasks.send_due_drip_emails',
        'schedule': crontab(minute=0),  # Every hour
    },
    # Check for scheduled reports daily at 6 AM
    'send-scheduled-reports': {
        'task': 'reports.tasks.send_scheduled_reports',
        'schedule': crontab(hour=6, minute=0),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
