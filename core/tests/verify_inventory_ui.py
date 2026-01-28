import os
import django
from django.test import Client, TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from inventory.models import Warehouse, StockLevel
from products.models import Product
from products.utils import generate_barcode

class InventoryUIVerification(TestCase):
    def setUp(self):
        # Setup Tenant and User
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="public")
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", 
            password="password",
            tenant=self.tenant
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        # Setup Data
        self.warehouse = Warehouse.objects.create(
            warehouse_name="Main Warehouse",
            warehouse_code="WH-001",
            tenant=self.tenant
        )
        self.product = Product.objects.create(
            product_name="Test Widget",
            sku="WIDGET-001",
            base_price=Decimal("10.00"),
            tenant=self.tenant,
            owner=self.user
        )

    def test_dashboard_loads(self):
        """Verify dashboard loads correctly"""
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, 200)
        print("Inventory Dashboard: OK")

    def test_stock_list_loads(self):
        """Verify stock list loads"""
        response = self.client.get('/inventory/stock/')
        self.assertEqual(response.status_code, 200)
        print("Stock List: OK")

    def test_add_stock(self):
        """Verify adding stock works"""
        initial_count = StockLevel.objects.count()
        
        response = self.client.post('/inventory/stock/add/', {
            'product': self.product.id,
            'warehouse': self.warehouse.id,
            'quantity': 100,
            'reason': 'purchase' # Assuming form needs this or generic add
        })
        
        # Check for redirect (success)
        self.assertEqual(response.status_code, 302)
        
        # Check stock level created
        stock = StockLevel.objects.get(product=self.product, warehouse=self.warehouse)
        self.assertEqual(stock.quantity, 100)
        print("Add Stock Operation: OK")

    def test_barcode_generation(self):
        """Verify barcode util"""
        svg = generate_barcode("TEST-SKU-123")
        self.assertIsNotNone(svg)
        self.assertTrue("<svg" in svg)
        print("Barcode Generation: OK")

if __name__ == "__main__":
    # Test runner setup
    pass
