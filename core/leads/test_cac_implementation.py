"""
Test module to verify the CAC (Customer Acquisition Cost) implementation in the Lead model.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from leads.models import Lead, Industry, LeadSource, LeadStatus, MarketingChannel
from accounts.models import Account


class LeadCACImplementationTest(TestCase):
    def setUp(self):
        # Create a tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            subdomain="test-tenant"
        )
        
        # Create a user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Create industry
        self.industry = Industry.objects.create(
            name="tech",
            label="Technology",
            tenant_id=self.tenant.id
        )
        
        # Create lead source
        self.lead_source = LeadSource.objects.create(
            name="ads",
            label="Paid Ads",
            tenant_id=self.tenant.id
        )
        
        # Create lead status
        self.lead_status = LeadStatus.objects.create(
            name="new",
            label="New",
            tenant_id=self.tenant.id
        )
        
        # Create marketing channel
        self.marketing_channel = MarketingChannel.objects.create(
            channel_name="email",
            label="Email Marketing",
            tenant_id=self.tenant.id
        )
        
        # Set tenant_id for user
        self.user.tenant_id = self.tenant.id
        self.user.save()

    def test_marketing_channel_model(self):
        """Test that MarketingChannel model works correctly"""
        self.assertEqual(self.marketing_channel.channel_name, "email")
        self.assertEqual(self.marketing_channel.label, "Email Marketing")
        self.assertEqual(self.marketing_channel.tenant_id, self.tenant.id)
        self.assertTrue(self.marketing_channel.channel_is_active)
        self.assertFalse(self.marketing_channel.is_system)
        
        # Test string representation
        self.assertEqual(str(self.marketing_channel), "Email Marketing")
    
    def test_lead_marketing_channel_ref_field(self):
        """Test that the marketing_channel_ref field works correctly"""
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            marketing_channel_ref=self.marketing_channel
        )
        
        self.assertEqual(lead.marketing_channel_ref, self.marketing_channel)
        self.assertEqual(lead.marketing_channel_ref.label, "Email Marketing")
    
    # Remove duplicate test methods - keep only the first occurrence

    def test_cac_field_exists_and_is_decimal(self):
        """Test that cac_cost field exists and is a DecimalField"""
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            cac_cost=Decimal('50.00')
        )
        
        self.assertEqual(lead.cac_cost, Decimal('50.00'))
        self.assertIsInstance(lead.cac_cost, Decimal)

    def test_marketing_channel_field_exists(self):
        """Test that marketing_channel field exists with choices"""
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            marketing_channel="paid_ads"
        )
        
        self.assertEqual(lead.marketing_channel, "paid_ads")
        # Check that the value is one of the valid choices
        valid_choices = [choice[0] for choice in Lead.MARKETING_CHANNEL_CHOICES]
        self.assertIn(lead.marketing_channel, valid_choices)

    def test_campaign_source_field_exists(self):
        """Test that campaign_source field exists"""
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            campaign_source="Summer Sale Campaign"
        )
        
        self.assertEqual(lead.campaign_source, "Summer Sale Campaign")

    def test_lead_acquisition_date_field_exists(self):
        """Test that lead_acquisition_date field exists and auto-sets on creation"""
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id
        )
        
        # Check that acquisition date is set automatically
        self.assertIsNotNone(lead.lead_acquisition_date)
        self.assertIsInstance(lead.lead_acquisition_date, datetime)

    def test_calculate_cac_method(self):
        """Test the calculate_cac method"""
        lead = Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            cac_cost=Decimal('75.50')
        )
        
        cac = lead.calculate_cac()
        self.assertEqual(cac, Decimal('75.50'))
        
        # Test with no cac_cost set
        lead_no_cost = Lead.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id
        )
        
        cac_no_cost = lead_no_cost.calculate_cac()
        self.assertEqual(cac_no_cost, 0.0)

    def test_get_channel_metrics(self):
        """Test the get_channel_metrics class method"""
        # Create multiple leads for the same channel
        Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            marketing_channel="paid_ads",
            cac_cost=Decimal('100.00'),
            status="converted"
        )
        
        Lead.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            company="Test Company 2",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            marketing_channel="paid_ads",
            cac_cost=Decimal('50.00'),
            status="new"
        )
        
        # Get metrics for the paid_ads channel
        metrics = Lead.get_channel_metrics("paid_ads", tenant_id=self.tenant.id)
        
        self.assertEqual(metrics['channel'], "paid_ads")
        self.assertEqual(metrics['total_leads'], 2)
        self.assertEqual(metrics['total_cac_spent'], 150.0)
        self.assertEqual(metrics['average_cac'], 75.0)
        self.assertEqual(metrics['converted_leads'], 1)
        self.assertEqual(metrics['conversion_rate'], 50.0)

    def test_get_campaign_metrics(self):
        """Test the get_campaign_metrics class method"""
        # Create multiple leads for the same campaign
        Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            campaign_source="Email Campaign Q3",
            cac_cost=Decimal('30.00'),
            status="converted"
        )
        
        Lead.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            company="Test Company 2",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            campaign_source="Email Campaign Q3",
            cac_cost=Decimal('40.00'),
            status="new"
        )
        
        # Get metrics for the email campaign
        metrics = Lead.get_campaign_metrics("Email Campaign Q3", tenant_id=self.tenant.id)
        
        self.assertEqual(metrics['campaign'], "Email Campaign Q3")
        self.assertEqual(metrics['total_leads'], 2)
        self.assertEqual(metrics['total_cac_spent'], 70.0)
        self.assertEqual(metrics['average_cac'], 35.0)
        self.assertEqual(metrics['converted_leads'], 1)
        self.assertEqual(metrics['conversion_rate'], 50.0)

    def test_get_total_cac_by_period(self):
        """Test the get_total_cac_by_period class method"""
        # Create leads with different acquisition dates
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        Lead.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            cac_cost=Decimal('25.00'),
            lead_acquisition_date=timezone.now() - timedelta(days=1)
        )
        
        Lead.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            company="Test Company 2",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id,
            cac_cost=Decimal('35.00'),
            lead_acquisition_date=timezone.now()
        )
        
        # Get CAC for the last 2 days
        metrics = Lead.get_total_cac_by_period(
            start_date=yesterday,
            end_date=today,
            tenant_id=self.tenant.id
        )
        
        self.assertEqual(metrics['period_start'], yesterday)
        self.assertEqual(metrics['period_end'], today)
        self.assertEqual(metrics['total_leads'], 2)
        self.assertEqual(metrics['total_cac_spent'], 60.0)
        self.assertAlmostEqual(metrics['average_cac'], 30.0, places=2)

    def test_save_sets_acquisition_date(self):
        """Test that save method automatically sets lead_acquisition_date"""
        lead = Lead(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company="Test Company",
            industry="tech",
            owner=self.user,
            tenant_id=self.tenant.id
        )
        
        # Save the lead
        lead.save()
        
        # Check that acquisition date was set
        self.assertIsNotNone(lead.lead_acquisition_date)
        self.assertIsInstance(lead.lead_acquisition_date, datetime)
        
        # Check that it's close to current time
        time_diff = abs((timezone.now() - lead.lead_acquisition_date).total_seconds())
        self.assertLess(time_diff, 60)  # Should be within 60 seconds


if __name__ == '__main__':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    import django
    django.setup()
    unittest.main()
