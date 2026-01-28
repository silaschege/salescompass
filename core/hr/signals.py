from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from hr.models import Employee
from learn.models import UserProgress, Course

@receiver(pre_save, sender=Employee)
def validate_employee_certification(sender, instance, **kwargs):
    """
    Example safety check: Before promoting an employee to 'Warehouse Lead',
    verify they have completed the 'Warehouse Safety 101' course in Learn.
    """
    if instance.job_title == 'Warehouse Lead':
        safety_course = Course.objects.filter(title__icontains='Warehouse Safety').first()
        if safety_course:
            progress = UserProgress.objects.filter(
                user=instance.user,
                course=safety_course,
                completion_status='completed'
            ).exists()
            
            if not progress:
                # In a real system, we might just log a warning or send an alert.
                # For this ERP prototype, we'll demonstrate a 'soft' validation notice.
                print(f"WARNING: Employee {instance.user.email} is missing mandatory certification: {safety_course.title}")
                # instance.compliance_alert = True (if field existed)
