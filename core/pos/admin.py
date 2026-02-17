from django.contrib import admin
from .models import (
    POSTerminal, POSSession, POSTransaction, POSTransactionLine,
    POSPayment, POSReceipt, POSCashDrawer, POSCashMovement,
    POSRefund, POSRefundLine
)


class POSTransactionLineInline(admin.TabularInline):
    model = POSTransactionLine
    extra = 0
    readonly_fields = ['line_total', 'product_name', 'product_sku']


class POSPaymentInline(admin.TabularInline):
    model = POSPayment
    extra = 0


class POSRefundLineInline(admin.TabularInline):
    model = POSRefundLine
    extra = 0


@admin.register(POSTerminal)
class POSTerminalAdmin(admin.ModelAdmin):
    list_display = [
        'terminal_name', 'terminal_code', 'warehouse', 
        'is_active', 'is_online', 'tenant'
    ]
    list_filter = ['is_active', 'is_online', 'warehouse', 'tenant']
    search_fields = ['terminal_name', 'terminal_code', 'location']
    ordering = ['terminal_name']


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_number', 'terminal', 'cashier', 'status',
        'opened_at', 'closed_at', 'total_sales', 'total_transactions'
    ]
    list_filter = ['status', 'terminal', 'tenant']
    search_fields = ['session_number', 'cashier__username', 'cashier__email']
    ordering = ['-opened_at']
    date_hierarchy = 'opened_at'
    readonly_fields = [
        'session_number', 'total_sales', 'total_transactions',
        'total_refunds', 'total_discounts'
    ]


@admin.register(POSTransaction)
class POSTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'terminal', 'customer', 'status',
        'total_amount', 'amount_paid', 'cashier', 'created_at'
    ]
    list_filter = ['status', 'terminal', 'tenant']
    search_fields = [
        'transaction_number', 'customer__account_name',
        'customer_name', 'customer_phone'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [POSTransactionLineInline, POSPaymentInline]
    readonly_fields = [
        'transaction_number', 'subtotal', 'tax_amount',
        'total_amount', 'amount_paid', 'change_due'
    ]


@admin.register(POSPayment)
class POSPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction', 'payment_method', 'amount', 'status',
        'reference_number', 'created_at'
    ]
    list_filter = ['payment_method', 'status', 'tenant']
    search_fields = ['transaction__transaction_number', 'reference_number']
    ordering = ['-created_at']


@admin.register(POSReceipt)
class POSReceiptAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'transaction', 'receipt_type',
        'is_printed', 'printed_count', 'created_at'
    ]
    list_filter = ['receipt_type', 'is_printed', 'tenant']
    search_fields = ['receipt_number', 'transaction__transaction_number']
    ordering = ['-created_at']


@admin.register(POSCashDrawer)
class POSCashDrawerAdmin(admin.ModelAdmin):
    list_display = [
        'terminal', 'status', 'current_cash',
        'last_opened_at', 'last_opened_by'
    ]
    list_filter = ['status', 'tenant']
    readonly_fields = ['current_cash', 'last_opened_at']


@admin.register(POSCashMovement)
class POSCashMovementAdmin(admin.ModelAdmin):
    list_display = [
        'drawer', 'movement_type', 'amount', 'balance_after',
        'performed_by', 'created_at'
    ]
    list_filter = ['movement_type', 'tenant']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(POSRefund)
class POSRefundAdmin(admin.ModelAdmin):
    list_display = [
        'refund_number', 'original_transaction', 'refund_type',
        'status', 'refund_amount', 'created_at'
    ]
    list_filter = ['refund_type', 'status', 'tenant']
    search_fields = [
        'refund_number', 'original_transaction__transaction_number'
    ]
    ordering = ['-created_at']
    inlines = [POSRefundLineInline]
    readonly_fields = ['refund_number']
