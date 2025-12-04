from django.contrib import admin
from .models import FeatureFlag, FeatureTarget


class FeatureTargetInline(admin.TabularInline):
    model = FeatureTarget
    extra = 1


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['key', 'name', 'is_active', 'rollout_percentage', 'created_by']
    list_filter = ['is_active']
    search_fields = ['key', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [FeatureTargetInline]


@admin.register(FeatureTarget)
class FeatureTargetAdmin(admin.ModelAdmin):
    list_display = ['feature_flag', 'target_type', 'target_value', 'is_active']
    list_filter = ['target_type', 'is_active']
    search_fields = ['feature_flag__key', 'target_value']
