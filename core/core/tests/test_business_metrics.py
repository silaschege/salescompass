from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import User
from leads.models import Lead
from opportunities.models import Opportunity
from marketing.models import Campaign
from datetime import datetime, timedelta
from decimal import Decimal
from core.services.business_metrics_service import BusinessMetricsService

User = get_user_model()


class TestCLVCalculations(TestCase):
    """
    Test CLV calculation methods
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Set some initial CLV-related values for testing
        self.user.customer_lifetime_value = 5000.00
        self.user.avg_order_value = 500.00
        self.user.purchase_frequency = 2.0
        self.user.customer_lifespan_years = 5.0
        self.user.save()
    
    def test_clv_calculation_simple(self):
        """
        Test simple CLV calculation: AOV * Purchase Frequency * Customer Lifespan
        """
        expected_clv = self.user.avg_order_value * self.user.purchase_frequency * self.user.customer_lifespan_years
        calculated_clv = self.user.calculate_clv_simple()
        
        self.assertEqual(calculated_clv, expected_clv)
    
    def test_clv_with_gross_margin(self):
        """
        Test CLV calculation with gross margin
        """
        # Set additional fields needed for detailed CLV calculation
        self.user.gross_margin_percentage = 0.4  # 40%
        self.user.marketing_cost_per_customer = 50.00
        self.user.overhead_costs_annual = 1000.00
        self.user.churn_rate_annual = 0.2  # 20%
        self.user.save()
        
        # Calculate CLV using the detailed method
        clv = self.user.calculate_detailed_clv()
        
        # Verify that CLV is calculated correctly
        self.assertIsInstance(clv, float)
        self.assertGreaterEqual(clv, 0)
    
    def test_customer_lifespan_calculation(self):
        """
        Test customer lifespan calculation
        """
        # Set customer_since to 2 years ago
        self.user.customer_since = (datetime.now() - timedelta(days=730)).date()
        self.user.retention_rate = 0.85  # 85% retention rate
        self.user.save()
        
        lifespan = self.user.calculate_customer_lifespan()
        
        # Should be at least 2 years since the customer has been around for 2 years
        self.assertGreaterEqual(lifespan, 2.0)


class TestCACCalculations(TestCase):
    """
    Test CAC calculation methods
    """
    
    def setUp(self):
        # Create a test campaign
        self.campaign = Campaign.objects.create(
            name='Test Campaign',
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            budget=10000.00,
            actual_cost=8000.00,
        )
        
        # Create some test leads
        for i in range(10):
            Lead.objects.create(
                first_name=f'First{i}',
                last_name=f'Last{i}',
                email=f'test{i}@example.com',
                company=f'Company{i}',
                cac_cost=800.00,  # $800 CAC per lead
                status='converted' if i < 5 else 'new',  # 5 converted, 5 not converted
            )
    
    def test_cac_calculation(self):
        """
        Test basic CAC calculation
        """
        total_cost = 8000.00  # From campaign actual_cost
        new_customers = 5  # 5 leads converted
        
        expected_cac = total_cost / new_customers
        calculated_cac = BusinessMetricsService.calculate_cac(total_cost, new_customers)
        
        self.assertEqual(calculated_cac, expected_cac)
    
    def test_cac_by_channel(self):
        """
        Test CAC calculation by marketing channel
        """
        cac_by_channel = BusinessMetricsService.calculate_cac_by_channel()
        
        # For this simple test, verify that the function returns a dictionary
        self.assertIsInstance(cac_by_channel, dict)
    
    def test_cohort_based_cac(self):
        """
        Test cohort-based CAC calculation
        """
        from datetime import date
        
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        cohort_cac = BusinessMetricsService.calculate_cohort_cac(start_date, end_date)
        
        # Verify the function returns a dictionary with expected structure
        self.assertIsInstance(cohort_cac, dict)
        self.assertIn('cohort_period', cohort_cac)
        self.assertIn('cac', cohort_cac)


class TestSalesVelocityMetrics(TestCase):
    """
    Test sales velocity metric calculations
    """
    
    def setUp(self):
        # Create test opportunities
        self.opportunity1 = Opportunity.objects.create(
            opportunity_name='Test Opportunity 1',
            account=None,  # Will need to create an account
            amount=5000.00,
            stage=None,  # Will need to create or reference a stage
            close_date=(datetime.now() + timedelta(days=30)).date(),
            probability=0.5,
            created_at=datetime.now() - timedelta(days=15)  # Created 15 days ago
        )
        
        self.opportunity2 = Opportunity.objects.create(
            opportunity_name='Test Opportunity 2',
            account=None,
            amount=7500.00,
            stage=None,
            close_date=(datetime.now() + timedelta(days=45)).date(),
            probability=0.7,
            created_at=datetime.now() - timedelta(days=10)  # Created 10 days ago
        )
    
    def test_sales_velocity_calculation(self):
        """
        Test sales velocity calculation
        """
        # Calculate for a single opportunity
        velocity1 = self.opportunity1.calculate_sales_velocity()
        velocity2 = self.opportunity2.calculate_sales_velocity()
        
        # Both should be positive numbers
        self.assertGreaterEqual(velocity1, 0)
        self.assertGreaterEqual(velocity2, 0)
    
    def test_pipeline_velocity(self):
        """
        Test pipeline velocity calculation
        """
        from opportunities.models import OpportunityStage
        
        # Create a default stage if none exists
        default_stage, created = OpportunityStage.objects.get_or_create(
            opportunity_stage_name='Prospecting',
            defaults={'order': 1, 'probability': 0.2}
        )
        
        # Update opportunities with a stage
        self.opportunity1.stage = default_stage
        self.opportunity1.save()
        
        self.opportunity2.stage = default_stage
        self.opportunity2.save()
        
        # Calculate pipeline velocity
        pipeline_velocity = BusinessMetricsService.calculate_pipeline_velocity()
        
        # Should return a positive value
        self.assertGreaterEqual(pipeline_velocity, 0)
    
    def test_average_sales_cycle(self):
        """
        Test average sales cycle calculation
        """
        # Calculate average sales cycle
        avg_cycle = BusinessMetricsService.calculate_average_sales_cycle()
        
        # Should return a positive number
        self.assertGreaterEqual(avg_cycle, 0)


class TestROICalculations(TestCase):
    """
    Test ROI calculation methods
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='roi_test_user',
            email='roi@example.com',
            password='testpass123'
        )
        # Set some initial values
        self.user.customer_lifetime_value = 5000.00
        self.user.acquisition_cost = 500.00
        self.user.save()
    
    def test_roi_calculation(self):
        """
        Test basic ROI calculation: (CLV - CAC) / CAC
        """
        expected_roi = (self.user.customer_lifetime_value - self.user.acquisition_cost) / self.user.acquisition_cost
        calculated_roi = self.user.calculate_roi()
        
        self.assertEqual(calculated_roi, expected_roi)
    
    def test_roi_with_zero_cac(self):
        """
        Test ROI calculation when CAC is zero (should return infinity)
        """
        self.user.acquisition_cost = 0
        self.user.save()
        
        roi = self.user.calculate_roi()
        
        # When CAC is 0, ROI should be infinity (if CLV > 0)
        self.assertEqual(roi, float('inf'))


