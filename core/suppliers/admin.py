from django.contrib import admin
from .models import Supplier, SupplierCategory, SupplierContact, SupplierDocument, SupplierPerformanceReview


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['supplier_name', 'supplier_code', 'category', 'status', 'is_active']
    list_filter = ['status', 'is_active', 'category']
    search_fields = ['supplier_name', 'supplier_code', 'email']


@admin.register(SupplierCategory)
class SupplierCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']


@admin.register(SupplierContact)
class SupplierContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'email', 'is_primary']


@admin.register(SupplierDocument)
class SupplierDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'document_type', 'expiry_date']


@admin.register(SupplierPerformanceReview)
class SupplierPerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'date', 'delivery_rating', 'quality_rating', 'responsiveness_rating']
    list_filter = ['date']
    search_fields = ['supplier__supplier_name']
