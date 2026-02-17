"""
Integration tests for the main dashboard.
Tests performance, chart rendering, and mobile responsiveness.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from time import time

from leads.models import Lead
from opportunities.models import Opportunity, OpportunityStage
from cases.models import Case
from sales.models import Sale
from accounts.models import Account
from core.models import Role

User = get_user_model()


class DashboardIntegrationTests(TestCase):
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create role with visibility rules
        self.role = Role.objects.create(
            name='Sales Rep',
            permissions=['leads:read', 'opportunities:read'],
            data_visibility_rules={
                'lead': 'own_only',
                'opportunity': 'own_only',
                'case': 'own_only'
            }
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=self.role
        )
        
        # Create test account
        self.account = Account.objects.create(
            name='Test Account',
            industry='tech',
            tier='gold',
            country='US',
            owner=self.user
        )
        
        # Create product for sales
        from sales.models import Product
        self.product = Product.objects.create(
            name='Test Product',
            product_type='software',
            price=100.00
        )
        
        # Create opportunity stages
        self.stage1 = OpportunityStage.objects.create(
            name='Discovery',
            order=1,
            probability=0.2
        )
        self.stage2 = OpportunityStage.objects.create(
            name='Proposal',
            order=2,
            probability=0.5
        )
        
        # Create sample data
        self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for testing."""
        # Create leads
        for i in range(5):
            Lead.objects.create(
                first_name=f'Test{i}',
                last_name='Lead',
                email=f'lead{i}@test.com',
                company=f'Company {i}',
                industry='tech',
                owner=self.user
            )
        
        # Create opportunities
        for i in range(5):
            Opportunity.objects.create(
                name=f'Opportunity {i}',
                account=self.account,
                amount=1000 * (i + 1),
                stage=self.stage1 if i < 3 else self.stage2,
                close_date=timezone.now().date(),
                owner=self.user
            )
        
        # Create cases
        for i in range(5):
            Case.objects.create(
                subject=f'Case {i}',
                description=f'Test case {i}',
                account=self.account,
                priority='high' if i < 2 else 'medium',
                owner=self.user
            )
        
        # Create sales
        for i in range(3):
            Sale.objects.create(
                account=self.account,
                product=self.product,
                sale_type='software',
                amount=500 * (i + 1),
                sales_rep=self.user
            )
    
    def test_dashboard_loads_under_2_seconds(self):
        """Test that dashboard loads in under 2 seconds."""
        # Login first
        self.client.login(username='test@example.com', password='testpass123')
        
        # Measure load time
        start_time = time()
        response = self.client.get(reverse('dashboard:main'))
        load_time = time() - start_time
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Check load time (should be well under 2 seconds)
        self.assertLess(load_time, 2.0, f"Dashboard loaded in {load_time:.3f}s, exceeds 2s threshold")
        
        # Log actual load time for monitoring
        print(f"\n✓ Dashboard loaded in {load_time:.3f} seconds")
    
    def test_charts_render_correctly(self):
        """Test that charts are properly included in the response."""
        self.client.login(username='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:main'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Verify Chart.js CDN is loaded
        self.assertIn('chart.js', content.lower(), "Chart.js CDN not found")
        
        # Verify revenue chart canvas exists
        self.assertIn('revenueChart', content, "Revenue chart canvas not found")
        
        # Verify pipeline chart canvas exists
        self.assertIn('pipelineChart', content, "Pipeline chart canvas not found")
        
        print("\n✓ Chart elements verified")
    
    def test_mobile_responsiveness(self):
        """Test that dashboard uses responsive CSS classes."""
        self.client.login(username='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:main'))
        content = response.content.decode('utf-8')
        
        # Verify responsive Bootstrap classes
        responsive_classes = [
            'col-md-3',   # Stats cards
            'col-md-8',   # Revenue chart
            'col-md-4',   # Pipeline chart
            'col-md-12',  # Activity feed
        ]
        
        for css_class in responsive_classes:
            self.assertIn(css_class, content, f"Responsive class '{css_class}' not found")
        
        # Verify container-fluid for full-width layout
        self.assertIn('container-fluid', content, "Fluid container not found")
        
        # Verify responsive chart settings
        self.assertIn('responsive: true', content, "Chart responsive setting not found")
        self.assertIn('maintainAspectRatio', content, "Chart aspect ratio setting not found")
        
        print("\n✓ Mobile responsive design verified")
    
    def test_dashboard_stats_cards(self):
        """Test that stats cards display correct data."""
        self.client.login(username='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:main'))
        
        # Verify context data
        self.assertIn('total_leads', response.context)
        self.assertIn('total_opportunities', response.context)
        self.assertIn('total_cases', response.context)
        self.assertIn('total_revenue', response.context)
        
        # Verify data is integer/numeric
        self.assertIsInstance(response.context['total_leads'], int)
        self.assertIsInstance(response.context['total_opportunities'], int)
        self.assertIsInstance(response.context['total_cases'], int)
        self.assertIsInstance(response.context['total_revenue'], int)
        
        # Verify expected counts
        self.assertEqual(response.context['total_leads'], 5)
        self.assertEqual(response.context['total_opportunities'], 5)
        self.assertEqual(response.context['total_cases'], 5)
        
        print("\n✓ Stats cards data verified")
    
    def test_activity_feed_present(self):
        """Test that activity feed is populated."""
        self.client.login(username='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:main'))
        
        # Verify activity feed in context
        self.assertIn('recent_activities', response.context)
        activities = response.context['recent_activities']
        
        # Should have activities (limited to 10)
        self.assertGreater(len(activities), 0)
        self.assertLessEqual(len(activities), 10)
        
        # Verify activity structure
        if activities:
            activity = activities[0]
            self.assertIn('type', activity)
            self.assertIn('title', activity)
            self.assertIn('description', activity)
            self.assertIn('timestamp', activity)
            
            # Verify type is valid
            self.assertIn(activity['type'], ['lead', 'opportunity', 'case'])
        
        print(f"\n✓ Activity feed verified ({len(activities)} activities)")
    
    def test_performance_with_large_dataset(self):
        """Test dashboard performance with larger dataset."""
        # Create additional data
        for i in range(50):
            Lead.objects.create(
                first_name=f'Perf{i}',
                last_name='Test',
                email=f'perf{i}@test.com',
                company=f'Perf Co {i}',
                industry='tech',
                owner=self.user
            )
        
        self.client.login(username='test@example.com', password='testpass123')
        
        start_time = time()
        response = self.client.get(reverse('dashboard:main'))
        load_time = time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0, f"Dashboard with large dataset loaded in {load_time:.3f}s")
        
        print(f"\n✓ Large dataset performance: {load_time:.3f} seconds")
