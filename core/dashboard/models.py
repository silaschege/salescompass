from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
from core.models import User

# Dynamic models have replaced the hardcoded choices
# The legacy choices have been removed as they are no longer needed


class WidgetType(TenantModel):
    """
    Dynamic widget type values - allows tenant-specific widget type tracking.
    """
    widget_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'revenue', 'pipeline'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Revenue Chart', 'Sales Pipeline'
    order = models.IntegerField(default=0)
    widget_type_is_active = models.BooleanField(default=True, help_text="Whether this widget type is active")
    widget_type_created_at = models.DateTimeField(auto_now_add=True)
    widget_type_updated_at = models.DateTimeField(auto_now=True)
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'widget_name']
        unique_together = [('tenant', 'widget_name')]
        verbose_name_plural = 'Widget Types'
    
    def __str__(self):
        return self.label


class WidgetCategory(TenantModel):
    """
    Dynamic widget category values - allows tenant-specific category tracking.
    """
    category_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'leads', 'opportunities'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Leads', 'Opportunities'
    order = models.IntegerField(default=0)
    widget_category_is_active = models.BooleanField(default=True, help_text="Whether this category is active")
    widget_category_created_at = models.DateTimeField(auto_now_add=True)
    widget_category_updated_at = models.DateTimeField(auto_now=True)
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'category_name']
        unique_together = [('tenant', 'category_name')]
        verbose_name_plural = 'Widget Categories'
    
    def __str__(self):
        return self.label


class DashboardWidget(TenantModel):
    # Field that was previously using hardcoded choices
    widget_type_old = models.CharField(max_length=50, verbose_name="Widget Type (Legacy)")
    # New dynamic field
    widget_type_ref = models.ForeignKey(
        WidgetType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='dashboard_widgets',
        help_text="Dynamic widget type (replaces widget_type_old field)"
    )
    widget_name = models.CharField(max_length=255, verbose_name="Widget Name")  # Renamed from 'name' to avoid conflict
    widget_description = models.TextField()  # Renamed from 'description' to avoid conflict with base class
    category_old = models.CharField(max_length=50, default='general', verbose_name="Category (Legacy)")
    # New dynamic field
    category_ref = models.ForeignKey(
        WidgetCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='dashboard_widgets',
        help_text="Dynamic category (replaces category_old field)"
    )
    template_path = models.CharField(max_length=255)
    widget_is_active = models.BooleanField(default=True) # Renamed from 'is_active' to avoid conflict with base class
    widget_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    widget_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.widget_name

    class Meta:
        unique_together = [('tenant', 'widget_type_old')]  # Ensuring uniqueness per tenant based on the old field


class DashboardConfig(TenantModel):
    """
    User-specific dashboard configuration.
    Stores dashboard layouts and widget positions for each user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_configs')
    dashboard_name = models.CharField(max_length=255)
    dashboard_description = models.TextField(blank=True)
    layout = models.JSONField(default=dict, help_text="Widget layout configuration")
    widgets = models.JSONField(default=list, help_text="List of widgets with their positions and settings")
    is_default = models.BooleanField(default=False, help_text="Whether this is the user's default dashboard")
    is_shared = models.BooleanField(default=False, help_text="Whether this dashboard is shared with others")
    role_based = models.CharField(max_length=50, blank=True, help_text="Role this dashboard is designed for")
    config_created_at = models.DateTimeField(auto_now_add=True)
    config_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dashboard_name} - {self.user.email}"

    class Meta:
        ordering = ['-is_default', '-config_created_at']
