from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from core.models import User
from tenants.models import Tenant
from global_alerts.models import AlertInstance


class ResourceAllocation(models.Model):
    """Model for tracking resource distribution across services"""
    id = models.AutoField(primary_key=True)
    resource_type = models.CharField(max_length=100, choices=[
        ('cpu', 'CPU Cores'),
        ('memory', 'Memory (GB)'),
        ('storage', 'Storage (GB)'),
        ('bandwidth', 'Bandwidth (Mbps)'),
        ('database_connections', 'Database Connections'),
        ('api_rate_limit', 'API Rate Limit (requests/min)'),
        ('worker_processes', 'Worker Processes'),
        ('queue_capacity', 'Queue Capacity'),
    ])
    allocated_amount = models.FloatField(help_text="Amount of resource allocated")
    available_amount = models.FloatField(help_text="Amount of resource currently available")
    maximum_amount = models.FloatField(help_text="Maximum amount of resource available")
    allocated_to_service = models.CharField(max_length=255, help_text="Service or component the resource is allocated to")
    allocated_to_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='resource_allocations')
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources_allocated')
    allocation_date = models.DateTimeField(default=timezone.now)
    expiration_date = models.DateTimeField(null=True, blank=True, help_text="When this allocation expires")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Additional notes about the resource allocation")
    
    class Meta:
        verbose_name = "Resource Allocation"
        verbose_name_plural = "Resource Allocations"
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.resource_type}: {self.allocated_amount} allocated to {self.allocated_to_service}"


class InfrastructureAlert(models.Model):
    """Model for managing infrastructure-level alerts"""
    id = models.AutoField(primary_key=True)
    alert_type = models.CharField(max_length=100, choices=[
        ('cpu_high', 'High CPU Usage'),
        ('memory_high', 'High Memory Usage'),
        ('disk_full', 'Disk Full'),
        ('network_down', 'Network Down'),
        ('service_down', 'Service Down'),
        ('database_slow', 'Slow Database'),
        ('connection_failed', 'Connection Failed'),
        ('timeout', 'Timeout'),
        ('error_rate', 'High Error Rate'),
        ('latency', 'High Latency'),
        ('capacity_threshold', 'Capacity Threshold Reached'),
        ('security_breach', 'Security Breach'),
        ('backup_failure', 'Backup Failure'),
        ('replication_error', 'Replication Error'),
        ('certificate_expiry', 'Certificate Expiry'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='warning')
    title = models.CharField(max_length=255)
    description = models.TextField()
    affected_service = models.CharField(max_length=255, help_text="Service or component affected")
    affected_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='infrastructure_alerts')
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='infrastructure_alerts_assigned')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    trigger_timestamp = models.DateTimeField(default=timezone.now)
    resolved_timestamp = models.DateTimeField(null=True, blank=True)
    acknowledged_timestamp = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='infrastructure_alerts_acknowledged')
    resolution_notes = models.TextField(blank=True)
    escalation_level = models.IntegerField(default=1)
    auto_resolve_after_minutes = models.IntegerField(null=True, blank=True, help_text="Auto-resolve after X minutes if condition clears")
    
    class Meta:
        verbose_name = "Infrastructure Alert"
        verbose_name_plural = "Infrastructure Alerts"
        ordering = ['-trigger_timestamp']
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.title} - {self.status}"


