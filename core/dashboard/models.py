from django.db import models
from core.models import TenantModel, User


class DashboardConfig(TenantModel):
    """
    Custom dashboard configuration allowing users to arrange widgets.
    Part of Dashboard Builder system.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_configs')
    name = models.CharField(max_length=255, help_text="Dashboard name, e.g., 'Sales Overview', 'Manager Dashboard'")
    description = models.TextField(blank=True)
    
    is_default = models.BooleanField(default=False, help_text="Set as default dashboard for this user")
    is_shared = models.BooleanField(default=False, help_text="Share with all users in tenant")
    
    # Layout configuration stored as JSON
    layout = models.JSONField(
        default=dict,
        help_text="Grid layout configuration with widget placements"
    )
    
    # Widget-specific settings
    widget_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom settings per widget"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    tenant_id = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-updated_at']
        unique_together = [('user', 'name', 'tenant_id')]
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['tenant_id', 'is_shared']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"
    
    def set_as_default(self):
        """Set this dashboard as default."""
        DashboardConfig.objects.filter(user=self.user, is_default=True).update(is_default=False)
        self.is_default = True
        self.save(update_fields=['is_default'])


class DashboardWidget(models.Model):
    """
    Registry of available dashboard widgets.
    """
    WIDGET_TYPE_CHOICES = [
        # Core Features
        ('revenue', 'Revenue Chart'),
        ('pipeline', 'Sales Pipeline'),
        ('tasks', 'Task List'),
        ('leads', 'Lead Metrics'),
        ('accounts', 'Accounts Overview'),
        ('opportunities', 'Opportunities Overview'),
        
        # Customer Engagement
        ('cases', 'Support Cases'),
        ('nps', 'NPS Score'),
        ('communication', 'Communication Stats'),
        ('engagement', 'Engagement Metrics'),
        
        # Sales & Marketing
        ('sales', 'Sales Performance'),
        ('products', 'Product Metrics'),
        ('proposals', 'Proposal Pipeline'),
        ('marketing', 'Marketing Campaigns'),
        ('commissions', 'Commission Tracking'),
        
        # Analytics & Reporting
        ('reports', 'Report Dashboard'),
        ('leaderboard', 'Sales Leaderboard'),
        ('activity', 'Recent Activity'),
        
        # Automation & Settings
        ('automation', 'Automation Workflows'),
        ('settings', 'System Settings'),
        
        # Learning & Development
        ('learn', 'Learning Progress'),
        
        # Developer & Admin
        ('developer', 'Developer Tools'),
        ('billing', 'Billing Overview'),
        
        # Control Plane
        ('infrastructure', 'Infrastructure Usage'),
        ('tenants', 'Tenant Management'),
        ('audit_logs', 'Audit Logs'),
        ('feature_flags', 'Feature Flags'),
        ('global_alerts', 'Global Alerts'),
    ]
    
    CATEGORY_CHOICES = [
        ('leads', 'Leads'),
        ('opportunities', 'Opportunities'),
        ('revenue', 'Revenue'),
        ('sales', 'Sales'),
        ('tasks', 'Tasks'),
        ('cases', 'Cases'),
        ('accounts', 'Accounts'),
        ('products', 'Products'),
        ('proposals', 'Proposals'),
        ('communication', 'Communication'),
        ('engagement', 'Engagement'),
        ('nps', 'NPS'),
        ('analytics', 'Analytics'),
        ('billing', 'Billing'),
        ('commissions', 'Commissions'),
        ('infrastructure', 'Infrastructure'),
        ('tenants', 'Tenants'),
        ('marketing', 'Marketing'),
        ('automation', 'Automation'),
        ('learn', 'Learning'),
        ('developer', 'Developer'),
        ('control_plane', 'Control Plane'),
        ('general', 'General'),
    ]
    
    widget_type = models.CharField(max_length=50, unique=True, choices=WIDGET_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    template_path = models.CharField(max_length=255)
    required_permission = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, default='bi-grid-3x3-gap', help_text="Bootstrap icon class (e.g., 'bi-graph-up')")
    default_span = models.IntegerField(default=6)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name
