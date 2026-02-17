from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .utils import generate_report

@shared_task
def send_scheduled_report(schedule_id: int):
    """Send scheduled report via email."""
    from .models import ReportSchedule, ReportExport
    
    schedule = ReportSchedule.objects.get(id=schedule_id)
    report = schedule.report
    
    # Generate report
    response = generate_report(report.id, schedule.export_format)
    
    # Save export record
    export = ReportExport.objects.create(
        report=report,
        export_format=schedule.export_format,
        status='completed'
    )
    export.file.save(f"report_{report.id}_{export.id}.{schedule.export_format}", response)
    
    # Send email to recipients
    for recipient in schedule.recipients:
        html_content = render_to_string('reports/export_email.html', {
            'report': report,
            'export': export,
            'download_url': f"https://salescompass.com/reports/export/{export.id}/"
        })
        
        msg = EmailMultiAlternatives(
            subject=f"SalesCompass Report: {report.name}",
            body="Please view in HTML",
            from_email="reports@salescompass.com",
            to=[recipient]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    
    # Schedule next run
    from datetime import timedelta
    if schedule.frequency == 'daily':
        schedule.next_run += timedelta(days=1)
    elif schedule.frequency == 'weekly':
        schedule.next_run += timedelta(weeks=1)
    elif schedule.frequency == 'monthly':
        schedule.next_run += timedelta(days=30)
    schedule.save(update_fields=['next_run'])


@shared_task
def check_due_reports():
    """Periodic task to check for due report schedules and trigger them."""
    from django.utils import timezone
    from .models import ReportSchedule
    
    now = timezone.now()
    due_schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_run__lte=now
    )
    
    for schedule in due_schedules:
        # Trigger the send_scheduled_report task asynchronously
        send_scheduled_report.delay(schedule.id)