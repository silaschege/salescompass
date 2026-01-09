from django.contrib import admin
from .models import(
     Tenant, TenantLifecycleEvent, 
     TenantMigrationRecord, TenantUsageMetric, 
     TenantCloneHistory, TenantFeatureEntitlement, 
     TenantSettings, SettingType, SettingGroup, 
     Setting, WhiteLabelSettings, OverageAlert, 
     NotificationTemplate, Notification, AlertThreshold,
    TenantDataIsolationAudit, TenantDataIsolationViolation
)
     

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'is_suspended', 'is_archived', 'created_at']
    list_filter = ['is_active', 'is_suspended', 'is_archived', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TenantLifecycleEvent)
class TenantLifecycleEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'tenant', 'timestamp', 'triggered_by']
    list_filter = ['event_type', 'timestamp']
    readonly_fields = ['timestamp']


@admin.register(TenantMigrationRecord)
class TenantMigrationRecordAdmin(admin.ModelAdmin):
    list_display = ['migration_type', 'source_tenant', 'destination_tenant', 'status', 'started_at']
    list_filter = ['migration_type', 'status', 'started_at']



@admin.register(TenantCloneHistory)
class TenantCloneHistoryAdmin(admin.ModelAdmin):
    list_display = ['original_tenant', 'cloned_tenant', 'clone_type', 'status', 'started_at']
    list_filter = ['clone_type', 'status', 'started_at']




@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'primary_color', 'secondary_color', 'time_zone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SettingType)
class SettingTypeAdmin(admin.ModelAdmin):
    list_display = ['setting_type_name', 'label', 'tenant', 'setting_type_is_active']
    list_filter = ['setting_type_is_active', 'tenant']


@admin.register(SettingGroup)
class SettingGroupAdmin(admin.ModelAdmin):
    list_display = ['setting_group_name', 'tenant', 'setting_group_is_active']
    list_filter = ['setting_group_is_active', 'tenant']


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['setting_name', 'tenant', 'group', 'setting_type']
    list_filter = ['setting_type', 'tenant']


@admin.register(WhiteLabelSettings)
class WhiteLabelSettingsAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'brand_name', 'primary_color', 'is_active']
    list_filter = ['is_active', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Branding Assets', {
            'fields': ('logo', 'logo_small', 'favicon', 'brand_image')
        }),
        ('Brand Colors', {
            'fields': ('primary_color', 'secondary_color', 'accent_color', 'background_color', 
                      'login_background_color', 'login_text_color')
        }),
        ('Brand Text', {
            'fields': ('brand_name', 'tagline', 'copyright_text')
        }),
        ('Domain Settings', {
            'fields': ('custom_domain', 'subdomain')
        }),
        ('Display Options', {
            'fields': ('show_brand_name', 'show_logo', 'show_tagline', 'is_active')
        }),
        ('Legal & Support Links', {
            'fields': ('privacy_policy_url', 'terms_of_service_url', 'support_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )



@admin.register(TenantUsageMetric)
class TenantUsageMetricAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'metric_type', 'value', 'unit', 'timestamp']
    list_filter = ['metric_type', 'unit', 'timestamp', 'tenant']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    search_fields = ['tenant__name', 'metric_type']
    
    fieldsets = (
        ('Tenant Information', {
            'fields': ('tenant',)
        }),
        ('Metric Details', {
            'fields': ('metric_type', 'value', 'unit')
        }),
        ('Time Period', {
            'fields': ('period_start', 'period_end', 'timestamp')
        }),
    )



@admin.register(TenantFeatureEntitlement)
class TenantFeatureEntitlementAdmin(admin.ModelAdmin):
    list_display = ['feature_name', 'tenant', 'feature_key', 'is_enabled', 'entitlement_type', 'created_at']
    list_filter = ['is_enabled', 'entitlement_type', 'created_at', 'tenant']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['feature_key', 'feature_name', 'tenant__name']
    fieldsets = (
        ('Feature Information', {
            'fields': ('tenant', 'feature_key', 'feature_name')
        }),
        ('Entitlement Details', {
            'fields': ('is_enabled', 'entitlement_type')
        }),
        ('Trial Period', {
            'fields': ('trial_start_date', 'trial_end_date'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OverageAlert)
class OverageAlertAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'metric_type', 'threshold_percentage', 'alert_level', 'is_resolved', 'created_at']
    list_filter = ['alert_level', 'is_resolved', 'created_at', 'tenant', 'metric_type']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['tenant__name', 'metric_type']
    fieldsets = (
        ('Tenant Information', {
            'fields': ('tenant',)
        }),
        ('Alert Details', {
            'fields': ('metric_type', 'threshold_value', 'current_value', 'threshold_percentage', 'alert_level')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['name', 'subject']
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'subject', 'message_body')
        }),
        ('Configuration', {
            'fields': ('notification_type', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'tenant', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'severity', 'is_read', 'delivery_method', 'created_at', 'tenant']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['title', 'message', 'tenant__name', 'user__username']
    fieldsets = (
        ('Notification Information', {
            'fields': ('tenant', 'user', 'title', 'message')
        }),
        ('Configuration', {
            'fields': ('notification_type', 'severity', 'delivery_method')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'sent_at')
        }),
        ('Related Objects', {
            'fields': ('related_object_id', 'related_object_type'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AlertThreshold)
class AlertThresholdAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'metric_type', 'threshold_percentage', 'alert_level', 'is_active', 'created_at']
    list_filter = ['alert_level', 'is_active', 'created_at', 'tenant', 'metric_type']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['tenant__name', 'metric_type']
    fieldsets = (
        ('Tenant Information', {
            'fields': ('tenant',)
        }),
        ('Threshold Details', {
            'fields': ('metric_type', 'threshold_percentage', 'alert_level', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TenantDataIsolationAudit)
class TenantDataIsolationAuditAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'audit_date', 'audit_type', 'status', 'total_records_checked', 'violations_found', 'auditor']
    list_filter = ['audit_type', 'status', 'audit_date', 'tenant', 'auditor']
    readonly_fields = ['created_at', 'updated_at', 'audit_date']
    search_fields = ['tenant__name', 'auditor__username']
    fieldsets = (
        ('Tenant Information', {
            'fields': ('tenant', 'auditor')
        }),
        ('Audit Details', {
            'fields': ('audit_type', 'status', 'total_records_checked', 'violations_found')
        }),
        ('Results', {
            'fields': ('details', 'notes')
        }),
        ('Timestamps', {
            'fields': ('audit_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TenantDataIsolationViolation)
class TenantDataIsolationViolationAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'record_id', 'violation_type', 'severity', 'resolution_status', 'created_at']
    list_filter = ['violation_type', 'severity', 'resolution_status', 'created_at', 'model_name']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['model_name', 'record_id']
    fieldsets = (
        ('Audit Information', {
            'fields': ('audit',)
        }),
        ('Violation Details', {
            'fields': ('model_name', 'record_id', 'field_name', 'violation_type', 'severity')
        }),
        ('Tenants', {
            'fields': ('expected_tenant', 'actual_tenant')
        }),
        ('Resolution', {
            'fields': ('resolution_status', 'resolved_at', 'resolved_by', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )