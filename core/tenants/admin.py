from django.contrib import admin
from .models import Tenant, TenantLifecycleEvent, TenantMigrationRecord, TenantUsageMetric, TenantCloneHistory, TenantFeatureEntitlement
from .data_preservation import TenantDataPreservation, TenantDataRestoration, TenantDataPreservationStrategy, TenantDataPreservationSchedule
from .automated_lifecycle import AutomatedTenantLifecycleRule, AutomatedTenantLifecycleEvent, TenantLifecycleWorkflowExecution, TenantSuspensionWorkflow, TenantTerminationWorkflow


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'is_suspended', 'is_archived', 'created_at')
    list_filter = ('is_active', 'is_suspended', 'is_archived', 'subscription_status', 'created_at')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TenantLifecycleEvent)
class TenantLifecycleEventAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'event_type', 'timestamp', 'triggered_by')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('tenant__name', 'reason')
    readonly_fields = ('timestamp',)


@admin.register(TenantMigrationRecord)
class TenantMigrationRecordAdmin(admin.ModelAdmin):
    list_display = ('source_tenant', 'destination_tenant', 'migration_type', 'status', 'started_at')
    list_filter = ('migration_type', 'status', 'started_at')
    search_fields = ('source_tenant__name', 'destination_tenant__name')


@admin.register(TenantUsageMetric)
class TenantUsageMetricAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'metric_type', 'value', 'timestamp')
    list_filter = ('metric_type', 'timestamp')
    search_fields = ('tenant__name',)


@admin.register(TenantCloneHistory)
class TenantCloneHistoryAdmin(admin.ModelAdmin):
    list_display = ('original_tenant', 'cloned_tenant', 'clone_type', 'status', 'started_at')
    list_filter = ('clone_type', 'status', 'started_at')
    search_fields = ('original_tenant__name', 'cloned_tenant__name')


@admin.register(TenantFeatureEntitlement)
class TenantFeatureEntitlementAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'feature_name', 'is_enabled', 'entitlement_type')
    list_filter = ('is_enabled', 'entitlement_type')
    search_fields = ('tenant__name', 'feature_name')


@admin.register(TenantDataPreservation)
class TenantDataPreservationAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'preservation_type', 'status', 'file_size_mb', 'preservation_date')
    list_filter = ('preservation_type', 'status', 'preservation_date')
    search_fields = ('tenant__name',)


@admin.register(TenantDataRestoration)
class TenantDataRestorationAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'status', 'started_at', 'completed_at', 'progress_percentage')
    list_filter = ('status', 'started_at')
    search_fields = ('tenant__name',)


@admin.register(TenantDataPreservationStrategy)
class TenantDataPreservationStrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'preservation_frequency', 'is_active', 'retention_period_days')
    list_filter = ('is_active', 'preservation_frequency')
    search_fields = ('name',)


@admin.register(TenantDataPreservationSchedule)
class TenantDataPreservationScheduleAdmin(admin.ModelAdmin):
    list_display = ('strategy', 'tenant', 'next_scheduled_run', 'is_active')
    list_filter = ('is_active', 'next_scheduled_run')
    search_fields = ('strategy__name', 'tenant__name')


@admin.register(AutomatedTenantLifecycleRule)
class AutomatedTenantLifecycleRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'condition_type', 'action_type', 'is_active', 'evaluation_frequency')
    list_filter = ('is_active', 'condition_type', 'action_type', 'evaluation_frequency')
    search_fields = ('name', 'description')


@admin.register(AutomatedTenantLifecycleEvent)
class AutomatedTenantLifecycleEventAdmin(admin.ModelAdmin):
    list_display = ('rule', 'tenant', 'event_type', 'status', 'triggered_at')
    list_filter = ('event_type', 'status', 'triggered_at')
    search_fields = ('rule__name', 'tenant__name')





@admin.register(TenantLifecycleWorkflowExecution)
class TenantLifecycleWorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'tenant', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at')
    search_fields = ('workflow__name', 'tenant__name')


@admin.register(TenantSuspensionWorkflow)
class TenantSuspensionWorkflowAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'status', 'initiated_by', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at')
    search_fields = ('tenant__name',)


@admin.register(TenantTerminationWorkflow)
class TenantTerminationWorkflowAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'status', 'initiated_by', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at')
    search_fields = ('tenant__name',)
