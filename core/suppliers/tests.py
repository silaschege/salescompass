from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from .models import Supplier, SupplierCategory, SupplierPerformanceReview, SupplierDocument
from django.utils import timezone
import datetime

User = get_user_model()

class SupplierPhase2Tests(TestCase):
    def setUp(self):
        # Create Tenant and User
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.user = User.objects.create_user(username="testuser", password="password", tenant=self.tenant)
        self.client = Client()
        self.client.login(username="testuser", password="password")
        
        # Create Category
        self.category = SupplierCategory.objects.create(
            name="Test Category", 
            tenant=self.tenant
        )
        
        # Create Supplier
        self.supplier = Supplier.objects.create(
            supplier_name="Test Supplier",
            category=self.category,
            tenant=self.tenant,
            status='active'
        )

    def test_performance_scoring(self):
        """Test performance review creation and rating calculation."""
        # Initial score should be None
        self.assertIsNone(self.supplier.overall_score)
        
        # Create a Review
        review1 = SupplierPerformanceReview.objects.create(
            supplier=self.supplier,
            tenant=self.tenant,
            date=datetime.date.today(),
            delivery_rating=5.00,
            quality_rating=4.00,
            responsiveness_rating=5.00,
            created_by=self.user
        )
        
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.delivery_rating, 5.00)
        self.assertEqual(self.supplier.quality_rating, 4.00)
        self.assertEqual(self.supplier.responsiveness_rating, 5.00)
        # Average: (5+4+5)/3 = 4.67
        self.assertAlmostEqual(float(self.supplier.overall_score), 4.67, places=2)
        
        # Create second review
        review2 = SupplierPerformanceReview.objects.create(
            supplier=self.supplier,
            tenant=self.tenant,
            date=datetime.date.today(),
            delivery_rating=3.00,
            quality_rating=4.00,
            responsiveness_rating=3.00,
            created_by=self.user
        )
        
        self.supplier.refresh_from_db()
        # Delivery: (5+3)/2 = 4
        # Quality: (4+4)/2 = 4
        # Responsiveness: (5+3)/2 = 4
        # Overall: 4.00
        self.assertEqual(self.supplier.delivery_rating, 4.00)
        self.assertEqual(self.supplier.overall_score, 4.00)

    def test_document_management(self):
        """Test document upload and deletion."""
        # Upload
        doc = SupplierDocument.objects.create(
            supplier=self.supplier,
            tenant=self.tenant,
            document_type='contract',
            name='Test Contract',
            file='test.pdf' # Mock file
        )
        self.assertEqual(self.supplier.documents.count(), 1)
        
        # Delete via View
        url = reverse('suppliers:document_delete', args=[doc.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302) # Redirect
        self.assertEqual(self.supplier.documents.count(), 0)

    def test_supplier_classification(self):
        """Test supplier classification field."""
        self.supplier.classification = 'strategic'
        self.supplier.save()
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.classification, 'strategic')
        self.assertEqual(self.supplier.get_classification_display(), 'Strategic')

    def test_category_delete(self):
        """Test category deletion."""
        cat_id = self.category.pk
        url = reverse('suppliers:category_delete', args=[cat_id])
        
        # Verify supplier has category
        self.assertEqual(self.supplier.category, self.category)
        
        # Delete category
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Check category is gone
        self.assertFalse(SupplierCategory.objects.filter(pk=cat_id).exists())
        
        # Check supplier category is now Null (on_delete=SET_NULL)
        self.supplier.refresh_from_db()
        self.assertIsNone(self.supplier.category)
