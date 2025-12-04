from django.db import models
from django.utils import timezone


class Alert(models.Model):
    """Global system alerts/banners for tenant communication"""
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('maintenance', 'Scheduled Maintenance'),
        ('outage', 'Critical Outage'),
        ('announcement', 'New Feature Announcement'),
        ('security', 'Security Alert'),
        ('general', 'General Notice'),
    ]
    
    # Alert Details
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES, default='general')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    
    # Scheduling
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Targeting
    is_global = models.BooleanField(default=True, help_text="Show to all tenants")
    target_tenant_ids = models.JSONField(default=list, blank=True, help_text="Specific tenant IDs if not global")
    
    # Display Options
    is_dismissible = models.BooleanField(default=True)
    show_on_all_pages = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['is_active', '-start_time']),
            models.Index(fields=['severity', '-start_time']),
        ]
    
    def __str__(self):
        return f"{self.get_severity_display()}: {self.title}"
    
    def is_currently_active(self):
        """Check if alert should be displayed now"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        # Check if started
        if now < self.start_time:
            return False
        
        # Check if ended
        if self.end_time and now > self.end_time:
            return False
        
        return True
    
    def is_for_tenant(self, tenant_id):
        """Check if alert should be shown to specific tenant"""
        if self.is_global:
            return True
        
        return tenant_id in self.target_tenant_ids
    
    @property
    def css_class(self):
        """Return Bootstrap alert class based on severity"""
        severity_map = {
            'info': 'alert-info',
            'warning': 'alert-warning',
            'critical': 'alert-danger',
        }
        return severity_map.get(self.severity, 'alert-info')
    
    @classmethod
    def get_active_alerts_for_tenant(cls, tenant_id=None):
        """Get all currently active alerts for a tenant"""
        alerts = cls.objects.filter(is_active=True)
        
        # Filter by time
        now = timezone.now()
        alerts = alerts.filter(start_time__lte=now)
        alerts = alerts.filter(
            models.Q(end_time__isnull=True) | models.Q(end_time__gte=now)
        )
        
        # Filter by tenant
        if tenant_id:
            alerts = alerts.filter(
                models.Q(is_global=True) | models.Q(target_tenant_ids__contains=[tenant_id])
            )
        
        return alerts.order_by('-severity', '-start_time')
