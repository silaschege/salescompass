import os
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from products.models import Product, ProductCategory
from pos.services import POSService

class CategoriesAndImagesVerification(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", 
            password="password",
            tenant=self.tenant
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_category_hierarchy(self):
        """Verify we can create nested categories."""
        # Create Root
        electronics = ProductCategory.objects.create(
            name="Electronics",
            tenant=self.tenant
        )
        
        # Create Child
        phones = ProductCategory.objects.create(
            name="Phones",
            parent=electronics,
            tenant=self.tenant
        )
        
        self.assertEqual(phones.parent, electronics)
        self.assertIn(phones, electronics.children.all())
        print("Category Hierarchy: OK")

    def test_product_with_image_and_category(self):
        """Verify product can be created with image and category."""
        cat = ProductCategory.objects.create(name="Toys", tenant=self.tenant)
        
        # Small 1x1 GIF
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04'
            b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
            b'\x01\x00\x3b'
        )
        image = SimpleUploadedFile("product.gif", small_gif, content_type="image/gif")

        product = Product.objects.create(
            product_name="Action Figure",
            sku="TOY-001",
            base_price=20.00,
            category=cat,
            image=image,
            tenant=self.tenant,
            owner=self.user
        )
        
        self.assertEqual(product.category, cat)
        self.assertTrue(product.image)
        print("Product Image & Category: OK")

    def test_pos_search_by_category(self):
        """Verify POS search integration."""
        cat1 = ProductCategory.objects.create(name="Cat 1", tenant=self.tenant)
        cat2 = ProductCategory.objects.create(name="Cat 2", tenant=self.tenant)
        
        p1 = Product.objects.create(
            product_name="P1", sku="S1", base_price=10, category=cat1, tenant=self.tenant, owner=self.user
        )
        p2 = Product.objects.create(
            product_name="P2", sku="S2", base_price=10, category=cat2, tenant=self.tenant, owner=self.user
        )
        
        # Test generic search (should find both if active)
        results = POSService.search_products("P", self.tenant)
        self.assertEqual(len(results), 2)
        
        # Assuming we add category filtering in POSService later or verify via View query
        # Currently POSService.search_products is simple query, 
        # but let's verify models are ready for filtering
        filtered = Product.objects.filter(category=cat1, tenant=self.tenant)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), p1)
        print("POS Category Filtering Readiness: OK")
