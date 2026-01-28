from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import StockLevel, StockMovement

class ValuationService:
    """
    Handles IAS 2 Inventory Valuation methods.
    """

    @staticmethod
    def get_unit_cost(product, warehouse, method='avco'):
        """
        Calculates unit cost based on the specified method.
        """
        if method == 'avco':
            return ValuationService._get_avco_cost(product, warehouse)
        elif method == 'fifo':
            return ValuationService._get_fifo_cost(product, warehouse)
        return product.base_price * Decimal('0.7') # Fallback to 70% of retail

    @staticmethod
    def _get_avco_cost(product, warehouse):
        """
        Average Cost (AVCO) / Moving Weighted Average.
        """
        levels = StockLevel.objects.filter(product=product, warehouse=warehouse)
        total_qty = sum(l.quantity for l in levels)
        if total_qty <= 0:
            return Decimal('0')
            
        total_value = sum(l.quantity * (l.cost_price or 0) for l in levels)
        return total_value / total_qty

    @staticmethod
    def _get_fifo_cost(product, warehouse):
        """
        First-In, First-Out (FIFO).
        Returns the cost of the OLDEST available batch.
        """
        oldest_batch = StockLevel.objects.filter(
            product=product, 
            warehouse=warehouse, 
            quantity__gt=0
        ).order_by('acquisition_date').first()
        
        return oldest_batch.cost_price if oldest_batch else Decimal('0')

    @staticmethod
    @transaction.atomic
    def record_acquisition(product, warehouse, quantity, unit_cost, batch_number=None):
        """
        Records new stock and updates valuation.
        """
        today = timezone.now().date()
        batch_number = batch_number or f"BATCH-{product.sku}-{today.strftime('%Y%m%d')}"
        
        # Create a specific StockLevel entry for this batch (supporting FIFO)
        stock = StockLevel.objects.create(
            tenant=product.tenant,
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            cost_price=unit_cost,
            batch_number=batch_number,
            acquisition_date=today,
            last_valuation_date=today
        )
        
        return stock

    @staticmethod
    def test_nrv(product):
        """
        IAS 2: Inventory should be measured at the lower of cost and net realizable value (NRV).
        """
        if not product.nrv:
            return True # Assume compliant if NRV not set
            
        stocks = StockLevel.objects.filter(product=product)
        for stock in stocks:
            if stock.cost_price > product.nrv:
                return False # Found impairment
        return True
