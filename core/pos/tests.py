from django.test import TestCase
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from pos.models import POSSession, POSTerminal, POSTransaction, POSTransactionLine
from pos.services import POSService
from products.models import Product
from accounts.models import Account
from loyalty.models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction
from decimal import Decimal

class POSLoyaltyTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.user = User.objects.create_user(username="cashier", email="cashier@test.com", password="password")
        self.tenant.users.add(self.user)
        
        # Setup Terminal
        self.terminal = POSTerminal.objects.create(
            tenant=self.tenant,
            terminal_name="Till 1",
            device_id="DEV001"
        )
        
        # Setup Product
        self.product = Product.objects.create(
            tenant=self.tenant,
            product_name="Test Product",
            sku="TP001",
            base_price=Decimal("100.00")
        )
        
        # Setup Customer & Loyalty
        self.customer = Account.objects.create(
            tenant=self.tenant,
            name="Loyal Customer",
            email="loyal@test.com"
        )
        
        self.program = LoyaltyProgram.objects.create(
            tenant=self.tenant,
            program_name="Default Rewards",
            points_per_currency=1.0, # Earn 1 pt per $1
            redemption_conversion_rate=0.01 # 1 pt = $0.01, so 100 pts = $1.00
        )
        
        self.loyalty_profile = CustomerLoyalty.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            program=self.program,
            points_balance=5000 # $50.00 worth
        )
        
        # Open Session
        self.session = POSService.open_session(self.terminal, self.user)

    def test_loyalty_redemption(self):
        """Test paying with loyalty points."""
        
        # Create Transaction
        txn = POSService.create_transaction(self.session, self.user, customer=self.customer)
        POSService.add_line_item(txn, self.product, quantity=1) # Total $100.00
        
        # Redeem $10.00 (Should cost 1000 points)
        # 10.00 / 0.01 = 1000 points
        
        payment = POSService.process_payment(
            transaction=txn,
            payment_method='loyalty', # Method might be overridden by redeem_points flag logic or explicit method
            amount=Decimal("10.00"),
            user=self.user,
            redeem_points=True
        )
        
        self.loyalty_profile.refresh_from_db()
        
        # Check Points Deducted
        # Initial 5000 - 1000 = 4000
        self.assertEqual(self.loyalty_profile.points_balance, 4000)
        
        # Check Transaction Ledger
        ledger = LoyaltyTransaction.objects.filter(
            loyalty_account=self.loyalty_profile,
            transaction_type='redeem'
        ).last()
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger.points, -1000)
        
        # Check remaining balance on transaction
        txn.refresh_from_db()
        self.assertEqual(txn.amount_paid, Decimal("10.00"))
        # Pay Remaining $90
        POSService.process_payment(
            transaction=txn,
            payment_method='cash',
            amount=Decimal("90.00"),
            user=self.user
        )
        
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'completed')
        
    def test_loyalty_earning(self):
        """Test earning points on purchase."""
        
        # Create Transaction ($100)
        txn = POSService.create_transaction(self.session, self.user, customer=self.customer)
        POSService.add_line_item(txn, self.product, quantity=1)
        
        # Pay full cash
        POSService.process_payment(
            transaction=txn,
            payment_method='cash',
            amount=Decimal("100.00"),
            user=self.user
        )
        
        self.loyalty_profile.refresh_from_db()
        
        # Earned 100 points (100 * 1.0)
        # Initial 5000 + 100 = 5100
        self.assertEqual(self.loyalty_profile.points_balance, 5100)
        
        ledger = LoyaltyTransaction.objects.filter(
            loyalty_account=self.loyalty_profile,
            transaction_type='earn'
        ).last()
        self.assertEqual(ledger.points, 100)
