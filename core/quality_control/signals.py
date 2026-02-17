from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InspectionLog, NonConformanceReport

@receiver(post_save, sender=InspectionLog)
def create_ncr_on_failed_inspection(sender, instance, created, **kwargs):
    """
    Automatically create an NCR if specific inspection fails and one doesn't exist.
    """
    if instance.status == 'failed':
        # Check if NCR already exists
        if not hasattr(instance, 'ncr'):
            NonConformanceReport.objects.create(
                tenant=instance.tenant,
                inspection_log=instance,
                issue_description=f"Automated NCR generated from failed inspection {instance.pk}. Please investigate."
            )
