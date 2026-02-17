"""
Quick test suite using Django TestCase for faster execution.

This file provides Django-native tests that work with 'python manage.py test'.
These tests are designed to work without the full migration overhead.
"""
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from accounts.models import Account, Contact
from leads.models import Lead, LeadStatus, LeadSource
from opportunities.models import Opportunity, OpportunityStage
from decimal import Decimal

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test case with common setup for multi-tenant tests."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase - runs once per TestCase."""
        # Create tenant
        cls.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            subdomain='test',
            is_active=True
        )
        
        # Create user
        cls.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123',
            tenant=cls.tenant
        )
        
        # Create a second tenant for isolation tests
        cls.other_tenant = Tenant.objects.create(
            name='Other Tenant',
            slug='other-tenant',
            subdomain='other',
            is_active=True
        )
        
        cls.other_user = User.objects.create_user(
            email='otheruser@example.com',
            username='otheruser',
            password='testpass123',
            tenant=cls.other_tenant
        )


class AccountModelTests(BaseTestCase):
    """Tests for the Account model."""
    
    def test_account_creation(self):
        """Test basic account creation."""
        account = Account.objects.create(
            account_name='Acme Corp',
            industry='tech',
            tenant=self.tenant,
            owner=self.user
        )
        self.assertIsNotNone(account.pk)
        self.assertEqual(account.account_name, 'Acme Corp')
        self.assertEqual(account.tenant, self.tenant)
    
    def test_account_str_representation(self):
        """Test account string representation."""
        account = Account.objects.create(
            account_name='Test Company',
            tenant=self.tenant,
            owner=self.user
        )
        self.assertEqual(str(account), 'Test Company')
    
    def test_account_tenant_isolation(self):
        """Test accounts are isolated by tenant."""
        account1 = Account.objects.create(
            account_name='Account 1',
            tenant=self.tenant,
            owner=self.user
        )
        account2 = Account.objects.create(
            account_name='Account 2',
            tenant=self.other_tenant,
            owner=self.other_user
        )
        
        tenant1_accounts = Account.objects.filter(tenant=self.tenant)
        self.assertIn(account1, tenant1_accounts)
        self.assertNotIn(account2, tenant1_accounts)


class ContactModelTests(BaseTestCase):
    """Tests for the Contact model."""
    
    def setUp(self):
        """Set up test data for each test method."""
        self.account = Account.objects.create(
            account_name='Test Account',
            tenant=self.tenant,
            owner=self.user
        )
    
    def test_contact_creation(self):
        """Test basic contact creation."""
        contact = Contact.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            account=self.account,
            tenant=self.tenant
        )
        self.assertIsNotNone(contact.pk)
        self.assertEqual(contact.first_name, 'John')
        self.assertEqual(contact.account, self.account)
    
    def test_contact_account_relationship(self):
        """Test contact is properly linked to account."""
        contact = Contact.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            account=self.account,
            tenant=self.tenant
        )
        self.assertEqual(contact.account, self.account)
        self.assertIn(contact, self.account.contacts.all())


class LeadModelTests(BaseTestCase):
    """Tests for the Lead model."""
    
    def setUp(self):
        """Set up test data for each test method."""
        self.lead_status = LeadStatus.objects.create(
            status_name='new',
            label='New',
            order=1,
            tenant=self.tenant
        )
        self.lead_status_qualified = LeadStatus.objects.create(
            status_name='qualified',
            label='Qualified',
            order=2,
            is_qualified=True,
            tenant=self.tenant
        )
    
    def test_lead_creation(self):
        """Test basic lead creation."""
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            company='Acme Corp',
            status='new',
            status_ref=self.lead_status,
            owner=self.user,
            tenant=self.tenant
        )
        self.assertIsNotNone(lead.pk)
        self.assertEqual(lead.first_name, 'John')
        self.assertEqual(lead.company, 'Acme Corp')
    
    def test_lead_full_name(self):
        """Test lead full_name property."""
        lead = Lead.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            company='Test Corp',
            status='new',
            status_ref=self.lead_status,
            owner=self.user,
            tenant=self.tenant
        )
        self.assertEqual(lead.full_name, 'Jane Smith')
    
    def test_lead_status_transition(self):
        """Test updating lead status."""
        lead = Lead.objects.create(
            first_name='Test',
            last_name='Lead',
            email='test@example.com',
            company='Test Co',
            status='new',
            status_ref=self.lead_status,
            owner=self.user,
            tenant=self.tenant
        )
        
        # Update status
        lead.status_ref = self.lead_status_qualified
        lead.status = 'qualified'
        lead.save()
        
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'qualified')
        self.assertTrue(lead.status_ref.is_qualified)
    
    def test_lead_tenant_isolation(self):
        """Test leads are isolated by tenant."""
        lead1 = Lead.objects.create(
            first_name='Lead',
            last_name='One',
            email='lead1@example.com',
            company='Company 1',
            status='new',
            status_ref=self.lead_status,
            owner=self.user,
            tenant=self.tenant
        )
        
        other_status = LeadStatus.objects.create(
            status_name='new',
            label='New',
            order=1,
            tenant=self.other_tenant
        )
        
        lead2 = Lead.objects.create(
            first_name='Lead',
            last_name='Two',
            email='lead2@example.com',
            company='Company 2',
            status='new',
            status_ref=other_status,
            owner=self.other_user,
            tenant=self.other_tenant
        )
        
        tenant1_leads = Lead.objects.filter(tenant=self.tenant)
        self.assertIn(lead1, tenant1_leads)
        self.assertNotIn(lead2, tenant1_leads)


