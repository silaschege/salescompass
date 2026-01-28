from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from products.models import Product, PricingTier, PriceList, PriceListItem
from products.services import PricingService
from accounts.models import Account

class PricingVerification(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", password="password", tenant=self.tenant
        )
        
        # Product: Base $100
        self.product = Product.objects.create(
            product_name="Pro Widget", sku="WID-001", base_price=100.00, 
            tenant=self.tenant, owner=self.user
        )
        
        # Tier: 10+ items = $90
        PricingTier.objects.create(
            product=self.product, min_quantity=10, unit_price=90.00, tenant=self.tenant
        )
        
        # Price List: VIP = $80
        self.vip_list = PriceList.objects.create(name="VIP", tenant=self.tenant)
        PriceListItem.objects.create(
            price_list=self.vip_list, product=self.product, price=80.00, tenant=self.tenant
        )
        
        # Accounts
        self.acc_std = Account.objects.create(account_name="Standard Inc", tenant=self.tenant, owner=self.user)
        self.acc_vip = Account.objects.create(account_name="VIP Inc", price_list=self.vip_list, tenant=self.tenant, owner=self.user)

    def test_pricing_hierarchy(self):
        # 1. Base Price (Standard user, qty 1)
        price = PricingService.get_price(self.product, self.acc_std, 1)
        self.assertEqual(price, Decimal('100.00'))
        
        # 2. Tiered Price (Standard user, qty 10)
        price = PricingService.get_price(self.product, self.acc_std, 10)
        self.assertEqual(price, Decimal('90.00'))
        
        # 3. Price List (VIP user, qty 1) - overrides base
        price = PricingService.get_price(self.product, self.acc_vip, 1)
        self.assertEqual(price, Decimal('80.00'))
        
        # 4. Price List wins over Tier? Or Tier within Price List?
        # Current logic: Price List is checked first. If found, returns that. 
        # Ideally Price List should also support tiers, but for now simple override.
        price = PricingService.get_price(self.product, self.acc_vip, 10)
        self.assertEqual(price, Decimal('80.00')) # VIP fixed price
        
        print("Pricing Logic: OK")