class PerformanceBaseline(models.Model):
    """Model for establishing performance benchmarks"""
    id = models.AutoField(primary_key=True)
    baseline_type = models.CharField(max_length=100, choices=[
        ('response_time', 'API Response Time'),
        ('throughput', 'Request Throughput'),
        ('concurrency', 'Concurrent Users'),
        ('memory_usage', 'Memory Usage'),
        ('cpu_usage', 'CPU Usage'),
        ('database_queries', 'Database Query Time'),
        ('cache_hit_ratio', 'Cache Hit Ratio'),
        ('disk_io', 'Disk I/O'),
    ])
    baseline_value = models.FloatField(help_text="Expected performance value")
    unit = models.CharField(max_length=20, default='ms')
    service_name = models.CharField(max_length=255, help_text="Service or component being benchmarked")
    environment = models.CharField(max_length=50, choices=[
        ('development', 'Development'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ], default='production')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='performance_baselines')
    baseline_period = models.CharField(max_length=50, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Performance Baseline"
        verbose_name_plural = "Performance Baselines"
        unique_together = ['baseline_type', 'service_name', 'environment', 'tenant', 'baseline_period']
        ordering = ['baseline_type', 'service_name']
    
    def __str__(self):
        return f"{self.baseline_type} baseline for {self.service_name} ({self.environment})"


class CapacityPlanning(models.Model):
    """Model for tracking capacity planning activities"""
    id = models.AutoField(primary_key=True)
    resource_type = models.CharField(max_length=100, choices=[
        ('cpu', 'CPU Cores'),
        ('memory', 'Memory (GB)'),
        ('storage', 'Storage (GB)'),
        ('bandwidth', 'Bandwidth (Mbps)'),
        ('database_connections', 'Database Connections'),
        ('api_rate_limit', 'API Rate Limit'),
        ('users', 'Users'),
        ('requests', 'Requests per Second'),
        ('transactions', 'Transactions per Day'),
    ])
    current_usage = models.FloatField(help_text="Current usage of the resource")
    current_capacity = models.FloatField(help_text="Current capacity of the resource")
    projected_growth_rate = models.FloatField(help_text="Projected growth rate (percentage)", default=0.0)
    projected_growth_unit = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], default='monthly')
    forecast_period_months = models.IntegerField(default=12, help_text="Forecast period in months")
    projected_usage = models.FloatField(help_text="Projected usage after forecast period", null=True, blank=True)
    capacity_needed = models.FloatField(help_text="Additional capacity needed", null=True, blank=True)
    recommendation = models.TextField(help_text="Recommendation for capacity planning")
    service_name = models.CharField(max_length=255, help_text="Service or component being analyzed")
    environment = models.CharField(max_length=50, choices=[
        ('development', 'Development'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ], default='production')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='capacity_planning')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='capacity_planning_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    implementation_status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='not_started')
    implementation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Capacity Planning"
        verbose_name_plural = "Capacity Planning"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.resource_type} capacity planning for {self.service_name}"


class InfrastructureAudit(models.Model):
    """Model for logging infrastructure changes"""
    id = models.AutoField(primary_key=True)
    change_type = models.CharField(max_length=100, choices=[
        ('deployment', 'Deployment'),
        ('configuration_change', 'Configuration Change'),
        ('scaling', 'Scaling'),
        ('maintenance', 'Maintenance'),
        ('upgrade', 'Upgrade'),
        ('rollback', 'Rollback'),
        ('patch', 'Patch'),
        ('backup', 'Backup'),
        ('restore', 'Restore'),
        ('migration', 'Migration'),
        ('security_scan', 'Security Scan'),
        ('monitoring_change', 'Monitoring Change'),
        ('alert_change', 'Alert Configuration Change'),
    ])
    service_name = models.CharField(max_length=255, help_text="Service or component affected")
    environment = models.CharField(max_length=50, choices=[
        ('development', 'Development'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ], default='production')
    change_summary = models.TextField(help_text="Brief summary of the change")
    change_details = models.JSONField(default=dict, blank=True, help_text="Detailed information about the change")
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='infrastructure_changes_initiated')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='infrastructure_changes_approved')
    approval_timestamp = models.DateTimeField(null=True, blank=True)
    change_timestamp = models.DateTimeField(default=timezone.now)
    rollback_possible = models.BooleanField(default=True, help_text="Whether the change can be rolled back")
    rollback_instructions = models.TextField(blank=True, help_text="Instructions for rolling back the change")
    impact_assessment = models.TextField(blank=True, help_text="Assessment of the change's impact")
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('executed', 'Executed'),
        ('rolled_back', 'Rolled Back'),
        ('failed', 'Failed'),
    ], default='pending')
    completion_timestamp = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Infrastructure Audit"
        verbose_name_plural = "Infrastructure Audits"
        ordering = ['-change_timestamp']
    
    def __str__(self):
        return f"{self.change_type} for {self.service_name} in {self.environment} - {self.status}"


