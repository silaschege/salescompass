from django.contrib import admin
from .models import (
    SettingGroup, Setting, SettingType,
    CustomField, ModuleLabel,
    TeamRole, Territory, TeamMember, AssignmentRule, PipelineStage,
    EmailIntegration, ActionType, OperatorType
)

@admin.register(SettingGroup)
class SettingGroupAdmin(admin.ModelAdmin):
    list_display = ('setting_group_name', 'setting_group_description')
    
@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('setting_name', 'group', 'setting_type', 'is_visible')
    list_filter = ('group', 'setting_type')

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'field_label', 'field_type', 'is_required', 'is_visible')
    list_filter = ('model_name', 'field_type', 'is_visible')
    search_fields = ('field_name', 'field_label')

@admin.register(ModuleLabel)
class ModuleLabelAdmin(admin.ModelAdmin):
    list_display = ('module_key', 'custom_label')
    list_filter = ('module_key',)

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'manager', 'status')
    list_filter = ('status', 'role')

@admin.register(AssignmentRule)
class AssignmentRuleAdmin(admin.ModelAdmin):
    list_display = ('assignment_rule_name', 'module', 'rule_type', 'priority', 'rule_is_active')
    list_filter = ('module', 'rule_type', 'rule_is_active')

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('pipeline_stage_name', 'pipeline_type', 'order', 'probability', 'is_won_stage', 'is_lost_stage')
    list_filter = ('pipeline_type', 'is_won_stage', 'is_lost_stage')
    ordering = ('pipeline_type', 'order')

@admin.register(EmailIntegration)
class EmailIntegrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'email_address', 'integration_is_active', 'last_sync')
    list_filter = ('provider', 'integration_is_active')
    readonly_fields = ('last_sync',)
