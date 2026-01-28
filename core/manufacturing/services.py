from .models import WorkOrder, ProductionLine
from django.db.models import Count, Q

class ManufacturingService:
    """
    Service to manage production floor operations.
    """
    
    @staticmethod
    def get_floor_status(tenant):
        """
        Returns summary of activity across all production lines.
        """
        lines = ProductionLine.objects.filter(tenant=tenant, is_active=True)
        status = []
        
        for line in lines:
            active_orders = WorkOrder.objects.filter(
                production_line=line,
                status__in=['confirmed', 'in_progress']
            )
            
            status.append({
                'line': line,
                'order_count': active_orders.count(),
                'active_orders': active_orders,
                'is_busy': active_orders.count() > 0
            })
            
        return status

    @staticmethod
    def start_work_order(work_order_id):
        """Marks a work order as in progress."""
        from django.utils import timezone
        order = WorkOrder.objects.get(id=work_order_id)
        order.status = 'in_progress'
        order.actual_start_date = timezone.now()
        order.save()
        return order

    @staticmethod
    def complete_work_order(work_order_id):
        """
        Marks work order as completed.
        In a real system, this would deduct materials from inventory.
        """
        from django.utils import timezone
        order = WorkOrder.objects.get(id=work_order_id)
        order.status = 'completed'
        order.actual_end_date = timezone.now()
        order.save()
        
        # Integration: Deduction logic (Placeholder)
        return order
