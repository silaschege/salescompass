from django.db import models
from django.utils import timezone
import json


class AuditLog(models.Model):
    """Centralized audit logging for SOC2/HIPAA compliance"""
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    # Who
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    user_email = models.EmailField(db_index=True)
    tenant_id = models.IntegerField(db_index=True)
    
    # What
    action_type = models.CharField(max_length=100, db_index=True)  # e.g., USER_DELETE, BILLING_UPDATE
    resource_type = models.CharField(max_length=100)  # e.g., User, Lead, Opportunity
    resource_id = models.CharField(max_length=100, blank=True)
    
    # When
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Where
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True)
    
    # Details
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info', db_index=True)
    
    # Forensics - Before/After state
    state_before = models.JSONField(null=True, blank=True)
    state_after = models.JSONField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant_id', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['user_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action_type} by {self.user_email} at {self.timestamp}"
    
    @staticmethod
    def log_action(user, action_type, resource_type, resource_id='', description='', 
                   severity='info', state_before=None, state_after=None, 
                   ip_address='0.0.0.0', user_agent='', **metadata):
        """Helper method to create audit logs"""
        return AuditLog.objects.create(
            user_id=user.id if user else None,
            user_email=user.email if user else 'system@salescompass.com',
            tenant_id=getattr(user, 'tenant_id', 0),
            action_type=action_type,
            resource_type=resource_type,
            resource_id=str(resource_id),
            description=description,
            severity=severity,
            state_before=state_before,
            state_after=state_after,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
