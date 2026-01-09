from django.contrib import admin
from .models import Sale, SalesCommission, SalesCommissionRule, TerritoryPerformance, TerritoryAssignmentOptimizer, TeamMemberTerritoryMetrics, SalesTarget, SalesPerformanceMetric

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['product', 'account', 'sales_rep', 'amount', 'sale_date', 'sale_type']
    list_filter = ['sale_type', 'sale_date']
    search_fields = ['account__name', 'product__name']

@admin.register(SalesCommission)
class SalesCommissionAdmin(admin.ModelAdmin):
    list_display = ['sale', 'sales_rep', 'amount', 'status', 'date_earned']
    list_filter = ['status', 'date_earned']
    search_fields = ['sales_rep__email']

@admin.register(SalesCommissionRule)
class SalesCommissionRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'percentage', 'flat_amount', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active', 'product_type']
    search_fields = ['name']

@admin.register(TerritoryPerformance)
class TerritoryPerformanceAdmin(admin.ModelAdmin):
    list_display = ['territory', 'period_start', 'period_end', 'total_revenue', 'total_deals']
    list_filter = ['period_start', 'territory']

@admin.register(TerritoryAssignmentOptimizer)
class TerritoryAssignmentOptimizerAdmin(admin.ModelAdmin):
    list_display = ['territory', 'optimization_type', 'status', 'optimization_date']
    list_filter = ['status', 'optimization_type']

@admin.register(TeamMemberTerritoryMetrics)
class TeamMemberTerritoryMetricsAdmin(admin.ModelAdmin):
    list_display = ['team_member', 'personal_revenue', 'personal_deals', 'performance_score']
    search_fields = ['team_member__user__email']

@admin.register(SalesTarget)
class SalesTargetAdmin(admin.ModelAdmin):
    list_display = ['target_type', 'metric_name', 'target_value', 'start_date', 'end_date']
    list_filter = ['target_type', 'metric_name']

@admin.register(SalesPerformanceMetric)
class SalesPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ['date', 'metric_name', 'value', 'dimension']
    list_filter = ['dimension', 'metric_name', 'date']
