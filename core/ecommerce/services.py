from .models import Cart, CartItem, EcommerceCustomer, Order, OrderItem
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
    def remove_from_cart(cart, item_id):
        """
        Removes a specific item from the cart.
        """
        try:
            item = cart.items.get(id=item_id)
            item.delete()
            return True, "Item removed from cart"
        except CartItem.DoesNotExist:
            return False, "Item not found in cart"

    @staticmethod
    def clear_cart(cart):
        """
        Removes all items from the cart.
        """
        cart.items.all().delete()
        return True, "Cart cleared"

    @staticmethod
    def process_checkout(cart, shipping_info, payment_method, user=None):
        """
        Converts a cart to an order/invoice and handles inventory/billing sync.
        Now awards loyalty points upon completion.
        """
        if not cart.items.exists():
            return None, "Cart is empty"
        
        tenant = cart.tenant

        # Create Order
        order = Order.objects.create(
            tenant=tenant,
            customer=cart.customer,
            total_amount=cart.total_amount,
            payment_method=payment_method,
            shipping_address=shipping_info.get('address', ''),
            shipping_city=shipping_info.get('city', ''),
            shipping_country=shipping_info.get('country', ''),
            shipping_zip=shipping_info.get('zip', ''),
            notes=shipping_info.get('notes', '')
        )

        # Create OrderItems
        for item in cart.items.all():
            OrderItem.objects.create(
                tenant=tenant,
                order=order,
                product=item.product,
                product_name=item.product.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity
            )
            
            # Reduce inventory
            InventoryService.reduce_stock(
                product=item.product,
                quantity=item.quantity,
                reference=f"{order.order_number}",
                tenant=tenant,
                user=user
            )

        # Award loyalty points
        if cart.customer and cart.customer.crm_account:
            from loyalty.services import LoyaltyService
            LoyaltyService.award_points(
                customer=cart.customer.crm_account,
                points=int(order.total_amount),
                description=f"Earned from E-commerce Order {order.order_number}",
                sale_amount=order.total_amount,
                reference=f"ECOMM-ORDER-{order.id}"
            )

        # Deactivate cart
        cart.is_active = False
        cart.save()

        return order, None
