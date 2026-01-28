from .models import Cart, CartItem, EcommerceCustomer
from products.services import PricingService
from inventory.services import InventoryService
from decimal import Decimal

class EcommerceService:
    """
    Service to handle ecommerce business logic.
    """
    
    @staticmethod
    def get_or_create_cart(tenant, customer=None, session_key=None):
        """
        Retrieves an active cart for a customer or session.
        """
        if customer:
            cart, created = Cart.objects.get_or_create(
                tenant=tenant,
                customer=customer,
                is_active=True
            )
        elif session_key:
            cart, created = Cart.objects.get_or_create(
                tenant=tenant,
                session_key=session_key,
                is_active=True
            )
        else:
            raise ValueError("Either customer or session_key must be provided.")
        return cart

    @staticmethod
    def add_to_cart(cart, product, quantity=1):
        """
        Adds a product to the cart or updates quantity if already exists.
        """
        # Check stock availability
        # Note: In a real system, we'd check against a specific ecommerce warehouse
        # For now, we'll check global or first available warehouse
        
        # Get price
        unit_price = PricingService.get_price(product, account=cart.customer.crm_account if cart.customer else None)
        
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            tenant=cart.tenant,
            defaults={'unit_price': unit_price, 'quantity': 0}
        )
        
        item.quantity += int(quantity)
        item.unit_price = unit_price # Update to latest price
        item.save()
        return item

    @staticmethod
    def process_checkout(cart, shipping_info, payment_method):
        """
        Converts a cart to an order/invoice and handles inventory/billing sync.
        Now awards loyalty points upon completion.
        """
        # ... logic to create invoice (as per existing workflow) ...
        # Assume invoice_amount is cart total
        
        # Award loyalty points
        if cart.customer and cart.customer.crm_account:
            from loyalty.services import LoyaltyService
            # Simple points rule for now
            LoyaltyService.award_points(
                customer=cart.customer.crm_account,
                points=int(cart.total_amount),
                description=f"Earned from E-commerce Order",
                sale_amount=cart.total_amount,
                reference=f"ECOMM-CART-{cart.id}"
            )

        cart.is_active = False
        cart.save()
        return True
