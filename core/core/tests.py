from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from core.models import User


class UserModelTests(TestCase):
    """Tests for User model methods"""
    
    def setUp(self):
        """Create test user with known CLV values"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Set known values for testing
        self.user.avg_order_value = Decimal('100.00')
        self.user.purchase_frequency = 12  # Monthly purchases
        self.user.retention_rate = Decimal('0.8500')  # 85% retention
        self.user.acquisition_cost = Decimal('50.00')
        self.user.customer_since = date.today() - timedelta(days=365)
        self.user.save()

    def test_user_creation(self):
        """Test that user is created correctly"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_calculate_clv_standard(self):
        """Test CLV calculation with standard retention rate"""
        # Formula: (AOV × Frequency × Retention) / (1 - Retention) - CAC
        # (100 × 12 × 0.85) / (1 - 0.85) - 50 = 1020 / 0.15 - 50 = 6800 - 50 = 6750
        clv = self.user.calculate_clv()
        expected = (100 * 12 * 0.85) / (1 - 0.85) - 50
        self.assertAlmostEqual(float(clv), expected, places=2)

    def test_calculate_clv_zero_retention(self):
        """Test CLV calculation when retention is zero"""
        self.user.retention_rate = Decimal('0.0000')
        self.user.save()
        
        clv = self.user.calculate_clv()
        # With 0 retention, CLV should be 0 (max of -CAC and 0)
        self.assertEqual(float(clv), 0)

    def test_calculate_clv_full_retention(self):
        """Test CLV calculation when retention is 100%"""
        self.user.retention_rate = Decimal('1.0000')
        self.user.save()
        
        clv = self.user.calculate_clv()
        # With 100% retention, uses 5-year estimate: AOV × Frequency × 5
        expected = 100 * 12 * 5
        self.assertAlmostEqual(float(clv), expected, places=2)

    def test_calculate_roi_positive(self):
        """Test ROI calculation with positive return"""
        # ROI = (CLV - CAC) / CAC
        clv = self.user.calculate_clv()
        roi = self.user.calculate_roi(float(clv))
        
        # CLV is ~6750, CAC is 50
        # ROI = (6750 - 50) / 50 = 134
        self.assertGreater(roi, 100)

    def test_calculate_roi_zero_cac(self):
        """Test ROI calculation when CAC is zero"""
        self.user.acquisition_cost = Decimal('0.00')
        self.user.save()
        
        roi = self.user.calculate_roi(1000)
        # With zero CAC and positive revenue, ROI should be infinity
        self.assertEqual(roi, float('inf'))

    def test_calculate_customer_lifespan(self):
        """Test customer lifespan calculation"""
        lifespan = self.user.calculate_customer_lifespan()
        
        # With 85% retention, churn is 15%, lifespan = 1/0.15 ≈ 6.67 years
        # But for customers < 2 years tenure, uses retention-based estimate
        self.assertGreater(lifespan, 0)

    def test_calculate_clv_simple(self):
        """Test simple CLV calculation"""
        clv = self.user.calculate_clv_simple()
        
        # CLV = AOV × Frequency × Lifespan
        # Should be positive for our test user
        self.assertGreater(float(clv), 0)

    def test_update_clv(self):
        """Test that update_clv() saves calculated values"""
        # Reset values
        self.user.customer_lifetime_value = Decimal('0.00')
        self.user.save()
        
        # Call update_clv
        clv = self.user.update_clv()
        
        # Refresh from database
        self.user.refresh_from_db()
        
        # Verify CLV was saved
        self.assertGreater(float(self.user.customer_lifetime_value), 0)


class UserCLVEdgeCaseTests(TestCase):
    """Edge case tests for CLV calculations"""
    
    def test_new_user_no_data(self):
        """Test CLV for new user with no purchase data"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        # New user with default values
        clv = user.calculate_clv()
        
        # Should return 0 for new user with no data
        self.assertEqual(float(clv), 0)

    def test_high_retention_rate(self):
        """Test CLV with very high retention rate"""
        user = User.objects.create_user(
            username='loyaluser',
            email='loyal@example.com',
            password='testpass123'
        )
        user.avg_order_value = Decimal('500.00')
        user.purchase_frequency = 24
        user.retention_rate = Decimal('0.9900')  # 99% retention
        user.save()
        
        clv = user.calculate_clv()
        
        # Very high retention should give very high CLV
        self.assertGreater(float(clv), 10000)

    def test_low_value_customer(self):
        """Test CLV for low-value customer"""
        user = User.objects.create_user(
            username='lowvalue',
            email='low@example.com',
            password='testpass123'
        )
        user.avg_order_value = Decimal('10.00')
        user.purchase_frequency = 1
        user.retention_rate = Decimal('0.5000')
        user.acquisition_cost = Decimal('100.00')
        user.save()
        
        clv = user.calculate_clv()
        
        # Low value customer with high CAC might have 0 CLV (capped at 0)
        self.assertGreaterEqual(float(clv), 0)
