from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from products.models import Product, ProductCategory
from billing.models import TaxRate, TaxRule
from billing.services import TaxService
from pos.models import POSTerminal, POSSession, POSTransaction
from pos.services import POSService

class TaxVerification(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", 
            password="password",
            tenant=self.tenant
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        # Setup Default Tax (16%)
        self.vat = TaxRate.objects.create(
            name="VAT", rate=Decimal('16.00'), is_default=True, tenant=self.tenant
        )
        
        # Setup Zero Rated (0%)
        self.zero = TaxRate.objects.create(
            name="Zero", rate=Decimal('0.00'), is_default=False, tenant=self.tenant
        )
        
        # Product with Default Tax
        self.p_standard = Product.objects.create(
            product_name="Standard", sku="STD", base_price=100, tenant=self.tenant, owner=self.user
        )
        
        # Product with Override
        self.p_zero = Product.objects.create(
            product_name="Zero Rated", sku="ZERO", base_price=100, tax_rate=self.zero, tenant=self.tenant, owner=self.user
        )

    def test_tax_calculation(self):
        """Test TaxService calculation logic."""
        # Standard Product (16%)
        tax_amt, rate = TaxService.calculate_tax(Decimal('100'), self.p_standard, self.tenant)
        self.assertEqual(rate, self.vat)
        self.assertEqual(tax_amt, Decimal('16.00')) # 100 * 0.16
        
        # Zero Rated Product (0%)
        tax_amt, rate = TaxService.calculate_tax(Decimal('100'), self.p_zero, self.tenant)
        self.assertEqual(rate, self.zero)
        self.assertEqual(tax_amt, Decimal('0.00'))
        
        print("TaxService Calculation: OK")

    def test_pos_transaction_tax(self):
        """Test POS integration of taxes."""
        # Setup POS
        terminal = POSTerminal.objects.create(
            terminal_name="T1", terminal_code="T1", tenant=self.tenant
        )
        session = POSService.open_session(terminal, self.user)
        txn = POSService.create_transaction(session, self.user)
        
        # Add Standard Item
        POSService.add_line_item(txn, self.p_standard, quantity=1, unit_price=100)
        
        # Add Zero Rated Item
        POSService.add_line_item(txn, self.p_zero, quantity=1, unit_price=100)
        
        # Check Totals
        # Line 1: 100 + 16 (if exclusive) or 100 incl 13.79 (if inclusive)
        # Wait, POSService currently hardcodes is_tax_inclusive=True in add_line_item
        # So:
        # Line 1 (Standard): 100 inclusive. Tax = 100 - (100/1.16) = 13.79
        # Line 2 (Zero): 100 inclusive. Tax = 0.
        # Check specific tax value logic in model
        
        txn.refresh_from_db()
        lines = txn.lines.all()
        l1 = lines.filter(product=self.p_standard).first()
        l2 = lines.filter(product=self.p_zero).first()
        
        self.assertAlmostEqual(l1.tax_amount, Decimal('13.79'), places=2)
        self.assertEqual(l2.tax_amount, Decimal('0.00'))
        
        self.assertAlmostEqual(txn.tax_amount, Decimal('13.79'), places=2)
        self.assertEqual(txn.total_amount, Decimal('200.00')) # 100 + 100 inclusive
        
        print("POS Transaction Tax: OK")
