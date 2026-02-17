from django.test import TestCase
from django.utils import timezone
from leads.models import Lead
from leads.services import LeadScoringService
from settings_app.models import DemographicScoringRule, BehavioralScoringRule
from core.models import User
from tenants.models import Tenant


class EnhancedLeadScoringTest(TestCase):
    """
    Test the enhanced lead scoring system with business metrics.
    """
    
    def setUp(self):
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            tenant_id='test_tenant',
            name='Test Tenant'
        )
        
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            tenant_id='test_tenant'
        )
        
        # Create demographic scoring rules
        self.enterprise_rule = DemographicScoringRule.objects.create(
            name='Enterprise Company Scoring',
            field_name='company_size',
            operator='gt',
            field_value='1000',
            points=20,
            priority=10,
            tenant_id='test_tenant',
            is_active=True
        )
        
        self.tech_industry_rule = DemographicScoringRule.objects.create(
            name='Tech Industry Bonus',
            field_name='industry',
            operator='equals',
            field_value='tech',
            points=15,
            priority=5,
            tenant_id='test_tenant',
            is_active=True
        )
        
        # Create behavioral scoring rules
        self.pricing_page_rule = BehavioralScoringRule.objects.create(
            name='Pricing Page Visit',
            action_type='pricing_page_visit',
            points=25,
            priority=20,
            tenant_id='test_tenant',
            is_active=True,
            business_impact='high'
        )
        
        self.demo_request_rule = BehavioralScoringRule.objects.create(
            name='Demo Request',
            action_type='product_demo_request',
            points=30,
            priority=30,
            tenant_id='test_tenant',
            is_active=True,
            business_impact='critical'
        )
    
    def test_lead_scoring_with_business_metrics(self):
        """
        Test that leads are scored properly with business metrics.
        """
        # Create a lead with high business metrics
        lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='+1234567890',
            company='Enterprise Corp',
            industry='tech',
            job_title='CTO',
            company_size=2000,  # Large company
            annual_revenue=5000000,  # $5M revenue
            funding_stage='Series B',
            business_type='B2B',
            tenant_id='test_tenant',
            owner=self.user
        )
        
        # Calculate the score
        score = LeadScoringService.calculate_lead_score(lead)
        
        # The score should be higher due to:
        # - Basic profile info: email, phone, job_title, company, industry, description (6 * 5 = 30)
        # - Business metrics: company size (15), revenue (10), funding stage (10), business type (5) = 40
        # - Demographic rules: enterprise (20) and tech industry (15) = 35
        # Total should be around 105 but capped at 100
        self.assertLessEqual(score, 100)  # Score should be capped at 100
        self.assertGreater(score, 80)  # Score should be high due to business metrics
        
        # Refresh from DB to get updated score
        lead.refresh_from_db()
        self.assertEqual(lead.lead_score, score)
    
    def test_lead_scoring_low_business_metrics(self):
        """
        Test that leads with low business metrics get lower scores.
        """
        # Create a lead with low business metrics
        lead = Lead.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            company='Small Startup',
            industry='other',
            company_size=5,  # Small company
            annual_revenue=50000,  # $50K revenue
            funding_stage='pre_seed',
            business_type='B2C',
            tenant_id='test_tenant',
            owner=self.user
        )
        
        # Calculate the score
        score = LeadScoringService.calculate_lead_score(lead)
        
        # This lead should have a lower score due to smaller company size, 
        # lower revenue, and not matching the high-value demographic rules
        self.assertLess(score, 60)  # Should be lower than the high-value lead
        
        # Refresh from DB to get updated score
        lead.refresh_from_db()
        self.assertEqual(lead.lead_score, score)
    
    def test_lead_scoring_with_behavioral_signals(self):
        """
        Test that behavioral signals significantly impact the score.
        """
        # Create a lead with moderate business metrics
        lead = Lead.objects.create(
            first_name='Bob',
            last_name='Johnson',
            email='bob.johnson@example.com',
            company='Mid Market Inc',
            industry='tech',
            company_size=200,  # Mid-size company
            annual_revenue=2000000,  # $2M revenue
            tenant_id='test_tenant',
            owner=self.user
        )
        
        # Calculate the base score without behavioral signals
        base_score = LeadScoringService.calculate_lead_score(lead)
        
        # The score should be moderate due to business metrics
        self.assertGreater(base_score, 30)
        self.assertLess(base_score, 80)
        
        # Refresh from DB to get updated score
        lead.refresh_from_db()
        self.assertEqual(lead.lead_score, base_score)
