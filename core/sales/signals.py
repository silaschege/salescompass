from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sale
from loyalty.services import LoyaltyService

@receiver(post_save, sender=Sale)
def handle_sale_accounting_and_loyalty(sender, instance, created, **kwargs):
    """
    Automates IFRS 15 revenue deferral and loyalty point awarding.
    """
    if created:
        # 1. Loyalty Points
        LoyaltyService.award_points(
            customer=instance.account,
            points=int(instance.amount),
            description=f"Points earned for Sale #{instance.id}",
            sale_amount=instance.amount,
            reference=f"SALE-{instance.id}"
        )
        
        # 2. IFRS 15 Revenue Deferral
        from .services_revenue import RevenueRecognitionService
        try:
            RevenueRecognitionService.defer_on_sale(instance)
        except Exception as e:
            # In production, log this error
            pass
