from django.contrib import admin
from .models import (
    Warehouse, StockLocation, StockLevel, StockMovement,
    StockAdjustment, StockAdjustmentLine, ReorderRule, StockAlert
)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['warehouse_name', 'warehouse_code', 'city', 'country', 'is_active', 'is_default', 'tenant']
    list_filter = ['is_active', 'is_default', 'country', 'tenant']
    search_fields = ['warehouse_name', 'warehouse_code', 'city']
    ordering = ['warehouse_name']


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ['location_code', 'location_name', 'warehouse', 'aisle', 'shelf', 'bin', 'is_active']
    list_filter = ['is_active', 'warehouse', 'tenant']
    search_fields = ['location_code', 'location_name']
    ordering = ['warehouse', 'location_code']


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'location', 'quantity', 'reserved_quantity', 'available_quantity', 'updated_at']
    list_filter = ['warehouse', 'tenant']
    search_fields = ['product__product_name', 'product__sku']
    ordering = ['product', 'warehouse']
    readonly_fields = ['available_quantity', 'stock_value']

    def available_quantity(self, obj):
        return obj.available_quantity
    available_quantity.short_description = 'Available'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'from_warehouse', 'to_warehouse', 'performed_by', 'created_at']
    list_filter = ['movement_type', 'from_warehouse', 'to_warehouse', 'tenant']
    search_fields = ['product__product_name', 'product__sku', 'notes']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


class StockAdjustmentLineInline(admin.TabularInline):
    model = StockAdjustmentLine
    extra = 0
    readonly_fields = ['variance']

    def variance(self, obj):
        if obj.pk:
            return obj.variance
        return '-'


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['adjustment_number', 'warehouse', 'reason', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'reason', 'warehouse', 'tenant']
    search_fields = ['adjustment_number', 'notes']
    ordering = ['-created_at']
    inlines = [StockAdjustmentLineInline]
    readonly_fields = ['created_at', 'approved_at', 'applied_at']


@admin.register(ReorderRule)
class ReorderRuleAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'min_quantity', 'reorder_quantity', 'lead_time_days', 'is_active']
    list_filter = ['is_active', 'warehouse', 'tenant']
    search_fields = ['product__product_name', 'product__sku']
    ordering = ['product', 'warehouse']


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'alert_type', 'status', 'current_quantity', 'threshold_quantity', 'created_at']
    list_filter = ['alert_type', 'status', 'warehouse', 'tenant']
    search_fields = ['product__product_name', 'message']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
