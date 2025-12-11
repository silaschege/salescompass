from django.contrib import admin
from .models import CommissionPlan, CommissionRule, UserCommissionPlan, Quota, Commission, Adjustment

class CommissionRuleInline(admin.TabularInline):
    model = CommissionRule
    fk_name = 'commission_rule_plan'
    extra = 1

@admin.register(CommissionPlan)
class CommissionPlanAdmin(admin.ModelAdmin):
    list_display = ('commission_plan_name', 'basis', 'period', 'commission_plan_is_active')
    inlines = [CommissionRuleInline]

@admin.register(UserCommissionPlan)
class UserCommissionPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_commission_plan', 'start_date', 'end_date')
    list_filter = ('user_commission_plan', 'start_date')

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
