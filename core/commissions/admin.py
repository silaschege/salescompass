from django.contrib import admin
from .models import CommissionPlan, CommissionRule, UserCommissionPlan, Quota, Commission, Adjustment

class CommissionRuleInline(admin.TabularInline):
    model = CommissionRule
    extra = 1

@admin.register(CommissionPlan)
class CommissionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'basis', 'period', 'is_active')
    inlines = [CommissionRuleInline]

@admin.register(UserCommissionPlan)
class UserCommissionPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date')
    list_filter = ('plan', 'start_date')

@admin.register(Quota)
class QuotaAdmin(admin.ModelAdmin):
    list_display = ('user', 'period_start', 'period_end', 'target_amount')
    list_filter = ('period_start',)

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'opportunity', 'amount', 'rate_applied', 'date_earned', 'status')
    list_filter = ('status', 'date_earned', 'user')
    readonly_fields = ('date_earned',)

@admin.register(Adjustment)
class AdjustmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'amount', 'date')
    list_filter = ('type', 'date', 'user')
