from django.db import models
from django.utils import timezone
from tenants.models import TenantAwareModel as TenantModel
from core.models import TimeStampedModel
from inventory.models import StockMovement

class Carrier(TenantModel, TimeStampedModel):
    """
    Shipping carriers (DHL, FedEx, UPS, Local Fleet).
    """
    name = models.CharField(max_length=100)
    api_endpoint = models.URLField(blank=True, null=True)
    api_key = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class DeliveryRoute(TenantModel, TimeStampedModel):
    """
    Route optimization for local fleet deliveries.
    Groups multiple shipments into a logical sequence.
    """
    route_name = models.CharField(max_length=255)
    driver_name = models.CharField(max_length=255, blank=True)
    vehicle_id = models.CharField(max_length=100, blank=True)
    
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], default='planned')
    
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.route_name

class Shipment(TenantModel, TimeStampedModel):
    """
    Outbound or Inbound shipment record.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('dispatched', 'Dispatched'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    shipment_number = models.CharField(max_length=50, unique=True)
    carrier = models.ForeignKey(Carrier, on_delete=models.SET_NULL, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Route Optimization
    route = models.ForeignKey(DeliveryRoute, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')
    stop_number = models.IntegerField(default=0, help_text="Order in the delivery route")
    
    # Origins & Destinations
    origin_warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, related_name='outbound_shipments')
    destination_address = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    # Link to Inventory
    stock_movement = models.OneToOneField(StockMovement, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipment')

    def __str__(self):
        return self.shipment_number

    def save(self, *args, **kwargs):
        if not self.shipment_number:
            import uuid
            self.shipment_number = f"SHP-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

class TrackingUpdate(TenantModel, TimeStampedModel):
    """
    Individual tracking snapshots from carrier APIs or internal logs.
    """
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='updates')
    status_description = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.shipment.shipment_number} - {self.status_description}"
