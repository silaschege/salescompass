from django.contrib import admin
from .models import Invoice, InvoiceLine, Payment

class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'status', 'issue_date', 'due_date', 'total_amount']
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_number', 'customer__account_name']
    inlines = [InvoiceLineInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_date', 'payment_method']
    list_filter = ['payment_method', 'payment_date']
