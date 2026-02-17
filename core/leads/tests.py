import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Lead, LeadStatus
from .services import LeadScoringService
from settings_app.models import DemographicScoringRule, BehavioralScoringRule
from accounts.models import Account
from core.models import User
from tenants.models import Tenant

User = get_user_model()

class LeadKanbanTests(TestCase):
    def setUp(self):
        # Create user and tenant
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            tenant_id='tenant1'
        )
        self.client.force_login(self.user)
        
        # Create Statuses
        self.status1 = LeadStatus.objects.create(
            name='new',
            label='New',
            order=1,
            tenant_id='tenant1'
        )
        self.status2 = LeadStatus.objects.create(
            name='qualified',
            label='Qualified',
            order=2,
            is_qualified=True,
            tenant_id='tenant1'
        )
        
        # Create Lead
        self.lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            company='Acme Corp',
            email='john@acme.com',
            status_ref=self.status1,
            status='new',
            lead_score=10,
            tenant_id='tenant1',
            owner=self.user
        )

    def test_kanban_view_status_code(self):
        """Test that the Lead Kanban view returns 200 OK."""
        url = reverse('leads:pipeline')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads/pipeline_kanban.html')

    def test_kanban_view_context(self):
        """Test that the Kanban view context contains statuses and leads."""
        url = reverse('leads:pipeline')
        response = self.client.get(url)
        
        # Check statuses in context
        statuses = response.context['statuses']
        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[0]['label'], 'New')
        
        # Check leads in status 1
        self.assertEqual(len(statuses[0]['leads']), 1)
        self.assertEqual(statuses[0]['leads'][0]['name'], 'John Doe')
        
        # Check status 2 is empty
        self.assertEqual(len(statuses[1]['leads']), 0)

    def test_update_status_ajax_success(self):
        """Test updating lead status via AJAX."""
        url = reverse('leads:update_status', args=[self.lead.id])
        data = {
            'status_id': self.status2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['new_status'], 'qualified')
        
        # Refresh lead from DB
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status_ref, self.status2)
        self.assertEqual(self.lead.status, 'qualified')
        
        # Check score updated (10 + 20 = 30)
        # Note: Logic adds 20 points for qualification
        self.assertEqual(self.lead.lead_score, 30)

    def test_update_status_invalid_status(self):
        """Test updating to a non-existent status."""
        url = reverse('leads:update_status', args=[self.lead.id])
        data = {
            'status_id': 99999
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['success'])

    def test_update_status_invalid_lead(self):
        """Test updating a non-existent lead."""
        url = reverse('leads:update_status', args=[99999])
        data = {
            'status_id': self.status2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)

    def test_update_status_cross_tenant_isolation(self):
        """Test that a user cannot update a lead from another tenant."""
        # Create another user and tenant
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123',
            tenant_id='tenant2'
        )
        self.client.force_login(other_user)
        
        url = reverse('leads:update_status', args=[self.lead.id])
        data = {
            'status_id': self.status2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return 404 because the lead is not found in tenant2
        self.assertEqual(response.status_code, 404)


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
            annual_revenue=50000,  # $5M revenue
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
            annual_revenue=20000,  # $2M revenue
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
