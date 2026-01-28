from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from products.models import Product, Coupon
from products.services import PromotionService
from accounts.models import Account

class PromotionVerification(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", password="password", tenant=self.tenant
        )
        self.product = Product.objects.create(
            product_name="Item 1", sku="ITM-001", base_price=100.00, 
            tenant=self.tenant, owner=self.user
        )
        
        # Coupon: SAVE10 (10% off)
        self.coupon = Coupon.objects.create(
            code="SAVE10", discount_type="percentage", discount_value=10.00,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=5),
            tenant=self.tenant
        )
        
        # Fixed Coupon: MINUS5 ($5 off, min purchase $50)
        self.fixed_coupon = Coupon.objects.create(
            code="MINUS5", discount_type="fixed", discount_value=5.00,
            min_purchase_amount=50.00,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=5),
            tenant=self.tenant
        )

    def test_coupon_validation(self):
        # 1. Valid Percentage Coupon
        valid, msg, c = PromotionService.validate_coupon("SAVE10", self.tenant, cart_total=100)
        self.assertTrue(valid)
        self.assertEqual(c, self.coupon)
        
        # 2. Invalid Code
        valid, msg, c = PromotionService.validate_coupon("INVALID", self.tenant)
        self.assertFalse(valid)
        
        # 3. Minimum Purchase check
        valid, msg, c = PromotionService.validate_coupon("MINUS5", self.tenant, cart_total=40)
        self.assertFalse(valid)
        self.assertIn("Minimum purchase", msg)
        
        valid, msg, c = PromotionService.validate_coupon("MINUS5", self.tenant, cart_total=60)
        self.assertTrue(valid)
        
    def test_calculation(self):
        # 10% of 200 = 20
        discount = PromotionService.calculate_discount(self.coupon, Decimal('200.00'))
        self.assertEqual(discount, Decimal('20.00'))
        
        # Fixed 5
        discount = PromotionService.calculate_discount(self.fixed_coupon, Decimal('200.00'))
        self.assertEqual(discount, Decimal('5.00'))
        
    def test_usage_limit(self):
        limit_coupon = Coupon.objects.create(
            code="LIMIT1", discount_type="fixed", discount_value=1,
            start_date=timezone.now(), end_date=timezone.now()+timedelta(days=1),
            usage_limit=1, tenant=self.tenant
        )
        
        # First use OK
        valid, _, _ = PromotionService.validate_coupon("LIMIT1", self.tenant)
        self.assertTrue(valid)
        
        PromotionService.use_coupon(limit_coupon)
        
        # Second use Fails
        valid, msg, _ = PromotionService.validate_coupon("LIMIT1", self.tenant)
        self.assertFalse(valid)
        self.assertIn("limit reached", msg)
        
        print("Promotions Logic: OK")
