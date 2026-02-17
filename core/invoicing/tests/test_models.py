
from django.test import TestCase
from tenants.models import Tenant
from core.models import User
from invoicing.models import Invoice
from billing.models import Subscription, Plan
from datetime import date
from decimal import Decimal

class InvoiceModelTest(TestCase):

    def setUp(self):
        # Create unique tenant and user for each test run to avoid unique constraint issues
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant-model", schema_name="test_tenant_model")
        self.user = User.objects.create_user(username="testuser_model", email="test_model@example.com", password="password")
        self.plan = Plan.objects.create(name="Test Plan", price=100)
        self.subscription = Subscription.objects.create(
            tenant=self.tenant,
            user=self.user,
            subscription_plan=self.plan
        )

    def test_create_invoice(self):
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            subscription=self.subscription,
            amount=Decimal("100.00"),
            due_date=date.today(),
            invoice_number="INV-TEST-001"
        )
        self.assertEqual(invoice.invoice_number, "INV-TEST-001")
        self.assertEqual(Invoice.objects.count(), 1)