class OpportunityModelTests(BaseTestCase):
    """Tests for the Opportunity model."""
    
    def setUp(self):
        """Set up test data for each test method."""
        self.account = Account.objects.create(
            account_name='Test Account',
            tenant=self.tenant,
            owner=self.user
        )
        self.stage = OpportunityStage.objects.create(
            name='prospecting',
            label='Prospecting',
            order=1,
            probability=Decimal('10.00'),
            tenant=self.tenant
        )
        self.stage_won = OpportunityStage.objects.create(
            name='closed_won',
            label='Closed Won',
            order=5,
            probability=Decimal('100.00'),
            is_won=True,
            tenant=self.tenant
        )
    
    def test_opportunity_creation(self):
        """Test basic opportunity creation."""
        opp = Opportunity.objects.create(
            opportunity_name='New Deal',
            account=self.account,
            stage=self.stage,
            amount=Decimal('50000.00'),
            probability=Decimal('10.00'),
            tenant=self.tenant
        )
        self.assertIsNotNone(opp.pk)
        self.assertEqual(opp.opportunity_name, 'New Deal')
        self.assertEqual(opp.amount, Decimal('50000.00'))
    
    def test_opportunity_weighted_value(self):
        """Test weighted value calculation."""
        opp = Opportunity.objects.create(
            opportunity_name='Deal 1',
            account=self.account,
            stage=self.stage,
            amount=Decimal('100000.00'),
            probability=Decimal('50.00'),
            tenant=self.tenant
        )
        expected_weighted = Decimal('100000.00') * Decimal('0.50')
        self.assertEqual(opp.weighted_value, expected_weighted)
    
    def test_opportunity_stage_transition(self):
        """Test moving opportunity through stages."""
        opp = Opportunity.objects.create(
            opportunity_name='Deal 2',
            account=self.account,
            stage=self.stage,
            amount=Decimal('75000.00'),
            probability=Decimal('10.00'),
            tenant=self.tenant
        )
        
        # Move to won stage
        opp.stage = self.stage_won
        opp.probability = Decimal('100.00')
        opp.save()
        
        opp.refresh_from_db()
        self.assertTrue(opp.stage.is_won)
        self.assertEqual(opp.probability, Decimal('100.00'))


class LeadToOpportunityConversionTests(BaseTestCase):
    """Integration tests for lead to opportunity conversion."""
    
    def setUp(self):
        """Set up test data."""
        self.lead_status_new = LeadStatus.objects.create(
            status_name='new',
            label='New',
            order=1,
            tenant=self.tenant
        )
        self.lead_status_qualified = LeadStatus.objects.create(
            status_name='qualified',
            label='Qualified',
            order=2,
            is_qualified=True,
            tenant=self.tenant
        )
        self.lead_status_closed = LeadStatus.objects.create(
            status_name='closed_won',
            label='Closed Won',
            order=3,
            is_closed=True,
            is_qualified=True,
            tenant=self.tenant
        )
        self.opp_stage = OpportunityStage.objects.create(
            name='prospecting',
            label='Prospecting',
            order=1,
            probability=Decimal('10.00'),
            tenant=self.tenant
        )
    
    def test_full_conversion_flow(self):
        """Test complete lead to opportunity conversion."""
        # Step 1: Create lead
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@acme.com',
            company='Acme Corp',
            status='new',
            status_ref=self.lead_status_new,
            owner=self.user,
            tenant=self.tenant,
            lead_score=50
        )
        self.assertEqual(lead.status, 'new')
        
        # Step 2: Qualify lead
        lead.status_ref = self.lead_status_qualified
        lead.status = 'qualified'
        lead.lead_score = 75
        lead.save()
        
        self.assertTrue(lead.status_ref.is_qualified)
        
        # Step 3: Create account from lead
        account = Account.objects.create(
            account_name=lead.company,
            tenant=self.tenant,
            owner=self.user
        )
        self.assertEqual(account.account_name, 'Acme Corp')
        
        # Step 4: Create opportunity
        opportunity = Opportunity.objects.create(
            opportunity_name=f'Deal - {lead.company}',
            account=account,
            stage=self.opp_stage,
            amount=Decimal('50000.00'),
            probability=Decimal('10.00'),
            tenant=self.tenant
        )
        
        # Step 5: Mark lead as converted
        lead.status_ref = self.lead_status_closed
        lead.status = 'closed_won'
        lead.save()
        
        # Verify final state
        lead.refresh_from_db()
        self.assertTrue(lead.status_ref.is_closed)
        self.assertEqual(opportunity.account.account_name, lead.company)
    
    def test_conversion_preserves_tenant(self):
        """Test conversion maintains tenant isolation."""
        lead = Lead.objects.create(
            first_name='Test',
            last_name='User',
            email='test@company.com',
            company='Test Company',
            status='new',
            status_ref=self.lead_status_new,
            owner=self.user,
            tenant=self.tenant
        )
        
        account = Account.objects.create(
            account_name=lead.company,
            tenant=self.tenant,
            owner=self.user
        )
        
        opportunity = Opportunity.objects.create(
            opportunity_name=f'Opportunity - {lead.company}',
            account=account,
            stage=self.opp_stage,
            amount=Decimal('25000.00'),
            probability=Decimal('10.00'),
            tenant=self.tenant
        )
        
        # All should have same tenant
        self.assertEqual(lead.tenant, self.tenant)
        self.assertEqual(account.tenant, self.tenant)
        self.assertEqual(opportunity.tenant, self.tenant)
