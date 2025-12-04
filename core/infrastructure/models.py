from django.db import models
from django.utils import timezone


class TenantUsage(models.Model):
    """Track resource usage per tenant"""
    tenant_id = models.IntegerField(db_index=True)
    
    # API Usage
    api_calls_count = models.IntegerField(default=0)
    api_calls_limit = models.IntegerField(default=10000)  # per day
    
    # Storage Usage
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    storage_limit_gb = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    
    # Database Connections
    active_db_connections = models.IntegerField(default=0)
    max_db_connections = models.IntegerField(default=20)
    
    # Timestamps
    measured_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-measured_at']
        indexes = [
            models.Index(fields=['tenant_id', '-measured_at']),
        ]
    
    def __str__(self):
        return f"Usage for Tenant {self.tenant_id} at {self.measured_at}"
    
    @property
    def api_usage_percentage(self):
        if self.api_calls_limit == 0:
            return 0
        return (self.api_calls_count / self.api_calls_limit) * 100
    
    @property
    def storage_usage_percentage(self):
        if self.storage_limit_gb == 0:
            return 0
        return (float(self.storage_used_gb) / float(self.storage_limit_gb)) * 100
    
    @property
    def is_over_api_limit(self):
        return self.api_calls_count > self.api_calls_limit
    
    @property
    def is_over_storage_limit(self):
        return self.storage_used_gb > self.storage_limit_gb


class ResourceLimit(models.Model):
    """Manual throttling and limit enforcement for tenants"""
    tenant_id = models.IntegerField(unique=True, db_index=True)
    
    # Throttling
    is_throttled = models.BooleanField(default=False)
    throttle_reason = models.TextField(blank=True)
    
    # Custom Limits
    custom_api_limit = models.IntegerField(null=True, blank=True)
    custom_storage_limit_gb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_db_connections = models.IntegerField(null=True, blank=True)
    
    # Audit
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['tenant_id']
    
    def __str__(self):
        status = "Throttled" if self.is_throttled else "Active"
        return f"Tenant {self.tenant_id} - {status}"
