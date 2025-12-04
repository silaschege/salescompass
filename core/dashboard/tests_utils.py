from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from dashboard.utils import (
    get_revenue_chart_data,
    get_pipeline_snapshot,
    get_activity_feed,
    calculate_percentage_change
)
from leads.models import Lead
from opportunities.models import Opportunity, OpportunityStage
from cases.models import Case
from sales.models import Sale
from accounts.models import Account

User = get_user_model()


class DashboardUtilsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Create test account
        self.account = Account.objects.create(
            name='Test Account',
            industry='tech',
            tier='gold',
            country='US',
            owner=self.user
        )
        
        # Create test product (required for Sale)
        from sales.models import Product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
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

    def test_get_revenue_chart_data(self):
        """Test revenue chart data generation."""
        # Create sales
        now = timezone.now()
        Sale.objects.create(
            account=self.account,
            product=self.product,
            sale_type='software',
            amount=1000,
            sale_date=now
        )
        Sale.objects.create(
            account=self.account,
            product=self.product,
            sale_type='software',
            amount=500,
            sale_date=now - timedelta(days=15)
        )
        
        result = get_revenue_chart_data(self.user, timeframe='6m')
        
        self.assertIn('labels', result)
        self.assertIn('data', result)
        
        # Verify JSON format
        labels = json.loads(result['labels'])
        data = json.loads(result['data'])
        
        self.assertEqual(len(labels), 6)
        self.assertEqual(len(data), 6)
        self.assertIsInstance(labels[0], str)
        self.assertIsInstance(data[0], (int, float))

    def test_get_pipeline_snapshot(self):
        """Test pipeline snapshot data generation."""
        # Create opportunities
        Opportunity.objects.create(
            name='Opp 1',
            account=self.account,
            amount=1000,
            stage=self.stage1,
            close_date=timezone.now().date(),
            owner=self.user
        )
        Opportunity.objects.create(
            name='Opp 2',
            account=self.account,
            amount=2000,
            stage=self.stage1,
            close_date=timezone.now().date(),
            owner=self.user
        )
        Opportunity.objects.create(
            name='Opp 3',
            account=self.account,
            amount=3000,
            stage=self.stage2,
            close_date=timezone.now().date(),
            owner=self.user
        )
        
        result = get_pipeline_snapshot(self.user)
        
        self.assertIn('labels', result)
        self.assertIn('data', result)
        
        labels = json.loads(result['labels'])
        data = json.loads(result['data'])
        
        # Should have 2 stages with data
        self.assertEqual(len(labels), 2)
        self.assertIn('Discovery', labels)
        self.assertIn('Proposal', labels)
        
        # Verify counts
        discovery_idx = labels.index('Discovery')
        self.assertEqual(data[discovery_idx], 2)

    def test_get_activity_feed(self):
        """Test activity feed generation."""
        # Create activities
        lead = Lead.objects.create(
            first_name='Test',
            last_name='Lead',
            email='lead@test.com',
            company='Test Co',
            industry='tech',
            owner=self.user
        )
        
        opp = Opportunity.objects.create(
            name='Test Opp',
            account=self.account,
            amount=1000,
            stage=self.stage1,
            close_date=timezone.now().date(),
            owner=self.user
        )
        
        case = Case.objects.create(
            subject='Test Case',
            description='Test description',
            account=self.account,
            priority='high',
            owner=self.user
        )
        
        activities = get_activity_feed(self.user, limit=10)
        
        self.assertIsInstance(activities, list)
        self.assertLessEqual(len(activities), 10)
        
        # Verify structure
        if activities:
            activity = activities[0]
            self.assertIn('type', activity)
            self.assertIn('title', activity)
            self.assertIn('description', activity)
            self.assertIn('timestamp', activity)

    def test_calculate_percentage_change(self):
        """Test percentage change calculation."""
        # Normal case
        self.assertEqual(calculate_percentage_change(150, 100), 50)
        
        # Decrease
        self.assertEqual(calculate_percentage_change(75, 100), -25)
        
        # Zero previous
        self.assertEqual(calculate_percentage_change(100, 0), 100)
        
        # Both zero
        self.assertEqual(calculate_percentage_change(0, 0), 0)
