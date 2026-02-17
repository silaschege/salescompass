"""
Inventory Service - Business logic for stock management.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from core.event_bus import event_bus
from .models import (
    StockLevel, StockMovement, StockAdjustmentLine, ReorderRule, StockAlert,
    InterStoreTransfer, InterStoreTransferLine, SerialNumber, WarehouseZone
)



class InventoryService:
    """
    Service class for inventory operations.
    """
    
    @staticmethod
    def get_stock_level(product, warehouse, location=None, batch_number=None, tenant=None):
        """
        Get current stock level for a product at a warehouse/location/batch.
        """
        filters = {
            'product': product,
            'warehouse': warehouse,
        }
        if location:
            filters['location'] = location
        if batch_number is not None:
            filters['batch_number'] = batch_number
        if tenant:
            filters['tenant'] = tenant
        
        try:
            # If batch_number is NOT provided, this might return multiple.
            # Usually called with context where batch is known, or total is needed.
            if batch_number is not None:
                return StockLevel.objects.get(**filters)
            else:
                # Fallback to first if multiple exist (not ideal if specifically needed)
                return StockLevel.objects.filter(**filters).first()
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
                  unit_cost=None, batch_number='', expiry_date=None,
                  serial_numbers=None, reference_type='', reference_id=None, 
                  notes='', tenant=None):
        """
        Add stock to a warehouse location with batch and serial tracking.
        """
        # Validate serial numbers if required
        if product.has_serial_numbers:
            if not serial_numbers:
                raise ValueError(f"Serial numbers required for {product.product_name}")
            if len(serial_numbers) != int(quantity):
                raise ValueError(f"Number of serial numbers ({len(serial_numbers)}) must match quantity ({quantity})")
            
            # Check for existing serial numbers
            existing = SerialNumber.objects.filter(product=product, serial_number__in=serial_numbers)
            if existing.exists():
                dupes = ", ".join([s.serial_number for s in existing])
                raise ValueError(f"Serial numbers already exist in system: {dupes}")

        # Get or create stock level for the specific batch
        stock, created = StockLevel.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            location=location,
            batch_number=batch_number or '',
            tenant=tenant or product.tenant,
            defaults={
                'quantity': Decimal('0'), 
                'cost_price': unit_cost,
                'expiry_date': expiry_date
            }
        )
        
        # If batch exists, update expiry if provided
        if not created and expiry_date:
            stock.expiry_date = expiry_date
        
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

        # Create serial numbers if provided
        if product.has_serial_numbers and serial_numbers:
            for sn in serial_numbers:
                SerialNumber.objects.create(
                    product=product,
                    serial_number=sn,
                    warehouse=warehouse,
                    location=location,
                    batch_number=batch_number or '',
                    expiry_date=expiry_date,
                    tenant=tenant or product.tenant
                )
        
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
    def remove_stock(product, warehouse, quantity, user=None, location=None,
                     batch_number=None, serial_numbers=None, reference_type='', 
                     reference_id=None, notes='', movement_type='out', tenant=None):
        """
        Remove stock from a warehouse location.
        Supports FIFO/FEFO and Serial Number tracking.
        """
        qty_to_remove = Decimal(str(quantity))
        tenant = tenant or product.tenant

        # Validate serial numbers if required
        if product.has_serial_numbers:
            if not serial_numbers:
                raise ValueError(f"Serial numbers required for {product.product_name}")
            if len(serial_numbers) != int(quantity):
                raise ValueError(f"Number of serial numbers must match quantity")
            
            # Check if serial numbers exist and are in stock at this warehouse
            sns = SerialNumber.objects.filter(
                product=product, 
                serial_number__in=serial_numbers,
                warehouse=warehouse,
                current_status='in_stock',
                tenant=tenant
            )
            if sns.count() != len(serial_numbers):
                found_sns = sns.values_list('serial_number', flat=True)
                missing = set(serial_numbers) - set(found_sns)
                raise ValueError(f"Serial numbers not found or not in stock: {', '.join(missing)}")
            
            # Update SN status
            sns.update(current_status='sold' if movement_type == 'out' else 'dispatched')

        if batch_number:
            stocks = StockLevel.objects.filter(
                product=product, warehouse=warehouse, location=location,
                batch_number=batch_number, tenant=tenant
            )
        else:
            # FIFO: Deduct from oldest acquisition first
            # FEFO: Use ordering = ['expiry_date', 'acquisition_date'] if preferred
            stocks = StockLevel.objects.filter(
                product=product, warehouse=warehouse, location=location,
                tenant=tenant, quantity__gt=0
            ).order_by('expiry_date', 'acquisition_date') # FEFO/FIFO Hybrid

        total_available = sum(s.available_quantity for s in stocks)
        
        if total_available < qty_to_remove:
            raise ValueError(
                f"Insufficient stock. Available: {total_available}, Requested: {quantity}"
            )
        
        # Deduct across batches
        for stock in stocks:
            if qty_to_remove <= 0:
                break
                
            deduct_qty = min(stock.available_quantity, qty_to_remove)
            stock.quantity -= deduct_qty
            stock.save()
            qty_to_remove -= deduct_qty
            
            # Record movement per batch? Usually we record one total movement, 
            # but for traceabilty we should probably record which batches were affected.
            # For now, we'll keep the movement recording outside or update it.
        
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
    def reduce_stock(product, quantity, reference='', tenant=None, user=None):
        """
        Helper method to reduce stock from the default warehouse.
        Used primarily by ecommerce checkout.
        """
        from .models import Warehouse
        tenant = tenant or product.tenant
        
        # Find default warehouse for the tenant
        warehouse = Warehouse.objects.filter(tenant=tenant, is_default=True).first()
        
        if not warehouse:
            # Fallback to any active warehouse
            warehouse = Warehouse.objects.filter(tenant=tenant, is_active=True).first()
            
        if not warehouse:
            # If still no warehouse, we can't reduce stock
            # In a real system we might log this or raise an alert
            return None
            
        return InventoryService.remove_stock(
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            user=user,
            reference_type='ecommerce_order',
            notes=f"Ecommerce Order: {reference}",
            movement_type='sale',
            tenant=tenant
        )

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
                    alert = StockAlert.objects.create(
                        product=product,
                        warehouse=warehouse,
                        alert_type=alert_type,
                        current_quantity=current_qty,
                        threshold_quantity=rule.min_quantity,
                        message=f"Stock is {'out' if current_qty <= 0 else 'low'}. Current: {current_qty}, Min: {rule.min_quantity}",
                        tenant=tenant or product.tenant
                    )
                    
                    # Trigger notification
                    try:
                        from .notifications import InventoryNotificationService
                        InventoryNotificationService.send_low_stock_alert(alert)
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).error(f"Failed to send low stock notification: {e}")
                    
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
    def ship_transfer(transfer, user, shipment_data=None):
        """
        Mark transfer as shipped and deduct stock from source.
        shipment_data: dict {line_id: {'serial_numbers': list, 'from_location': loc_id}}
        """
        if transfer.status not in ['draft', 'pending']:
            raise ValueError("Transfer must be in draft or pending status to ship.")
            
        import re
        
        # Deduct stock for all lines
        for line in transfer.lines.all():
            data = (shipment_data or {}).get(str(line.id), {})
            
            # Update line with shipment details if provided
            if 'from_location' in data:
                line.from_location_id = data['from_location']
            if 'serial_numbers' in data:
                # If it's a list, join it; if it's already a string, keep it
                sns = data['serial_numbers']
                if isinstance(sns, list):
                    line.serial_numbers = ",".join(sns)
                else:
                    line.serial_numbers = sns
            line.save()

            # Parse serial numbers for InventoryService
            sn_list = []
            if line.serial_numbers:
                sn_list = [sn.strip() for sn in re.split(r'[, \n\r]+', line.serial_numbers) if sn.strip()]

            InventoryService.remove_stock(
                product=line.product,
                warehouse=transfer.source_warehouse,
                quantity=line.quantity_requested,
                user=user,
                location=line.from_location,
                serial_numbers=sn_list if line.product.has_serial_numbers else None,
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
    def receive_transfer(transfer, receipt_data, user):
        """
        Receive transfer and add stock to destination.
        receipt_data: dict {line_id: {'quantity': Decimal, 'serial_numbers': list, 'to_location': loc_id}}
        """
        if transfer.status != 'in_transit':
            raise ValueError("Transfer must be in transit to receive.")
            
        import re
        all_received = True
        
        for line in transfer.lines.all():
            data = receipt_data.get(str(line.id), {})
            
            # Handle both old style (direct quantity) and new style (dict)
            if isinstance(data, (int, float, str, Decimal)):
                qty_received = Decimal(str(data))
                sns_raw = ""
                to_loc_id = None
            else:
                qty_received = Decimal(str(data.get('quantity', 0)))
                sns_raw = data.get('serial_numbers', "")
                to_loc_id = data.get('to_location')

            line.quantity_received = qty_received
            if to_loc_id:
                line.to_location_id = to_loc_id
            
            if qty_received > 0:
                # Parse serial numbers
                sn_list = []
                if sns_raw:
                    if isinstance(sns_raw, list):
                        sn_list = sns_raw
                    else:
                        sn_list = [sn.strip() for sn in re.split(r'[, \n\r]+', sns_raw) if sn.strip()]
                
                # If no specific SNs provided but product needs them, maybe they are same as shipped?
                # Usually we want explicit confirmation.
                
                InventoryService.add_stock(
                    product=line.product,
                    warehouse=transfer.destination_warehouse,
                    quantity=qty_received,
                    user=user,
                    location=line.to_location,
                    serial_numbers=sn_list if line.product.has_serial_numbers else None,
                    reference_type='transfer_in',
                    reference_id=transfer.id,
                    notes=f"Transfer {transfer.transfer_number} from {transfer.source_warehouse.warehouse_code}",
                    tenant=transfer.tenant
                )
            
            line.save()
            
            if qty_received < line.quantity_shipped:
                all_received = False
                
        transfer.status = 'received' if all_received else 'partial'
        transfer.received_at = timezone.now()
        transfer.save()
        return transfer
