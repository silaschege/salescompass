from django.contrib import admin
from .models import (
    SettingGroup, Setting, SettingChangeLog,
    CustomField, ModuleLabel,
    TeamRole, Territory, TeamMember, Quota, AssignmentRule, PipelineStage,
    EmailIntegration, APIKey, Webhook
)

@admin.register(SettingGroup)
class SettingGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    
@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'setting_type', 'is_active')
    list_filter = ('group', 'setting_type')

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'field_name', 'field_label', 'field_type', 'is_required', 'is_active')
    list_filter = ('model_name', 'field_type', 'is_active')
    search_fields = ('field_name', 'field_label')

@admin.register(ModuleLabel)
class ModuleLabelAdmin(admin.ModelAdmin):
    list_display = ('module_key', 'custom_label', 'custom_label_plural')
    list_filter = ('module_key',)

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'manager', 'status')
    list_filter = ('status', 'role')

@admin.register(AssignmentRule)
class AssignmentRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'module', 'rule_type', 'priority', 'is_active')
    list_filter = ('module', 'rule_type', 'is_active')
    filter_horizontal = ('assignees',)

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'pipeline_type', 'order', 'probability', 'is_closed', 'is_won', 'is_active')
    list_filter = ('pipeline_type', 'is_closed', 'is_won', 'is_active')
    ordering = ('pipeline_type', 'order')

@admin.register(EmailIntegration)
class EmailIntegrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'email_address', 'sync_enabled', 'last_synced')
    list_filter = ('provider', 'sync_enabled')
    readonly_fields = ('last_synced',)

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'key_prefix', 'created_by', 'last_used', 'is_active')
    list_filter = ('is_active', 'created_by')
    readonly_fields = ('key_prefix', 'key_hash', 'last_used')

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active', 'success_count', 'failure_count', 'last_triggered')
    list_filter = ('is_active',)
    readonly_fields = ('last_triggered', 'success_count', 'failure_count')

