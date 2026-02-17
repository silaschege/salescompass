from django.test import TestCase
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from products.models import Product, ProductCategory
from inventory.models import Warehouse, StockLevel
from ecommerce.models import EcommerceCustomer, Cart, CartItem
from ecommerce.services import EcommerceService
from decimal import Decimal

class EcommerceCheckoutTest(TestCase):
    def setUp(self):
        # Setup tenant
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_ecommerce")
        
        # Setup user
        self.user = User.objects.create_user(
            username="testcustomer",
            email="customer@example.com",
            password="password",
            tenant=self.tenant
        )
        
        # Setup customer profile
        self.customer = EcommerceCustomer.objects.create(
            user=self.user,
            tenant=self.tenant
        )
        
        # Setup category and product
        self.category = ProductCategory.objects.create(name="Electronics", tenant=self.tenant)
        self.product = Product.objects.create(
            product_name="Gadget",
            category=self.category,
            base_price=Decimal("100.00"),
            tenant=self.tenant
        )
        
        # Setup warehouse and stock
        self.warehouse = Warehouse.objects.create(
            warehouse_name="Main Warehouse",
            warehouse_code="WH001",
            is_default=True,
            tenant=self.tenant
        )
        self.stock = StockLevel.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("10.00"),
            tenant=self.tenant
        )
        
        # Setup cart
        self.cart = Cart.objects.create(
            customer=self.customer,
            tenant=self.tenant
        )
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            unit_price=Decimal("100.00"),
            tenant=self.tenant
        )

    def test_checkout_reduces_stock(self):
        shipping_info = {
            'address': '123 Street',
            'city': 'Nairobi',
            'country': 'Kenya',
            'zip': '00100'
        }
        payment_method = 'mpesa'
        
        # Process checkout
        order, error = EcommerceService.process_checkout(
            self.cart, 
            shipping_info, 
            payment_method, 
            user=self.user
        )
        
        self.assertIsNone(error)
        self.assertIsNotNone(order)
        
        # Refresh stock and verify reduction
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("8.00"))
        
        # Verify order exists
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)
