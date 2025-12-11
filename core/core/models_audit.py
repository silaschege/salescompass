from django.db import models
from django.conf import settings
from django.utils import timezone
from .models import SystemConfigType, SystemConfigCategory, SystemEventType, SystemEventSeverity, HealthCheckType, HealthCheckStatus, MaintenanceStatus, MaintenanceType, PerformanceMetricType, PerformanceEnvironment, NotificationType, NotificationPriority


class DynamicChoiceAuditLog(models.Model):
    """
    Model to track all changes to dynamic choice models
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    
    id = models.AutoField(primary_key=True)
    # Store the action performed
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    
    # Store which model was affected
    model_name = models.CharField(max_length=100, help_text="Name of the model that was changed")
    object_id = models.IntegerField(help_text="ID of the object that was changed")
    object_name = models.CharField(max_length=255, help_text="Display name of the object that was changed")
    
    # Store the user who made the change
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Store the tenant (for multi-tenant support)
    tenant_id = models.IntegerField(null=True, blank=True)
    
    # Store the change details
    old_values = models.JSONField(null=True, blank=True, help_text="JSON representation of old field values")
    new_values = models.JSONField(null=True, blank=True, help_text="JSON representation of new field values")
    changed_fields = models.JSONField(null=True, blank=True, help_text="List of fields that were changed")
    
    # Store the timestamp
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Optional additional details
    notes = models.TextField(blank=True, help_text="Additional notes about the change")
    
    class Meta:
        verbose_name = "Dynamic Choice Audit Log"
        verbose_name_plural = "Dynamic Choice Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user']),
            models.Index(fields=['tenant_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.model_name} #{self.object_id} by {self.user.username if self.user else 'Unknown'} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @classmethod
    def log_change(cls, action, model_name, object_id, object_name, user, old_values=None, new_values=None, changed_fields=None, tenant_id=None, notes=""):
        """
        Create an audit log entry for a change to a dynamic choice model.
        """
        return cls.objects.create(
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_name=object_name,
            user=user,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            tenant_id=tenant_id,
            notes=notes
        )


class DynamicChoiceAuditMixin:
    """
    Mixin to add audit trail functionality to dynamic choice models.
    """
    def save(self, *args, **kwargs):
        # Check if this is an update (object already exists) or a create
        is_update = self.pk is not None
        
        # Store old values if this is an update
        old_values = None
        changed_fields = []
        
        if is_update:
            # Get the old instance from the database
            old_instance = self.__class__.objects.get(pk=self.pk)
            old_values = {}
            new_values = {}
            
            # Compare all fields to find what changed
            for field in self._meta.fields:
                if field.name != 'updated_at':  # Skip the updated_at field which changes automatically
                    old_val = getattr(old_instance, field.name)
                    new_val = getattr(self, field.name)
                    
                    if old_val != new_val:
                        old_values[field.name] = str(old_val) if old_val is not None else None
                        new_values[field.name] = str(new_val) if new_val is not None else None
                        changed_fields.append(field.name)
        
        # Call the original save method
        super().save(*args, **kwargs)
        
        # Log the change
        if hasattr(self, 'tenant_id'):
            tenant_id = self.tenant_id
        else:
            tenant_id = None
            
        if is_update:
            # This is an update
            DynamicChoiceAuditLog.log_change(
                action='UPDATE',
                model_name=self.__class__.__name__,
                object_id=self.pk,
                object_name=getattr(self, 'name', getattr(self, 'display_name', str(self.pk))),
                user=getattr(self, '_current_user', None),
                old_values=old_values,
                new_values={field: str(getattr(self, field)) if getattr(self, field) is not None else None for field in changed_fields},
                changed_fields=changed_fields,
                tenant_id=tenant_id,
                notes="Updated via admin interface" if changed_fields else ""
            )
        else:
            # This is a create
            new_values = {}
            for field in self._meta.fields:
                if field.name not in ['id', 'created_at', 'updated_at']:  # Skip auto fields
                    new_values[field.name] = str(getattr(self, field.name)) if getattr(self, field.name) is not None else None
            
            DynamicChoiceAuditLog.log_change(
                action='CREATE',
                model_name=self.__class__.__name__,
                object_id=self.pk,
                object_name=getattr(self, 'name', getattr(self, 'display_name', str(self.pk))),
                user=getattr(self, '_current_user', None),
                new_values=new_values,
                tenant_id=tenant_id,
                notes="Created via admin interface"
            )


# Apply the audit mixin to all dynamic choice models
def apply_audit_mixin():
    """
    Function to apply audit mixin to all dynamic choice models.
    This would typically be called during app initialization.
    """
    # Inherit from both the original model and the audit mixin
    # This is done by dynamically creating new classes that inherit from both
    pass
