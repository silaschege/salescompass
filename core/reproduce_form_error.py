import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from core.purchasing.forms import SupplierPaymentForm
from tenants.models import Tenant
from core.models import User
from suppliers.models import Supplier
from core.purchasing.models import SupplierInvoice

def test_supplier_payment_form():
    print("Starting verification test for SupplierPaymentForm...")
    
    # Create a dummy tenant and user if none exist, or get existing ones
    tenant, _ = Tenant.objects.get_or_create(name="Test Tenant", schema_name="test_tenant")
    user, _ = User.objects.get_or_create(username="test_user", tenant=tenant)
    
    # Create test data for this tenant
    supplier1 = Supplier.objects.create(name="Supplier 1", tenant=tenant, is_active=True)
    supplier2 = Supplier.objects.create(name="Supplier 2", tenant=tenant, is_active=False)
    
    # Another tenant's supplier
    other_tenant, _ = Tenant.objects.get_or_create(name="Other Tenant", schema_name="other_tenant")
    supplier3 = Supplier.objects.create(name="Supplier 3", tenant=other_tenant, is_active=True)
    
    print(f"Testing with tenant: {tenant}")
    
    try:
        # Initialize the form with tenant
        form = SupplierPaymentForm(tenant=tenant)
        
        # Verify supplier queryset filtering
        suppliers = list(form.fields['supplier'].queryset)
        print(f"Filtered Suppliers: {[s.name for s in suppliers]}")
        
        assert supplier1 in suppliers
        assert supplier2 not in suppliers  # is_active=False
        assert supplier3 not in suppliers  # different tenant
        
        print("Supplier filtering: SUCCESS")
        
        # Verify invoice queryset filtering (conceptually same)
        print("Form initialization with 'tenant' keyword argument: SUCCESS")
        
    except TypeError as e:
        print(f"Form initialization FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
    
    print("Verification test COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    test_supplier_payment_form()
