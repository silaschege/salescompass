"""
Inventory Service - Business logic for stock management.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from core.event_bus import event_bus
from .models import (
    StockLevel, StockMovement, StockAdjustmentLine, ReorderRule, StockAlert,
    InterStoreTransfer, InterStoreTransferLine
)



class InventoryService:
    """
    Service class for inventory operations.
    """
    
    @staticmethod
    def get_stock_level(product, warehouse, location=None, tenant=None):
        """
        Get current stock level for a product at a warehouse/location.
        """
        filters = {
            'product': product,
            'warehouse': warehouse,
        }
        if location:
            filters['location'] = location
        if tenant:
            filters['tenant'] = tenant
        
        try:
            return StockLevel.objects.get(**filters)
        except StockLevel.DoesNotExist:
            return None

    @staticmethod
    def get_total_stock(product, tenant=None):
        """
        Get total stock across all warehouses for a product.
        """
        filters = {'product': product}
        if tenant:
            filters['tenant'] = tenant
        
        from django.db.models import Sum
        result = StockLevel.objects.filter(**filters).aggregate(
            total=Sum('quantity'),
            reserved=Sum('reserved_quantity')
        )
        return {
            'total': result['total'] or Decimal('0'),
            'reserved': result['reserved'] or Decimal('0'),
            'available': (result['total'] or Decimal('0')) - (result['reserved'] or Decimal('0'))
        }

    @staticmethod
    @transaction.atomic
    def add_stock(product, warehouse, quantity, user, location=None, 
                  unit_cost=None, reference_type='', reference_id=None, 
                  notes='', tenant=None):
        """
        Add stock to a warehouse location.
        """
        # Get or create stock level
        stock, created = StockLevel.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            location=location,
            tenant=tenant or product.tenant,
            defaults={'quantity': Decimal('0'), 'cost_price': unit_cost}
        )
        
        # Update quantity
        stock.quantity += Decimal(str(quantity))
        if unit_cost:
            # Calculate weighted average cost
            if stock.cost_price and stock.quantity > Decimal('0'):
                old_value = stock.cost_price * (stock.quantity - Decimal(str(quantity)))
                new_value = Decimal(str(unit_cost)) * Decimal(str(quantity))
                stock.cost_price = (old_value + new_value) / stock.quantity
            else:
                stock.cost_price = Decimal(str(unit_cost))
        stock.save()
        
        # Record movement
        StockMovement.objects.create(
            product=product,
            movement_type='in',
            quantity=Decimal(str(quantity)),
            to_warehouse=warehouse,
            to_location=location,
            unit_cost=unit_cost,
            total_cost=Decimal(str(quantity)) * Decimal(str(unit_cost)) if unit_cost else None,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            performed_by=user,
            tenant=tenant or product.tenant
        )
        
        # Check if we need to clear any alerts
        InventoryService._check_resolve_alerts(product, warehouse, stock.quantity, tenant)
        
        event_bus.emit('inventory.stock.added', {
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'quantity': float(quantity),
            'location_id': location.id if location else None,
            'tenant_id': (tenant or product.tenant).id,
            'user': user,
            'reference_type': reference_type,
            'reference_id': reference_id
        })
        
        return stock

    @staticmethod
    @transaction.atomic
    def remove_stock(product, warehouse, quantity, user, location=None,
                     reference_type='', reference_id=None, notes='', 
                     movement_type='out', tenant=None):
        """
        Remove stock from a warehouse location.
        """
        stock = InventoryService.get_stock_level(product, warehouse, location, tenant)
        
        if not stock:
            raise ValueError(f"No stock found for {product.product_name} at {warehouse.warehouse_code}")
        
        if stock.available_quantity < Decimal(str(quantity)):
            raise ValueError(
                f"Insufficient stock. Available: {stock.available_quantity}, Requested: {quantity}"
            )
        
        stock.quantity -= Decimal(str(quantity))
        stock.save()
        
        # Record movement
        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=Decimal(str(quantity)),
            from_warehouse=warehouse,
            from_location=location,
            unit_cost=stock.cost_price,
            total_cost=Decimal(str(quantity)) * stock.cost_price if stock.cost_price else None,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            performed_by=user,
            tenant=tenant or product.tenant
        )
        
        # Check reorder rules
        InventoryService._check_reorder_rules(product, warehouse, tenant)
        
        event_bus.emit('inventory.stock.removed', {
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'quantity': float(quantity),
            'location_id': location.id if location else None,
            'tenant_id': (tenant or product.tenant).id,
            'user': user,
            'reference_type': reference_type,
            'reference_id': reference_id,
            'movement_type': movement_type
        })
        
        return stock

    @staticmethod
    @transaction.atomic
    def transfer_stock(product, from_warehouse, to_warehouse, quantity, user,
                       from_location=None, to_location=None, notes='', tenant=None):
        """
        Transfer stock between warehouses or locations.
        """
        tenant = tenant or product.tenant
        
        # Remove from source
        source_stock = InventoryService.remove_stock(
            product=product,
            warehouse=from_warehouse,
            quantity=quantity,
            user=user,
            location=from_location,
            reference_type='transfer',
            movement_type='transfer',
            notes=notes,
            tenant=tenant
        )
        
        # Add to destination
        dest_stock = InventoryService.add_stock(
            product=product,
            warehouse=to_warehouse,
            quantity=quantity,
            user=user,
            location=to_location,
            unit_cost=source_stock.cost_price,
            reference_type='transfer',
            notes=notes,
            tenant=tenant
        )
        
        return {'from_stock': source_stock, 'to_stock': dest_stock}

    @staticmethod
    @transaction.atomic
    def reserve_stock(product, warehouse, quantity, tenant=None):
        """
        Reserve stock for a pending order.
        """
        stock = InventoryService.get_stock_level(product, warehouse, tenant=tenant)
        
        if not stock:
            raise ValueError(f"No stock found for {product.product_name} at {warehouse.warehouse_code}")
        
        if stock.available_quantity < Decimal(str(quantity)):
            raise ValueError(
                f"Insufficient stock to reserve. Available: {stock.available_quantity}, Requested: {quantity}"
            )
        
        stock.reserved_quantity += Decimal(str(quantity))
        stock.save()
        
        return stock

    @staticmethod
    @transaction.atomic
    def release_reservation(product, warehouse, quantity, tenant=None):
        """
        Release reserved stock.
        """
        stock = InventoryService.get_stock_level(product, warehouse, tenant=tenant)
        
        if stock and stock.reserved_quantity >= Decimal(str(quantity)):
            stock.reserved_quantity -= Decimal(str(quantity))
            stock.save()
        
        return stock

    @staticmethod
    def _check_reorder_rules(product, warehouse, tenant=None):
        """
        Check if reorder alert should be triggered.
        """
        filters = {'product': product, 'warehouse': warehouse, 'is_active': True}
        if tenant:
            filters['tenant'] = tenant
        
        rules = ReorderRule.objects.filter(**filters)
        
        for rule in rules:
            if rule.check_trigger():
                stock = InventoryService.get_stock_level(product, warehouse, tenant=tenant)
                current_qty = stock.available_quantity if stock else Decimal('0')
                
                # Check if alert already exists
                existing_alert = StockAlert.objects.filter(
                    product=product,
                    warehouse=warehouse,
                    alert_type='low_stock',
                    status__in=['new', 'acknowledged'],
                    tenant=tenant or product.tenant
                ).first()
                
                if not existing_alert:
                    alert_type = 'out_of_stock' if current_qty <= 0 else 'low_stock'
                    StockAlert.objects.create(
                        product=product,
                        warehouse=warehouse,
                        alert_type=alert_type,
                        current_quantity=current_qty,
                        threshold_quantity=rule.min_quantity,
                        message=f"Stock is {'out' if current_qty <= 0 else 'low'}. Current: {current_qty}, Min: {rule.min_quantity}",
                        tenant=tenant or product.tenant
                    )
                    
                    rule.last_triggered = timezone.now()
                    rule.save()

    @staticmethod
    def _check_resolve_alerts(product, warehouse, current_quantity, tenant=None):
        """
        Check if any alerts should be resolved after stock addition.
        """
        filters = {
            'product': product,
            'warehouse': warehouse,
            'status__in': ['new', 'acknowledged']
        }
        if tenant:
            filters['tenant'] = tenant
        
        alerts = StockAlert.objects.filter(**filters)
        
        for alert in alerts:
            if current_quantity > alert.threshold_quantity:
                alert.status = 'resolved'
                alert.save()

    @staticmethod
    def get_low_stock_products(warehouse=None, tenant=None):
        """
        Get all products with active low stock alerts.
        """
        filters = {
            'alert_type__in': ['low_stock', 'out_of_stock'],
            'status__in': ['new', 'acknowledged']
        }
        if warehouse:
            filters['warehouse'] = warehouse
        if tenant:
            filters['tenant'] = tenant
        
        return StockAlert.objects.filter(**filters).select_related('product', 'warehouse')


class TransferService:
    """
    Service for managing inter-store stock transfers.
    """
    
    @staticmethod
    @transaction.atomic
    def create_transfer(source, destination, lines, user, notes='', tenant=None):
        """
        Create a new draft transfer.
        lines: list of dicts {'product': Product, 'quantity': Decimal}
        """
        if source == destination:
            raise ValueError("Source and destination warehouses must be different.")
            
        transfer = InterStoreTransfer.objects.create(
            transfer_number=f"TRF-{timezone.now().strftime('%Y%m')}-{InterStoreTransfer.objects.count()+1:04d}",
            source_warehouse=source,
            destination_warehouse=destination,
            requested_by=user,
            notes=notes,
            tenant=tenant or user.tenant
        )
        
        for line in lines:
            InterStoreTransferLine.objects.create(
                transfer=transfer,
                product=line['product'],
                quantity_requested=Decimal(str(line['quantity'])),
                tenant=tenant or user.tenant
            )
            
        return transfer

    @staticmethod
    @transaction.atomic
    def ship_transfer(transfer, user):
        """
        Mark transfer as shipped and deduct stock from source.
        """
        if transfer.status not in ['draft', 'pending']:
            raise ValueError("Transfer must be in draft or pending status to ship.")
            
        # Deduct stock for all lines
        for line in transfer.lines.all():
            InventoryService.remove_stock(
                product=line.product,
                warehouse=transfer.source_warehouse,
                quantity=line.quantity_requested,
                user=user,
                reference_type='transfer_out',
                reference_id=transfer.id,
                notes=f"Transfer {transfer.transfer_number} to {transfer.destination_warehouse.warehouse_code}",
                movement_type='transfer',
                tenant=transfer.tenant
            )
            line.quantity_shipped = line.quantity_requested
            line.save()
            
        transfer.status = 'in_transit'
        transfer.shipped_at = timezone.now()
        transfer.save()
        return transfer

    @staticmethod
    @transaction.atomic
    def receive_transfer(transfer, received_lines, user):
        """
        Receive transfer and add stock to destination.
        received_lines: dict {line_id: quantity_received}
        """
        if transfer.status != 'in_transit':
            raise ValueError("Transfer must be in transit to receive.")
            
        all_received = True
        
        for line in transfer.lines.all():
            qty_received = Decimal(str(received_lines.get(str(line.id), 0)))
            line.quantity_received = qty_received
            line.save()
            
            if qty_received > 0:
                InventoryService.add_stock(
                    product=line.product,
                    warehouse=transfer.destination_warehouse,
                    quantity=qty_received,
                    user=user,
                    reference_type='transfer_in',
                    reference_id=transfer.id,
                    notes=f"Transfer {transfer.transfer_number} from {transfer.source_warehouse.warehouse_code}",
                    tenant=transfer.tenant
                )
            
            if qty_received < line.quantity_shipped:
                all_received = False
                
        transfer.status = 'received' if all_received else 'partial'
        transfer.received_at = timezone.now()
        transfer.save()
        return transfer
