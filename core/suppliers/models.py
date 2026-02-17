"""
Suppliers App - Vendor/Supplier management for SalesCompass CRM.
"""
from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User


class SupplierCategory(TenantModel):
    """Classification for suppliers."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Supplier Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Supplier(TenantModel):
    """
    Vendor/Supplier master data.
    """
    # Basic Information
    supplier_name = models.CharField(max_length=255)
    supplier_code = models.CharField(max_length=50, blank=True, help_text="Internal supplier code")
    category = models.ForeignKey(SupplierCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='suppliers')
    
    # Contact Details
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Business Information
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax/VAT ID")
    registration_number = models.CharField(max_length=100, blank=True)
    
    # Banking
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    
    # Terms
    payment_terms = models.CharField(max_length=50, default='Net 30', help_text="e.g., Net 30, Net 60")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Classification
    CLASSIFICATION_CHOICES = [
        ('strategic', 'Strategic'),
        ('preferred', 'Preferred'),
        ('transactional', 'Transactional'),
        ('approved', 'Approved'),
        ('probation', 'Probation'),
    ]
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, default='transactional')
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
        ('pending', 'Pending Approval'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    # Performance Metrics
    delivery_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="0.00 to 5.00")
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="0.00 to 5.00")
    responsiveness_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="0.00 to 5.00")
    overall_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_suppliers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['supplier_name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def __str__(self):
        return self.supplier_name
    
    @property
    def full_address(self):
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.postal_code, self.country]
        return ', '.join(p for p in parts if p)

    def update_ratings(self):
        """Recalculate average ratings from performance reviews."""
        reviews = self.performance_reviews.all()
        if not reviews.exists():
            return
            
        count = reviews.count()
        self.delivery_rating = sum(r.delivery_rating for r in reviews) / count
        self.quality_rating = sum(r.quality_rating for r in reviews) / count
        self.responsiveness_rating = sum(r.responsiveness_rating for r in reviews) / count
        
        # Overall score is average of the three metrics
        self.overall_score = (self.delivery_rating + self.quality_rating + self.responsiveness_rating) / 3
        self.save(update_fields=['delivery_rating', 'quality_rating', 'responsiveness_rating', 'overall_score'])

class SupplierPerformanceReview(TenantModel):
    """Periodic performance review for a supplier."""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance_reviews')
    date = models.DateField()
    
    # Metrics (1.00 to 5.00)
    delivery_rating = models.DecimalField(max_digits=3, decimal_places=2, help_text="Rate 1-5")
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, help_text="Rate 1-5")
    responsiveness_rating = models.DecimalField(max_digits=3, decimal_places=2, help_text="Rate 1-5")
    
    comments = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Review for {self.supplier.supplier_name} on {self.date}"

    @property
    def overall_score(self):
        """Calculate the average of the three rating metrics."""
        return (self.delivery_rating + self.quality_rating + self.responsiveness_rating) / 3

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.supplier.update_ratings()


class SupplierContact(TenantModel):
    """Additional contacts for a supplier."""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.supplier.supplier_name})"


class SupplierDocument(TenantModel):
    """Documents attached to suppliers (contracts, certifications, etc.)."""
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('certification', 'Certification'),
        ('insurance', 'Insurance'),
        ('tax', 'Tax Document'),
        ('other', 'Other'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='supplier_documents/')
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.name} - {self.supplier.supplier_name}"