class AppModule(models.Model):
    """Model for application modules that can be provisioned to tenants"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the application module")
    slug = models.SlugField(max_length=255, unique=True, help_text="URL-friendly identifier for the module")
    description = models.TextField(blank=True, help_text="Description of what the module does")
    version = models.CharField(max_length=50, default='1.0.0', help_text="Version of the module")
    is_active = models.BooleanField(default=True, help_text="Whether this module is available for provisioning")
    is_core_module = models.BooleanField(default=False, help_text="Whether this is a core module required for all tenants")
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependent_modules', help_text="Modules that this module depends on")
    requires_tenant_setup = models.BooleanField(default=True, help_text="Whether the module requires specific tenant setup")
    installation_script = models.TextField(blank=True, help_text="Script to run when installing the module")
    uninstallation_script = models.TextField(blank=True, help_text="Script to run when uninstalling the module")
    configuration_schema = models.JSONField(default=dict, blank=True, help_text="JSON schema for module configuration")
    default_configuration = models.JSONField(default=dict, blank=True, help_text="Default configuration for the module")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modules_created')
    icon_url = models.URLField(blank=True, help_text="URL to the module's icon")
    documentation_url = models.URLField(blank=True, help_text="URL to the module's documentation")
    
    class Meta:
        verbose_name = "Application Module"
        verbose_name_plural = "Application Modules"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class TenantModuleProvision(models.Model):
    """Model for tracking module provisioning to tenants"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='module_provisions')
    app_module = models.ForeignKey(AppModule, on_delete=models.CASCADE, related_name='tenant_provisions')
    is_enabled = models.BooleanField(default=False, help_text="Whether the module is enabled for this tenant")
    configuration = models.JSONField(default=dict, blank=True, help_text="Tenant-specific configuration for the module")
    installed_at = models.DateTimeField(null=True, blank=True, help_text="When the module was installed")
    installed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modules_installed')
    activated_at = models.DateTimeField(null=True, blank=True, help_text="When the module was activated")
    activated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modules_activated')
    deactivated_at = models.DateTimeField(null=True, blank=True, help_text="When the module was deactivated")
    deactivated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modules_deactivated')
    uninstalled_at = models.DateTimeField(null=True, blank=True, help_text="When the module was uninstalled")
    uninstalled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modules_uninstalled')
    version_installed = models.CharField(max_length=50, help_text="Version of the module installed")
    requires_restart = models.BooleanField(default=False, help_text="Whether activating this module requires system restart")
    installation_status = models.CharField(max_length=20, choices=[
        ('not_installed', 'Not Installed'),
        ('installing', 'Installing'),
        ('installed', 'Installed'),
        ('activating', 'Activating'),
        ('active', 'Active'),
        ('deactivating', 'Deactivating'),
        ('deactivated', 'Deactivated'),
        ('uninstalling', 'Uninstalling'),
        ('uninstalled', 'Uninstalled'),
        ('failed', 'Failed'),
    ], default='not_installed')
    installation_error = models.TextField(blank=True, help_text="Error message if installation failed")
    last_health_check = models.DateTimeField(null=True, blank=True, help_text="Last time module health was checked")
    health_status = models.CharField(max_length=20, choices=[
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='healthy')
    notes = models.TextField(blank=True, help_text="Additional notes about the module provisioning")
    
    class Meta:
        verbose_name = "Tenant Module Provision"
        verbose_name_plural = "Tenant Module Provisions"
        unique_together = ['tenant', 'app_module']
        ordering = ['tenant__name', 'app_module__name']
    
    def __str__(self):
        return f"{self.app_module.name} for {self.tenant.name} - {self.installation_status}"


class ModuleProvisionWorkflow(models.Model):
    """Model for managing module provisioning workflows"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the provisioning workflow")
    description = models.TextField(blank=True, help_text="Description of the workflow")
    app_module = models.ForeignKey(AppModule, on_delete=models.CASCADE, related_name='provision_workflows')
    workflow_type = models.CharField(max_length=50, choices=[
        ('new_tenant', 'New Tenant Setup'),
        ('existing_tenant', 'Existing Tenant Addition'),
        ('upgrade', 'Module Upgrade'),
        ('reinstall', 'Module Reinstall'),
        ('custom', 'Custom Workflow'),
    ])
    steps = models.JSONField(default=list, blank=True, help_text="Ordered list of steps in the workflow")
    is_active = models.BooleanField(default=True, help_text="Whether this workflow is active")
    is_default = models.BooleanField(default=False, help_text="Whether this is the default workflow for the module")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='module_provision_workflows_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='workflows_updated')
    
    class Meta:
        verbose_name = "Module Provision Workflow"
        verbose_name_plural = "Module Provision Workflows"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} for {self.app_module.name}"


class ModuleDependency(models.Model):
    """Model for managing module dependencies and conflicts"""
    id = models.AutoField(primary_key=True)
    dependent_module = models.ForeignKey(AppModule, on_delete=models.CASCADE, related_name='module_dependencies')
    required_module = models.ForeignKey(AppModule, on_delete=models.CASCADE, related_name='required_by_modules')
    dependency_type = models.CharField(max_length=50, choices=[
        ('requires', 'Requires'),
        ('conflicts_with', 'Conflicts With'),
        ('optional', 'Optional'),
        ('recommended', 'Recommended'),
    ])
    min_version = models.CharField(max_length=50, blank=True, help_text="Minimum required version")
    max_version = models.CharField(max_length=50, blank=True, help_text="Maximum allowed version")
    is_active = models.BooleanField(default=True, help_text="Whether this dependency is active")
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Additional notes about the dependency")
    
    class Meta:
        verbose_name = "Module Dependency"
        verbose_name_plural = "Module Dependencies"
        unique_together = ['dependent_module', 'required_module']
        ordering = ['dependent_module__name', 'required_module__name']
    
    def __str__(self):
        return f"{self.dependent_module.name} {self.dependency_type} {self.required_module.name}"


class ResourceMonitoring(models.Model):
    """Model for tracking resource utilization in real-time"""
    id = models.AutoField(primary_key=True)
    resource_type = models.CharField(max_length=100, choices=[
        ('cpu', 'CPU'),
        ('memory', 'Memory'),
        ('storage', 'Storage'),
        ('database', 'Database'),
        ('network', 'Network'),
        ('queue', 'Queue'),
        ('cache', 'Cache'),
        ('disk_io', 'Disk I/O'),
        ('connections', 'Connections'),
    ])
    service_name = models.CharField(max_length=255, help_text="Service or component being monitored")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='resource_monitoring')
    current_value = models.FloatField(help_text="Current value of the resource metric")
    unit = models.CharField(max_length=20, help_text="Unit of measurement (e.g., %, GB, MB/s)")
    threshold_critical = models.FloatField(help_text="Critical threshold value")
    threshold_warning = models.FloatField(help_text="Warning threshold value")
    is_alerting = models.BooleanField(default=False, help_text="Whether an alert is currently active")
    alert_severity = models.CharField(max_length=20, choices=[
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    peak_value = models.FloatField(null=True, blank=True, help_text="Peak value recorded in the period")
    avg_value = models.FloatField(null=True, blank=True, help_text="Average value in the period")
    min_value = models.FloatField(null=True, blank=True, help_text="Minimum value in the period")
    data_points_count = models.IntegerField(default=0, help_text="Number of data points collected in the period")
    status = models.CharField(max_length=20, choices=[
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], default='normal')
    
    class Meta:
        verbose_name = "Resource Monitoring"
        verbose_name_plural = "Resource Monitoring"
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['resource_type', 'service_name', 'tenant', '-last_updated']),
        ]
    
    def __str__(self):
        return f"{self.resource_type} monitoring for {self.service_name} ({self.current_value}{self.unit})"


class ResourceQuota(models.Model):
    """Model for managing resource quotas per tenant"""
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='resource_quotas')
    resource_type = models.CharField(max_length=100, choices=[
        ('cpu', 'CPU Cores'),
        ('memory', 'Memory (GB)'),
        ('storage', 'Storage (GB)'),
        ('bandwidth', 'Bandwidth (Mbps)'),
        ('database_connections', 'Database Connections'),
        ('api_calls', 'API Calls per Month'),
        ('users', 'Users'),
        ('accounts', 'Accounts'),
        ('leads', 'Leads'),
        ('opportunities', 'Opportunities'),
    ])
    allocated_quota = models.FloatField(help_text="Total quota allocated to the tenant")
    used_quota = models.FloatField(default=0, help_text="Amount of quota currently used")
    unit = models.CharField(max_length=20, default='units', help_text="Unit of measurement")
    reset_cycle = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], default='monthly')
    last_reset = models.DateTimeField(auto_now_add=True)
    is_soft_limit = models.BooleanField(default=False, help_text="Whether to warn instead of block when limit reached")
    grace_period_hours = models.IntegerField(default=0, help_text="Grace period in hours after quota exceeded")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resource Quota"
        verbose_name_plural = "Resource Quotas"
        unique_together = ['tenant', 'resource_type']
        ordering = ['tenant__name', 'resource_type']
    
    def __str__(self):
        return f"{self.resource_type} quota for {self.tenant.name}: {self.used_quota}/{self.allocated_quota} {self.unit}"
    
    def percentage_used(self):
        if self.allocated_quota > 0:
            return (self.used_quota / self.allocated_quota) * 100
        return 0


class ResourceAlert(models.Model):
    """Model for resource-specific alerts"""
    id = models.AutoField(primary_key=True)
    resource_monitoring = models.ForeignKey(ResourceMonitoring, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=100, choices=[
        ('threshold_exceeded', 'Threshold Exceeded'),
        ('quota_exceeded', 'Quota Exceeded'),
        ('resource_low', 'Resource Low'),
        ('peak_usage', 'Peak Usage'),
        ('anomaly_detected', 'Anomaly Detected'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ])
    message = models.TextField(help_text="Alert message")
    threshold_value = models.FloatField(help_text="Value that triggered the alert")
    current_value = models.FloatField(help_text="Current value at time of alert")
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], default='open')
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resource_alerts_acknowledged')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resource_alerts_resolved')
    resolved_at = models.DateTimeField(null=True, blank=True)
    escalation_level = models.IntegerField(default=1)
    escalation_reason = models.TextField(blank=True, help_text="Reason for escalating the alert")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resource Alert"
        verbose_name_plural = "Resource Alerts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_type} for {self.resource_monitoring.service_name}: {self.current_value} vs {self.threshold_value}"


class ResourceUsageReport(models.Model):
    """Model for resource usage reports"""
    id = models.AutoField(primary_key=True)
    report_type = models.CharField(max_length=100, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ])
    title = models.CharField(max_length=255, help_text="Report title")
    description = models.TextField(blank=True, help_text="Report description")
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resource_reports_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(help_text="Start date for the report")
    end_date = models.DateTimeField(help_text="End date for the report")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='resource_reports')
    resource_types = models.JSONField(default=list, blank=True, help_text="List of resource types included in the report")
    report_data = models.JSONField(default=dict, blank=True, help_text="Report data in JSON format")
    report_file_path = models.TextField(blank=True, help_text="Path to the generated report file")
    is_archived = models.BooleanField(default=False, help_text="Whether the report is archived")
    archived_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes about the report")
    
    class Meta:
        verbose_name = "Resource Usage Report"
        verbose_name_plural = "Resource Usage Reports"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} ({self.report_type}) - {self.generated_at.date()}"


class AlertRule(models.Model):
    """Model for defining custom alert rules"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the alert rule")
    description = models.TextField(blank=True, help_text="Description of what this alert rule monitors")
    is_active = models.BooleanField(default=True, help_text="Whether this alert rule is currently active")
    condition_type = models.CharField(max_length=100, choices=[
        ('threshold', 'Threshold'),
        ('anomaly', 'Anomaly Detection'),
        ('pattern', 'Pattern Matching'),
        ('time_based', 'Time Based'),
        ('dependency', 'Dependency Based'),
        ('custom', 'Custom Logic'),
    ])
    condition_expression = models.TextField(help_text="Expression that defines when the alert should trigger")
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='warning')
    frequency = models.CharField(max_length=20, choices=[
        ('real_time', 'Real Time'),
        ('minute', 'Every Minute'),
        ('five_minutes', 'Every 5 Minutes'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ], default='real_time')
    evaluation_window_minutes = models.IntegerField(default=5, help_text="Time window in minutes to evaluate the condition")
    cooldown_period_minutes = models.IntegerField(default=15, help_text="Cooldown period to prevent alert spamming")
    target_tenants = models.ManyToManyField(Tenant, blank=True, related_name='alert_rules_targeted')
    target_users = models.ManyToManyField(User, blank=True, related_name='alert_rules_targeted')
    notification_channels = models.JSONField(default=list, blank=True, help_text="Channels to send notifications to")
    escalation_policy = models.JSONField(default=dict, blank=True, help_text="How to escalate the alert")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alert_rules_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_evaluated = models.DateTimeField(null=True, blank=True, help_text="Last time the rule was evaluated")
    last_triggered = models.DateTimeField(null=True, blank=True, help_text="Last time the rule triggered an alert")
    trigger_count = models.IntegerField(default=0, help_text="Number of times this rule has triggered")
    suppression_rules = models.JSONField(default=list, blank=True, help_text="Rules to suppress this alert")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing alert rules")
    notes = models.TextField(blank=True, help_text="Internal notes about the alert rule")
    
    class Meta:
        verbose_name = "Alert Rule"
        verbose_name_plural = "Alert Rules"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.severity.upper()}"


