from .models import Shipment, DeliveryRoute
from django.utils import timezone

class RouteOptimizerService:
    """
    Service to handle logistics route management and optimization.
    """
    
    @staticmethod
    def optimize_pending_shipments(tenant, vehicle_limit=10):
        """
        Groups pending shipments into logical routes.
        For now, uses a basic heuristic (sequential batching).
        """
        pending = Shipment.objects.filter(
            tenant=tenant, 
            status='pending', 
            route__isnull=True
        ).order_by('created_at')
        
        if not pending.exists():
            return []
            
        new_routes = []
        shipments_per_route = 5
        
        for i in range(0, pending.count(), shipments_per_route):
            batch = pending[i:i+shipments_per_route]
            
            route = DeliveryRoute.objects.create(
                tenant=tenant,
                route_name=f"R-AUTO-{timezone.now().strftime('%m%d%H%M')}-{len(new_routes)+1}",
                status='planned'
            )
            
            for idx, shipment in enumerate(batch):
                shipment.route = route
                shipment.stop_number = idx + 1
                shipment.save()
                
            new_routes.append(route)
            
        return new_routes