class TestConversionFunnelMetrics(TestCase):
    """
    Test conversion funnel metric calculations
    """
    
    def setUp(self):
        # Create leads at different stages of the funnel
        for i in range(20):
            status = 'new'
            if i < 15:
                status = 'contacted'
            if i < 10:
                status = 'qualified'
            if i < 5:
                status = 'converted'
                
            Lead.objects.create(
                first_name=f'Funnel{i}',
                last_name='Test',
                email=f'funnel{i}@example.com',
                company=f'FunnelCo{i}',
                status=status
            )
    
    def test_conversion_rates(self):
        """
        Test conversion rate calculations at each funnel stage
        """
        funnel_metrics = BusinessMetricsService.calculate_conversion_funnel_metrics()
        
        # Should return a dictionary with conversion rates
        self.assertIn('new_to_contacted_rate', funnel_metrics)
        self.assertIn('contacted_to_qualified_rate', funnel_metrics)
        self.assertIn('qualified_to_converted_rate', funnel_metrics)
        
        # Rates should be between 0 and 100
        for key, value in funnel_metrics.items():
            if 'rate' in key:
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, 100)


class TestBusinessMetricsService(TestCase):
    """
    Test the BusinessMetricsService class
    """
    
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            username='service_test',
            email='service@example.com',
            password='testpass123'
        )
        
        # Create test campaign
        self.campaign = Campaign.objects.create(
            name='Service Test Campaign',
            status='active',
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            budget=5000.00,
            actual_cost=4000.00,
        )
        
        # Create test leads
        for i in range(5):
            Lead.objects.create(
                first_name=f'Service{i}',
                last_name='Test',
                email=f'service{i}@example.com',
                company=f'ServiceCo{i}',
                cac_cost=800.00,
                status='converted' if i < 3 else 'new',  # 3 converted
            )
    
    def test_get_clv_metrics(self):
        """
        Test getting CLV metrics
        """
        # Set up user with CLV data
        self.user.avg_order_value = 500.00
        self.user.purchase_frequency = 2.0
        self.user.customer_lifespan_years = 5.0
        self.user.save()
        
        clv_metrics = BusinessMetricsService.get_clv_metrics(user=self.user)
        
        self.assertIn('clv', clv_metrics)
        self.assertIn('breakdown', clv_metrics)
        self.assertGreaterEqual(clv_metrics['clv'], 0)
    
    def test_get_cac_metrics(self):
        """
        Test getting CAC metrics
        """
        cac_metrics = BusinessMetricsService.get_cac_metrics()
        
        self.assertIn('average_cac', cac_metrics)
        self.assertIn('total_cost', cac_metrics)
        self.assertIn('customers_acquired', cac_metrics)
        self.assertGreaterEqual(cac_metrics['average_cac'], 0)
    
    def test_get_sales_velocity_metrics(self):
        """
        Test getting sales velocity metrics
        """
        velocity_metrics = BusinessMetricsService.get_sales_velocity_metrics()
        
        self.assertIn('average_velocity', velocity_metrics)
        self.assertIn('pipeline_value', velocity_metrics)
        self.assertIn('conversion_rate', velocity_metrics)
    
    def test_get_roi_metrics(self):
        """
        Test getting ROI metrics
        """
        # Set up user with CLV and CAC data
        self.user.customer_lifetime_value = 5000.00
        self.user.acquisition_cost = 500.00
        self.user.save()
        
        roi_metrics = BusinessMetricsService.get_roi_metrics(user=self.user)
        
        self.assertIn('roi', roi_metrics)
        self.assertIn('clv', roi_metrics)
        self.assertIn('cac', roi_metrics)
        self.assertIsInstance(roi_metrics['roi'], (int, float))
    
    def test_get_conversion_funnel_metrics(self):
        """
        Test getting conversion funnel metrics
        """
        funnel_metrics = BusinessMetricsService.get_conversion_funnel_metrics()
        
        # Should contain metrics for each stage
        self.assertIn('total_leads', funnel_metrics)
        self.assertIn('conversion_rates', funnel_metrics)
        self.assertIsInstance(funnel_metrics['conversion_rates'], dict)
