import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.models import User

logger = logging.getLogger(__name__)

class InventoryNotificationService:
    """
    Service for sending inventory-related notifications.
    """
    
    @staticmethod
    def send_low_stock_alert(alert):
        """
        Send a low stock alert email to relevant users (warehouse managers or admins).
        """
        tenant = alert.tenant
        product = alert.product
        warehouse = alert.warehouse
        
        # Get users to notify: Warehouse manager or all tenant admins
        recipients = []
        if warehouse.manager and warehouse.manager.email:
            recipients.append(warehouse.manager.email)
        
        # Also include tenant admins if no manager or as fallback
        if not recipients:
            admins = User.objects.filter(tenant=tenant, is_staff=True)
            recipients = [u.email for u in admins if u.email]
            
        if not recipients:
            logger.warning(f"No recipients found for low stock alert: {alert}")
            return False
            
        subject = f"[Inventory Alert] Low Stock: {product.product_name}"
        
        context = {
            'alert': alert,
            'product': product,
            'warehouse': warehouse,
            'base_url': settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
        }
        
        # Try to render HTML template, fallback to plain text if not found
        try:
            html_message = render_to_string('inventory/emails/low_stock_alert.html', context)
            plain_message = strip_tags(html_message)
        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            plain_message = f"Low stock alert for {product.product_name} at {warehouse.warehouse_name}.\nCurrent Quantity: {alert.current_quantity}\nThreshold: {alert.threshold_quantity}"
            html_message = None
            
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                html_message=html_message,
                fail_silently=True
            )
            logger.info(f"Low stock email sent to {recipients} for {product.product_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send low stock email: {e}")
            return False
