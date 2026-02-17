from django.db import models
from django.utils import timezone
from tenants.models import TenantAwareModel as TenantModel
from core.models import TimeStampedModel
from products.models import Product

class ProductionLine(TenantModel, TimeStampedModel):
    """
    Physical or logical production lines in a factory/warehouse.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class BillOfMaterials(TenantModel, TimeStampedModel):
    """
    Defines the recipe for a finished good.
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='bom')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"BOM for {self.product.product_name}"

class BOMItem(TenantModel):
    """
    Individual raw materials/components in a BOM.
    """
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in_boms')
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    scrap_factor = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage of expected waste")

    def __str__(self):
        return f"{self.quantity} x {self.component.product_name}"

class WorkOrder(TenantModel, TimeStampedModel):
    """
    Production instruction to manufacture a quantity of a product.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='work_orders')
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    production_line = models.ForeignKey(ProductionLine, on_delete=models.SET_NULL, null=True, blank=True)
    
    planned_start_date = models.DateTimeField(null=True, blank=True)
    planned_end_date = models.DateTimeField(null=True, blank=True)
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    
    # Cost Tracking (IPSAS 12 / IAS 2 WIP)
    accumulated_material_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accumulated_labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accumulated_overhead_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    @property
    def total_accumulated_cost(self):
        return self.accumulated_material_cost + self.accumulated_labor_cost + self.accumulated_overhead_cost

    def clean(self):
        from django.core.exceptions import ValidationError
        from quality_control.models import InspectionLog, InspectionRule

        # Quality Gate: Mandatory inspection for finished goods
        if self.status == 'completed':
            # Check if there are inspection rules for this product
            rules = InspectionRule.objects.filter(product=self.product, tenant=self.tenant)
            if rules.exists():
                # Check if an inspection log exists and passed for this work order
                logs = InspectionLog.objects.filter(
                    source_reference=self.order_number,
                    tenant=self.tenant
                )
                
                if not logs.exists():
                    raise ValidationError(f"Cannot complete Work Order: No quality inspection log found for {self.order_number}.")
                
                if not logs.filter(status='passed').exists():
                    raise ValidationError(f"Cannot complete Work Order: Quality inspection for {self.order_number} has not passed.")

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"WO-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
