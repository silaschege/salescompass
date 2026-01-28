from django.test import TestCase
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from pos.models import POSSession, POSTerminal, POSTransaction, POSTransactionLine, POSPayment
from pos.services import POSService
from products.models import Product
from decimal import Decimal
from django.urls import reverse
import json

class POSPhase1Test(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Phase 1 Tenant", schema_name="phase1")
        self.user = User.objects.create_user(username="cashier1", email="cashier1@test.com", password="password")
        self.tenant.users.add(self.user)
        self.client.force_login(self.user)
        
        # Setup Terminal
        self.terminal = POSTerminal.objects.create(
            tenant=self.tenant,
            terminal_name="Main Till",
            terminal_code="TILL01"
        )
        
        # Setup Products
        self.product1 = Product.objects.create(
            tenant=self.tenant,
            product_name="Bread",
            sku="BRD001",
            upc="123456789",
            base_price=Decimal("50.00")
        )
        self.product2 = Product.objects.create(
            tenant=self.tenant,
            product_name="Milk",
            sku="MLK001",
            upc="987654321",
            base_price=Decimal("100.00")
        )
        
        # Open Session
        self.session = POSService.open_session(self.terminal, self.user)

    def test_split_payments(self):
        """Test multiple payments for a single transaction."""
        txn = POSService.create_transaction(self.session, self.user)
        POSService.add_line_item(txn, self.product2, quantity=2) # Total 200.00
        
        # First payment: Cash 100.00
        url = reverse('pos:api_transaction_pay', kwargs={'pk': txn.id})
        response = self.client.post(url, json.dumps({
            'payment_methods': [{'method': 'cash', 'amount': 100.00}]
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'partial')
        self.assertEqual(Decimal(data['remaining']), Decimal('100.00'))
        
        # Second payment: Card 100.00
        response = self.client.post(url, json.dumps({
            'payment_methods': [{'method': 'card', 'amount': 100.00, 'reference_number': 'CRD-123'}]
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'completed')
        
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'completed')
        self.assertEqual(txn.amount_paid, Decimal('200.00'))
        self.assertEqual(txn.payments.count(), 2)

    def test_hold_resume_transaction(self):
        """Test holding and resuming a transaction."""
        txn = POSService.create_transaction(self.session, self.user)
        POSService.add_line_item(txn, self.product1, quantity=3) # 150.00
        
        # Hold
        hold_url = reverse('pos:api_transaction_hold', kwargs={'pk': txn.id})
        response = self.client.post(hold_url)
        self.assertEqual(response.status_code, 200)
        
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'on_hold')
        
        # List held
        list_url = reverse('pos:api_held_transactions')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(t['id'] == txn.id for t in data['transactions']))
        
        # Resume
        resume_url = reverse('pos:api_transaction_resume', kwargs={'pk': txn.id})
        response = self.client.post(resume_url)
        self.assertEqual(response.status_code, 200)
        
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'draft')

    def test_barcode_lookup(self):
        """Test searching product by barcode."""
        url = reverse('pos:api_product_barcode', kwargs={'barcode': '123456789'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['product']['name'], 'Bread')
