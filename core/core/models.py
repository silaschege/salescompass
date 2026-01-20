from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.conf import settings
 
class TimeStampedModel(models.Model):
    """
    An abstract model for adding created_at and updated_at timestamps
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
 
class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    role = models.ForeignKey('access_control.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    last_mfa_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Customer Lifetime Value (CLV) related fields
    customer_lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, 
                                                help_text="Calculated customer lifetime value")
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                           help_text="Cost to acquire this customer")
    retention_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000, 
                                        help_text="Customer retention rate as a decimal (e.g., 0.85 for 85%)")
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                          help_text="Average value of customer orders")
    customer_since = models.DateField(null=True, blank=True, 
                                      help_text="Date when customer relationship started")
    purchase_frequency = models.PositiveIntegerField(default=0, 
                                                     help_text="Number of purchases per year")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def calculate_avg_order_value(self):
        """Calculate the average order value from all payments made by this user"""
        from django.db.models import Avg
        from billing.models import Payment
        
        # Get all payments related to this user through their invoices and subscriptions
        avg_value = Payment.objects.filter(
            invoice__subscription__user=self,
            status='succeeded'
        ).aggregate(avg_amount=Avg('amount'))['avg_amount']
        
        return avg_value or 0.00

    def calculate_retention_rate(self):
        """Calculate retention rate based on subscription renewals"""
        # This is a simplified calculation - in practice, you might want to consider
        # more complex factors like subscription duration, gaps in service, etc.
        from billing.models import Subscription
        subscriptions = Subscription.objects.filter(user=self)
        
        if not subscriptions.exists():
            return 0.0000
        
        # Count active and renewed subscriptions
        active_subscriptions = subscriptions.filter(status_ref__name__in=['active', 'trialing'])
        total_subscriptions = subscriptions.count()
        
        if total_subscriptions == 0:
            return 0.0000
        
        # This is a basic retention calculation - could be enhanced with time-based logic
        return min(1.0000, float(active_subscriptions.count()) / total_subscriptions)

    def calculate_purchase_frequency(self):
        """Calculate how many purchases the customer makes per year"""
        from django.db.models import Count
        from datetime import datetime, timedelta
        from billing.models import Payment
        
        # Count successful payments in the last year
        one_year_ago = datetime.now() - timedelta(days=365)
        
        annual_purchases = Payment.objects.filter(
            invoice__subscription__user=self,
            status='succeeded',
            processed_at__gte=one_year_ago
        ).count()
        
        return annual_purchases

    def calculate_clv(self):
        """
        Calculate Customer Lifetime Value using the formula:
        CLV = (Average Order Value × Purchase Frequency × Retention Rate) / (1 - Retention Rate) - Acquisition Cost
        If retention rate is 1 (100%), use a simplified calculation
        """
        avg_order_value = self.avg_order_value or self.calculate_avg_order_value()
        retention_rate = float(self.retention_rate or self.calculate_retention_rate())
        purchase_frequency = self.purchase_frequency or self.calculate_purchase_frequency()
        
        if retention_rate >= 1.0:
            # If retention rate is 100%, we can't divide by zero
            # Use a simplified calculation based on average order value and frequency
            clv = avg_order_value * purchase_frequency * 5  # 5-year estimate
        elif retention_rate > 0:
            # Standard CLV calculation
            clv = (avg_order_value * purchase_frequency * retention_rate) / (1 - retention_rate) - self.acquisition_cost
        else:
            # If retention rate is 0, CLV is just negative acquisition cost
            clv = -self.acquisition_cost
        
        # Ensure CLV is not negative
        return max(0.00, clv)

    def update_clv(self):
        """Update all CLV-related fields and save the user"""
        self.avg_order_value = self.calculate_avg_order_value()
        self.retention_rate = self.calculate_retention_rate()
        self.purchase_frequency = self.calculate_purchase_frequency()
        self.customer_lifetime_value = self.calculate_clv()
        self.save()
        
        return self.customer_lifetime_value

    def calculate_customer_lifespan(self):
        """
        Calculate the average customer lifespan in years.
        This is a simplified calculation based on when the customer started
        and whether they're still active.
        """
        if not self.customer_since:
            # If we don't know when the relationship started, use account creation date
            customer_start = self.date_joined.date()
        else:
            customer_start = self.customer_since
        
        # Calculate how long the customer has been with us
        from datetime import date
        today = date.today()
        tenure_days = (today - customer_start).days
        
        # For customers with more than 2 years of tenure, we'll use actual tenure
        # For newer customers, we'll use a projected average based on retention
        if tenure_days > 730:  # More than 2 years
            return tenure_days / 365.0
        else:
            # For newer customers, estimate based on retention rate
            retention_rate = float(self.retention_rate or self.calculate_retention_rate())
            if retention_rate > 0 and retention_rate < 1:
                # Inverse of churn rate as a simple lifetime calculation
                # Churn rate = 1 - retention_rate
                # Average lifetime = 1 / churn_rate
                churn_rate = 1 - retention_rate
                if churn_rate > 0:
                    return min(10.0, 1 / churn_rate)  # Cap at 10 years
            return max(0.5, tenure_days / 365.0)  # Default to actual tenure if >= 6 months

    def calculate_clv_simple(self):
        """
        Calculate Customer Lifetime Value using the simple formula:
        CLV = Average Order Value × Purchase Frequency × Customer Lifespan
        """
        avg_order_value = self.avg_order_value or self.calculate_avg_order_value()
        purchase_frequency = self.purchase_frequency or self.calculate_purchase_frequency()
        customer_lifespan = self.calculate_customer_lifespan()
        
        clv = avg_order_value * purchase_frequency * customer_lifespan
        return clv

    def calculate_roi(self, expected_revenue=None):
        """
        Calculate ROI: (Expected Revenue - CAC) / CAC
        """
        cac = self.acquisition_cost or 0
        if expected_revenue is None:
            # Use calculated CLV as expected revenue if not provided
            expected_revenue = self.calculate_clv()
        
        if cac == 0:
            # Avoid division by zero
            return float('inf') if expected_revenue > 0 else 0
        
        roi = (expected_revenue - cac) / cac
        return roi

    def get_customer_value_trend(self, months=12):
        """Get CLV trend over the specified number of months"""
        # This would require historical CLV tracking, which could be implemented
        # with a separate model to store historical values
        pass


class SystemConfigType(models.Model):
    """Model for storing dynamic configuration types"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the config type (e.g., 'string', 'integer')")
    display_name = models.CharField(max_length=100, help_text="Display name for the config type (e.g., 'String', 'Integer')")
    description = models.TextField(blank=True, help_text="Description of the config type")
    is_active = models.BooleanField(default=True, help_text="Whether this config type is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Config Type"
        verbose_name_plural = "System Config Types"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class SystemConfigCategory(models.Model):
    """Model for storing dynamic configuration categories"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the category (e.g., 'general', 'security')")
    display_name = models.CharField(max_length=100, help_text="Display name for the category (e.g., 'General', 'Security')")
    description = models.TextField(blank=True, help_text="Description of the category")
    is_active = models.BooleanField(default=True, help_text="Whether this category is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Config Category"
        verbose_name_plural = "System Config Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class SystemConfiguration(models.Model):
    """Model for storing global system settings and configurations"""
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=50, choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('file', 'File Path'),
    ], default='string')
    # New dynamic field
    data_type_ref = models.ForeignKey(
        SystemConfigType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic data type (replaces data_type field)"
    )
    category = models.CharField(max_length=100, choices=[
        ('general', 'General'),
        ('security', 'Security'),
        ('email', 'Email'),
        ('authentication', 'Authentication'),
        ('integration', 'Integration'),
        ('performance', 'Performance'),
    ], default='general')
    # New dynamic field
    category_ref = models.ForeignKey(
        SystemConfigCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic category (replaces category field)"
    )
    is_sensitive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}{'...' if len(self.value) > 50 else ''}"


class SystemEventType(models.Model):
    """Model for storing dynamic system event types"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the event type (e.g., 'system_start', 'backup')")
    display_name = models.CharField(max_length=100, help_text="Display name for the event type (e.g., 'System Start', 'Backup')")
    description = models.TextField(blank=True, help_text="Description of the event type")
    is_active = models.BooleanField(default=True, help_text="Whether this event type is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Event Type"
        verbose_name_plural = "System Event Types"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class SystemEventSeverity(models.Model):
    """Model for storing dynamic system event severities"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True, help_text="Unique identifier for the severity (e.g., 'info', 'error')")
    display_name = models.CharField(max_length=50, help_text="Display name for the severity (e.g., 'Information', 'Error')")
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code for UI representation")
    description = models.TextField(blank=True, help_text="Description of the severity level")
    is_active = models.BooleanField(default=True, help_text="Whether this severity is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Event Severity"
        verbose_name_plural = "System Event Severities"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class SystemEventLog(models.Model):
    """Model for tracking system-level events and operations"""
    id = models.AutoField(primary_key=True)
    event_type = models.CharField(max_length=100, choices=[
        ('system_start', 'System Start'),
        ('system_stop', 'System Stop'),
        ('maintenance', 'Maintenance'),
        ('backup', 'Backup'),
        ('restore', 'Restore'),
        ('configuration_change', 'Configuration Change'),
        ('security_scan', 'Security Scan'),
        ('patch_install', 'Patch Install'),
        ('monitoring_alert', 'Monitoring Alert'),
    ])
    # New dynamic field
    event_type_ref = models.ForeignKey(
        SystemEventType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic event type (replaces event_type field)"
    )
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ], default='info')
    # New dynamic field
    severity_ref = models.ForeignKey(
        SystemEventSeverity,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic severity (replaces severity field)"
    )
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    class Meta:
        verbose_name = "System Event Log"
        verbose_name_plural = "System Event Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.event_type}: {self.message[:50]}..."


class HealthCheckType(models.Model):
    """Model for storing dynamic health check types"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the check type (e.g., 'database', 'cache')")
    display_name = models.CharField(max_length=100, help_text="Display name for the check type (e.g., 'Database Connection', 'Cache Health')")
    description = models.TextField(blank=True, help_text="Description of the check type")
    is_active = models.BooleanField(default=True, help_text="Whether this check type is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Health Check Type"
        verbose_name_plural = "Health Check Types"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class HealthCheckStatus(models.Model):
    """Model for storing dynamic health check statuses"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True, help_text="Unique identifier for the status (e.g., 'healthy', 'error')")
    display_name = models.CharField(max_length=50, help_text="Display name for the status (e.g., 'Healthy', 'Error')")
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code for UI representation")
    description = models.TextField(blank=True, help_text="Description of the status level")
    is_active = models.BooleanField(default=True, help_text="Whether this status is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Health Check Status"
        verbose_name_plural = "Health Check Statuses"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class SystemHealthCheck(models.Model):
    """Model for monitoring and recording system health metrics"""
    id = models.AutoField(primary_key=True)
    check_type = models.CharField(max_length=100, choices=[
        ('database', 'Database Connection'),
        ('cache', 'Cache Health'),
        ('storage', 'Storage Space'),
        ('network', 'Network Connectivity'),
        ('api', 'API Response Time'),
        ('memory', 'Memory Usage'),
        ('cpu', 'CPU Usage'),
        ('disk_io', 'Disk I/O'),
        ('process', 'Process Health'),
    ])
    # New dynamic field
    check_type_ref = models.ForeignKey(
        HealthCheckType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic check type (replaces check_type field)"
    )
    status = models.CharField(max_length=20, choices=[
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ])
    # New dynamic field
    status_ref = models.ForeignKey(
        HealthCheckStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic status (replaces status field)"
    )
    value = models.FloatField(help_text="Numeric value of the metric")
    unit = models.CharField(max_length=20, blank=True, help_text="Unit of measurement (e.g., %, MB, seconds)")
    threshold_critical = models.FloatField(help_text="Threshold for critical status")
    threshold_warning = models.FloatField(help_text="Threshold for warning status")
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "System Health Check"
        verbose_name_plural = "System Health Checks"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.check_type}: {self.status.upper()} ({self.value}{self.unit})"


class MaintenanceStatus(models.Model):
    """Model for storing dynamic maintenance statuses"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True, help_text="Unique identifier for the status (e.g., 'scheduled', 'completed')")
    display_name = models.CharField(max_length=50, help_text="Display name for the status (e.g., 'Scheduled', 'Completed')")
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code for UI representation")
    description = models.TextField(blank=True, help_text="Description of the status level")
    is_active = models.BooleanField(default=True, help_text="Whether this status is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Maintenance Status"
        verbose_name_plural = "Maintenance Statuses"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class MaintenanceType(models.Model):
    """Model for storing dynamic maintenance types"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the maintenance type (e.g., 'system_update', 'database_maintenance')")
    display_name = models.CharField(max_length=100, help_text="Display name for the maintenance type (e.g., 'System Update', 'Database Maintenance')")
    description = models.TextField(blank=True, help_text="Description of the maintenance type")
    is_active = models.BooleanField(default=True, help_text="Whether this maintenance type is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Maintenance Type"
        verbose_name_plural = "Maintenance Types"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class MaintenanceWindow(models.Model):
    """Model for scheduling and tracking maintenance activities"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='scheduled')
    # New dynamic field
    status_ref = models.ForeignKey(
        MaintenanceStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic status (replaces status field)"
    )
    maintenance_type = models.CharField(max_length=50, choices=[
        ('system_update', 'System Update'),
        ('database_maintenance', 'Database Maintenance'),
        ('security_patch', 'Security Patch'),
        ('backup_restore', 'Backup/Restore'),
        ('infrastructure_upgrade', 'Infrastructure Upgrade'),
    ])
    # New dynamic field
    maintenance_type_ref = models.ForeignKey(
        MaintenanceType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic maintenance type (replaces maintenance_type field)"
    )
    affected_components = models.TextField(help_text="Comma-separated list of affected system components")
    estimated_downtime_minutes = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_created')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_approved')
    notified_users = models.ManyToManyField(User, related_name='maintenance_notifications', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Maintenance Window"
        verbose_name_plural = "Maintenance Windows"
        ordering = ['-scheduled_start']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_start.strftime('%Y-%m-%d %H:%M')} ({self.status})"


class PerformanceMetricType(models.Model):
    """Model for storing dynamic performance metric types"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the metric type (e.g., 'response_time', 'throughput')")
    display_name = models.CharField(max_length=100, help_text="Display name for the metric type (e.g., 'API Response Time', 'Request Throughput')")
    description = models.TextField(blank=True, help_text="Description of the metric type")
    is_active = models.BooleanField(default=True, help_text="Whether this metric type is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Performance Metric Type"
        verbose_name_plural = "Performance Metric Types"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class PerformanceEnvironment(models.Model):
    """Model for storing dynamic performance environments"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the environment (e.g., 'development', 'production')")
    display_name = models.CharField(max_length=100, help_text="Display name for the environment (e.g., 'Development', 'Production')")
    description = models.TextField(blank=True, help_text="Description of the environment")
    is_active = models.BooleanField(default=True, help_text="Whether this environment is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Performance Environment"
        verbose_name_plural = "Performance Environments"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class PerformanceMetric(models.Model):
    """Model for storing system performance data"""
    id = models.AutoField(primary_key=True)
    metric_type = models.CharField(max_length=100, choices=[
        ('response_time', 'API Response Time'),
        ('throughput', 'Request Throughput'),
        ('concurrency', 'Concurrent Users'),
        ('memory_usage', 'Memory Usage'),
        ('cpu_usage', 'CPU Usage'),
        ('database_queries', 'Database Query Time'),
        ('cache_hit_ratio', 'Cache Hit Ratio'),
        ('disk_io', 'Disk I/O'),
    ])
    # New dynamic field
    metric_type_ref = models.ForeignKey(
        PerformanceMetricType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic metric type (replaces metric_type field)"
    )
    value = models.FloatField()
    unit = models.CharField(max_length=20, default='ms')
    timestamp = models.DateTimeField(default=timezone.now)
    component = models.CharField(max_length=100, blank=True, help_text="Specific component being measured")
    environment = models.CharField(max_length=50, choices=[
        ('development', 'Development'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ], default='production')
    # New dynamic field
    environment_ref = models.ForeignKey(
        PerformanceEnvironment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic environment (replaces environment field)"
    )
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = "Performance Metric"
        verbose_name_plural = "Performance Metrics"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_type}: {self.value}{self.unit} ({self.component})"


class NotificationType(models.Model):
    """Model for storing dynamic notification types"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the notification type (e.g., 'info', 'alert')")
    display_name = models.CharField(max_length=100, help_text="Display name for the notification type (e.g., 'Information', 'Alert')")
    description = models.TextField(blank=True, help_text="Description of the notification type")
    is_active = models.BooleanField(default=True, help_text="Whether this notification type is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Type"
        verbose_name_plural = "Notification Types"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class NotificationPriority(models.Model):
    """Model for storing dynamic notification priorities"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True, help_text="Unique identifier for the priority (e.g., 'low', 'high')")
    display_name = models.CharField(max_length=50, help_text="Display name for the priority (e.g., 'Low', 'High')")
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code for UI representation")
    description = models.TextField(blank=True, help_text="Description of the priority level")
    is_active = models.BooleanField(default=True, help_text="Whether this priority is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Priority"
        verbose_name_plural = "Notification Priorities"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class SystemNotification(models.Model):
    """Model for managing system-wide notifications"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('alert', 'Alert'),
        ('maintenance', 'Maintenance Notice'),
        ('system_update', 'System Update'),
    ])
    # New dynamic field
    notification_type_ref = models.ForeignKey(
        NotificationType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic notification type (replaces notification_type field)"
    )
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='normal')
    # New dynamic field
    priority_ref = models.ForeignKey(
        NotificationPriority,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Dynamic priority (replaces priority field)"
    )
    start_datetime = models.DateTimeField(default=timezone.now)
    end_datetime = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True)
    affected_users = models.ManyToManyField(User, blank=True, related_name='system_notifications')
    affected_tenants = models.ManyToManyField('tenants.Tenant', blank=True, related_name='system_notifications')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Notification"
        verbose_name_plural = "System Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.notification_type.upper()}"


class ModelChoice(models.Model):
    """
    Dynamic model choice values - allows tenant-specific model choice tracking.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='core_model_choices'
    )
    model_choice_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'Account', 'Lead'")
    label = models.CharField(max_length=100) # e.g., 'Account', 'Lead'
    order = models.IntegerField(default=0)
    model_choice_is_active = models.BooleanField(default=True, help_text="Whether this model choice is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'model_choice_name']
        unique_together = [('tenant', 'model_choice_name')]
        verbose_name_plural = 'Model Choices'
    
    def __str__(self):
        return self.label


class FieldType(models.Model):
    """
    Dynamic field type values - allows tenant-specific field type tracking.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='core_field_types'
    )
    field_type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'text', 'number'")
    label = models.CharField(max_length=50) # e.g., 'Text', 'Number'
    order = models.IntegerField(default=0)
    field_type_is_active = models.BooleanField(default=True, help_text="Whether this field type is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'field_type_name']
        unique_together = [('tenant', 'field_type_name')]
        verbose_name_plural = 'Field Types'
    
    def __str__(self):
        return self.label


class ModuleChoice(models.Model):
    """
    Dynamic module choice values - allows tenant-specific module choice tracking.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='core_module_choices'
    )
    module_choice_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'leads', 'accounts'")
    label = models.CharField(max_length=100) # e.g., 'Leads', 'Accounts'
    order = models.IntegerField(default=0)
    module_choice_is_active = models.BooleanField(default=True, help_text="Whether this module choice is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'module_choice_name']
        unique_together = [('tenant', 'module_choice_name')]
        verbose_name_plural = 'Module Choices'
    
    def __str__(self):
        return self.label


class ModuleLabel(models.Model):
    MODULE_CHOICES = [
        ('leads', 'Leads'),
        ('accounts', 'Accounts'),
        ('opportunities', 'Opportunities'),
        ('cases', 'Cases'),
        ('proposals', 'Proposals'),
        ('products', 'Products'),
        ('tasks', 'Tasks'),
        ('dashboard', 'Dashboard'),
        ('reports', 'Reports'),
        ('commissions', 'Commissions'),
    ]

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='core_module_labels'
    )
    module_key = models.CharField(max_length=50, choices=MODULE_CHOICES)
    # New dynamic field
    module_key_ref = models.ForeignKey(
        ModuleChoice,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='module_labels',
        help_text="Dynamic module key (replaces module_key field)"
    )
    custom_label = models.CharField(max_length=100, help_text="e.g., 'Prospects' instead of 'Leads'")
    module_label_is_active = models.BooleanField(default=True, help_text="Whether this module label is active")

    def __str__(self):
        return f"{self.module_key}: {self.custom_label}"


class AssignmentRuleType(models.Model):
    """
    Dynamic assignment rule type values - allows tenant-specific rule type tracking.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='core_assignment_rule_types'
    )
    rule_type_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'round_robin', 'territory'")
    label = models.CharField(max_length=100) # e.g., 'Round Robin', 'Territory-Based'
    order = models.IntegerField(default=0)
    rule_type_is_active = models.BooleanField(default=True, help_text="Whether this rule type is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'rule_type_name']
        unique_together = [('tenant', 'rule_type_name')]
        verbose_name_plural = 'Assignment Rule Types'
    
    def __str__(self):
        return self.label
