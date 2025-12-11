from django.db import models
from django.utils import timezone
from core.models import User
from .models import Tenant
import json


class TenantDataPreservation(models.Model):
    """Model for managing tenant data preservation strategies"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='data_preservation_records')
    preservation_type = models.CharField(max_length=50, choices=[
        ('full_backup', 'Full Backup'),
        ('partial_backup', 'Partial Backup'),
        ('configuration_backup', 'Configuration Backup'),
        ('data_export', 'Data Export'),
        ('snapshot', 'System Snapshot'),
        ('migration_prep', 'Migration Preparation'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    description = models.TextField(blank=True, help_text="Description of the preservation operation")
    backup_location = models.TextField(blank=True, help_text="Location where data is preserved")
    file_size_mb = models.FloatField(default=0.0, help_text="Size of preserved data in MB")
    preservation_date = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this preservation expires")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='data_preservation_created')
    retention_period_days = models.IntegerField(default=30, help_text="Number of days to retain the preservation")
    modules_included = models.JSONField(default=list, blank=True, help_text="List of modules included in preservation")
    notes = models.TextField(blank=True, help_text="Additional notes about the preservation")
    
    class Meta:
        verbose_name = "Tenant Data Preservation"
        verbose_name_plural = "Tenant Data Preservations"
        ordering = ['-preservation_date']
    
    def __str__(self):
        return f"{self.preservation_type} for {self.tenant.name} at {self.preservation_date}"


class TenantDataRestoration(models.Model):
    """Model for tracking tenant data restoration operations"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='data_restoration_records')
    preservation_record = models.ForeignKey(TenantDataPreservation, on_delete=models.SET_NULL, null=True, blank=True, related_name='restorations')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    description = models.TextField(blank=True, help_text="Description of the restoration operation")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='data_restorations_initiated')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='data_restorations_completed')
    modules_restored = models.JSONField(default=list, blank=True, help_text="List of modules restored")
    total_records = models.IntegerField(default=0, help_text="Total number of records to restore")
    restored_records = models.IntegerField(default=0, help_text="Number of records successfully restored")
    failed_records = models.IntegerField(default=0, help_text="Number of records that failed to restore")
    error_log = models.TextField(blank=True, help_text="Log of any errors encountered during restoration")
    progress_percentage = models.FloatField(default=0.0, help_text="Progress percentage of the restoration")
    notes = models.TextField(blank=True, help_text="Additional notes about the restoration")
    
    class Meta:
        verbose_name = "Tenant Data Restoration"
        verbose_name_plural = "Tenant Data Restorations"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Restoration for {self.tenant.name} at {self.started_at}"
    
    def update_progress(self, restored_count, total_count):
        """Update the progress of the restoration"""
        self.restored_records = restored_count
        self.total_records = total_count
        if total_count > 0:
            self.progress_percentage = (restored_count / total_count) * 100
        else:
            self.progress_percentage = 0
        self.save()


class TenantDataPreservationStrategy(models.Model):
    """Model for defining data preservation strategies"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the preservation strategy")
    description = models.TextField(blank=True, help_text="Description of the preservation strategy")
    is_active = models.BooleanField(default=True, help_text="Whether this strategy is active")
    preservation_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('on_demand', 'On Demand'),
    ], default='weekly')
    retention_period_days = models.IntegerField(default=30, help_text="Number of days to retain backups")
    modules_to_preserve = models.JSONField(default=list, blank=True, help_text="List of modules to include in preservation")
    storage_location = models.CharField(max_length=255, default='default', help_text="Storage location for preserved data")
    compression_enabled = models.BooleanField(default=True, help_text="Whether to compress preserved data")
    encryption_enabled = models.BooleanField(default=True, help_text="Whether to encrypt preserved data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='preservation_strategies_created')
    
    class Meta:
        verbose_name = "Tenant Data Preservation Strategy"
        verbose_name_plural = "Tenant Data Preservation Strategies"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.preservation_frequency}"


class TenantDataPreservationSchedule(models.Model):
    """Model for scheduling automated data preservation"""
    id = models.AutoField(primary_key=True)
    strategy = models.ForeignKey(TenantDataPreservationStrategy, on_delete=models.CASCADE, related_name='schedules')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='preservation_schedules')
    next_scheduled_run = models.DateTimeField(help_text="When the next preservation should run")
    last_run = models.DateTimeField(null=True, blank=True, help_text="When the last preservation ran")
    is_active = models.BooleanField(default=True, help_text="Whether this schedule is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tenant Data Preservation Schedule"
        verbose_name_plural = "Tenant Data Preservation Schedules"
        ordering = ['tenant__name', 'next_scheduled_run']
        unique_together = ['strategy', 'tenant']
    
    def __str__(self):
        return f"{self.strategy.name} for {self.tenant.name} - Next: {self.next_scheduled_run}"
