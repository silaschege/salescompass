from django.test import TestCase
from django.contrib.auth import get_user_model
from billing.models import Plan, Subscription
from core.models import TenantModel
from django.core.exceptions import ValidationError

User = get_user_model()

class BillingTests(TestCase):
    def setUp(self):
        # Create Plans
        self.starter_plan = Plan.objects.create(
            name="Starter",
            slug="starter",
            tier="starter",
            price_monthly=29.00,
            price_yearly=290.00,
            max_users=2,
            max_leads=5
        )
        self.pro_plan = Plan.objects.create(
            name="Pro",
            slug="pro",
            tier="pro",
            price_monthly=99.00,
            price_yearly=990.00,
            max_users=10,
            max_leads=100
        )
        
        # Create Tenant User (Owner)
        self.tenant_id = "tenant_123"
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="password",
            tenant_id=self.tenant_id
        )

    def test_subscription_creation(self):
        """Test that a subscription can be created and linked to a tenant."""
        sub = Subscription.objects.create(
            tenant_id=self.tenant_id,
            plan=self.starter_plan,
            status='active'
        )
        self.assertEqual(sub.plan, self.starter_plan)
        self.assertTrue(sub.is_valid)

    def test_user_limit_enforcement(self):
        """Test that creating users beyond the plan limit raises ValidationError."""
        # Create active subscription for Starter plan (max_users=2)
        Subscription.objects.create(
            tenant_id=self.tenant_id,
            plan=self.starter_plan,
            status='active'
        )
        
        # We already have 1 user (self.user)
        
        # Create 2nd user (Should succeed)
        user2 = User.objects.create_user(
            username="user2@example.com",
            email="user2@example.com",
            password="password",
            tenant_id=self.tenant_id
        )
        
        # Create 3rd user (Should fail)
        with self.assertRaises(ValidationError):
            user3 = User(
                username="user3@example.com",
                email="user3@example.com",
                tenant_id=self.tenant_id
            )
            user3.save()

    def test_lead_limit_enforcement(self):
        """Test that creating leads beyond the plan limit raises ValidationError."""
        from leads.models import Lead
        
        # Create active subscription for Starter plan (max_leads=5)
        Subscription.objects.create(
            tenant_id=self.tenant_id,
            plan=self.starter_plan,
            status='active'
        )
        
        # Create 5 leads (Should succeed)
        for i in range(5):
            Lead.objects.create(
                first_name=f"Lead {i}",
                last_name="Test",
                email=f"lead{i}@test.com",
                company="Test Corp",
                tenant_id=self.tenant_id
            )
            
        # Create 6th lead (Should fail)
        with self.assertRaises(ValidationError):
            lead6 = Lead(
                first_name="Lead 6",
                last_name="Test",
                email="lead6@test.com",
                company="Test Corp",
                tenant_id=self.tenant_id
            )
            lead6.save()