class AlertEscalationPath(models.Model):
    """Model for managing alert escalation procedures"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the escalation path")
    description = models.TextField(blank=True, help_text="Description of the escalation procedure")
    steps = models.JSONField(default=list, blank=True, help_text="Ordered list of escalation steps")
    time_threshold_minutes = models.IntegerField(default=30, help_text="Time threshold to trigger next escalation step")
    repeat_interval_minutes = models.IntegerField(default=60, help_text="Interval to repeat escalation if unresolved")
    max_escalation_levels = models.IntegerField(default=3, help_text="Maximum number of escalation levels")
    is_active = models.BooleanField(default=True, help_text="Whether this escalation path is active")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalation_paths_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True, help_text="Last time this escalation path was used")
    usage_count = models.IntegerField(default=0, help_text="Number of times this escalation path was used")
    
    class Meta:
        verbose_name = "Alert Escalation Path"
        verbose_name_plural = "Alert Escalation Paths"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.max_escalation_levels} levels"


class AlertSuppressionRule(models.Model):
    """Model for defining when alerts should be suppressed"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the suppression rule")
    description = models.TextField(blank=True, help_text="Description of when alerts should be suppressed")
    is_active = models.BooleanField(default=True, help_text="Whether this suppression rule is active")
    suppression_type = models.CharField(max_length=50, choices=[
        ('time_based', 'Time Based'),
        ('maintenance_window', 'Maintenance Window'),
        ('severity_based', 'Severity Based'),
        ('resource_based', 'Resource Based'),
        ('tenant_based', 'Tenant Based'),
        ('pattern_based', 'Pattern Based'),
    ])
    suppression_condition = models.JSONField(default=dict, blank=True, help_text="Condition that determines when to suppress alerts")
    start_time = models.DateTimeField(null=True, blank=True, help_text="Start time for time-based suppression")
    end_time = models.DateTimeField(null=True, blank=True, help_text="End time for time-based suppression")
    applies_to_tenants = models.ManyToManyField(Tenant, blank=True, related_name='alert_suppressions')
    applies_to_alert_types = models.JSONField(default=list, blank=True, help_text="Alert types this suppression applies to")
    applies_to_severities = models.JSONField(default=list, blank=True, help_text="Severities this suppression applies to")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='suppression_rules_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_applied = models.DateTimeField(null=True, blank=True, help_text="Last time this rule was applied")
    suppression_count = models.IntegerField(default=0, help_text="Number of times this rule has suppressed alerts")
    
    class Meta:
        verbose_name = "Alert Suppression Rule"
        verbose_name_plural = "Alert Suppression Rules"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.suppression_type}"


