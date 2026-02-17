
import logging
from django.utils import timezone
from .models import AutomationAlert, AutomationNotificationPreference, WorkflowExecution, AutomationExecutionLog
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

class AutomationAlertService:
    @classmethod
    def create_alert_from_execution(cls, execution: WorkflowExecution) -> Optional[AutomationAlert]:
        """Create an alert for a failed workflow execution."""
        if execution.workflow_execution_status != 'failed':
            return None
            
        alert = AutomationAlert.objects.create(
            workflow=execution.workflow,
            workflow_execution=execution,
            alert_title=f"Workflow Failed: {execution.workflow.workflow_name}",
            alert_message=execution.workflow_execution_error_message or "Unknown error occurred during execution",
            alert_severity='high' if execution.workflow_execution_error_message else 'medium',
            tenant=execution.tenant
        )
        
        # Trigger notifications
        cls.notify_users_of_alert(alert)
        return alert

    @classmethod
    def notify_users_of_alert(cls, alert: AutomationAlert):
        """Send notifications to users based on their preferences."""
        # Get users in the tenant who have notification preferences
        preferences = AutomationNotificationPreference.objects.filter(
            tenant=alert.tenant,
            enable_email_notifications=True
        ).select_related('user')
        
        for pref in preferences:
            should_notify = False
            if pref.notify_on_all_failures:
                should_notify = True
            elif pref.notify_on_critical_only and alert.alert_severity in ['high', 'critical']:
                should_notify = True
                
            if should_notify:
                cls.send_email_notification(pref.user, alert)

    @staticmethod
    def send_email_notification(user, alert: AutomationAlert):
        """Send email notification to a user."""
        subject = f"[SalesCompass] {alert.alert_title}"
        message = f"""
        Hello {user.first_name or user.username},

        An automation workflow has failed and requires your attention.

        Workflow: {alert.workflow.workflow_name if alert.workflow else 'N/A'}
        Severity: {alert.alert_severity.upper()}
        Message: {alert.alert_message}

        You can view the details here: 
        {settings.BASE_URL}/automation/workflow-execution/{alert.workflow_execution.id if alert.workflow_execution else ''}/

        Regards,
        SalesCompass Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True
            )
            logger.info(f"Sent automation alert email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send automation alert email to {user.email}: {e}")
