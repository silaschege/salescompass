import os
import django
import sys

# Set up Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from products.models import Product, ProductBundle, CompetitorProduct

def verify_product_str():
    print("Verifying Product models __str__ methods...")
    try:
        # Test Product
        p = Product(product_name="Test Product", sku="TEST-001")
        print(f"Product __str__: {str(p)}")
        assert str(p) == "Test Product (TEST-001)"
        
        # Test ProductBundle
        pb = ProductBundle(product_bundle_name="Test Bundle")
        print(f"ProductBundle __str__: {str(pb)}")
        assert str(pb) == "Test Bundle"
        
        # Test CompetitorProduct
        cp = CompetitorProduct(competitor_name="Comp Corp", competitor_product_name="Comp Prod")
        print(f"CompetitorProduct __str__: {str(cp)}")
        assert str(cp) == "Comp Corp - Comp Prod"
        
        print("\nSUCCESS: All Product model __str__ methods verified!")
        
    except Exception as e:
        print(f"\nFAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_product_str()