class AlertNotificationPreference(models.Model):
    """Model for managing notification preferences"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alert_notification_preferences')
    alert_type = models.CharField(max_length=100, choices=[
        ('system', 'System Alerts'),
        ('security', 'Security Alerts'),
        ('performance', 'Performance Alerts'),
        ('availability', 'Availability Alerts'),
        ('capacity', 'Capacity Alerts'),
        ('maintenance', 'Maintenance Alerts'),
        ('custom', 'Custom Alerts'),
    ])
    channel = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('microsoft_teams', 'Microsoft Teams'),
        ('pagerduty', 'PagerDuty'),
        ('discord', 'Discord'),
    ])
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='normal')
    is_enabled = models.BooleanField(default=True, help_text="Whether notifications are enabled for this channel")
    custom_recipients = models.JSONField(default=list, blank=True, help_text="Additional recipients for this alert type")
    notification_template = models.TextField(blank=True, help_text="Custom template for notifications")
    timezone = models.CharField(max_length=50, default='UTC', help_text="Timezone for scheduling notifications")
    daily_digest = models.BooleanField(default=False, help_text="Whether to receive daily digest instead of individual alerts")
    weekly_summary = models.BooleanField(default=False, help_text="Whether to receive weekly summary")
    notification_schedule = models.JSONField(default=dict, blank=True, help_text="Schedule for when notifications are allowed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Alert Notification Preference"
        verbose_name_plural = "Alert Notification Preferences"
        unique_together = ['user', 'alert_type', 'channel']
        ordering = ['user__email', 'alert_type']
    
    def __str__(self):
        return f"{self.user.email} - {self.alert_type} - {self.channel}"


class AlertCorrelationGroup(models.Model):
    """Model for grouping related alerts"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the correlation group")
    description = models.TextField(blank=True, help_text="Description of the correlation group")
    correlation_rule = models.JSONField(default=dict, blank=True, help_text="Rule for determining related alerts")
    alerts = models.ManyToManyField(AlertInstance, related_name='correlation_groups', blank=True)
    root_cause_alert = models.ForeignKey(AlertInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='correlation_children')
    status = models.CharField(max_length=30, choices=[
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('root_cause_identified', 'Root Cause Identified'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], default='open')
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='warning')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='correlation_groups_assigned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, help_text="Notes about how the issue was resolved")
    impact_assessment = models.TextField(blank=True, help_text="Assessment of the impact of these correlated alerts")
    affected_tenants = models.ManyToManyField(Tenant, blank=True, related_name='correlation_groups')
    total_alerts = models.IntegerField(default=0, help_text="Total number of alerts in this group")
    unique_alert_types = models.JSONField(default=list, blank=True, help_text="List of unique alert types in this group")
    
    class Meta:
        verbose_name = "Alert Correlation Group"
        verbose_name_plural = "Alert Correlation Groups"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.total_alerts} alerts"
