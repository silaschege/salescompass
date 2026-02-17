
import os
import django
import sys

# Setup Django environment
# The project root is 'core', so we need to add it to path.
# Assuming this script is in salescompass-main (parent of core).
project_path = os.path.join(os.getcwd(), 'core')
sys.path.append(project_path)
# Also add current directory
sys.path.append(os.getcwd())

print(f"DEBUG: sys.path: {sys.path}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    # Continue anyway to debug imports

print("Verifying Invoicing Migration...")

try:
    print("Attempting to import core...")
    import core
    print(f"  - core imported: {core}")
    print(f"  - core file: {core.__file__}")

    print("Importing core.billing.models...")
    from core.billing import models as billing_models
    print("  - Subscription:", billing_models.Subscription)
    print("  - Invoice (Platform):", billing_models.Invoice)
    
    print("Importing core.billing.views...")
    from core.billing import views as billing_views
    print("  - InvoiceListView:", billing_views.InvoiceListView)
    
    print("Importing core.billing.urls...")
    from core.billing import urls as billing_urls
    print("  - urlpatterns found.")

    print("Importing core.invoicing.models...")
    from core.invoicing import models as invoicing_models
    print("  - Invoice (Tenant):", invoicing_models.Invoice)
    print("  - InvoiceLine:", invoicing_models.InvoiceLine)
    
    print("Importing core.invoicing.forms...")
    from core.invoicing import forms as invoicing_forms
    print("  - InvoiceForm:", invoicing_forms.InvoiceForm)
    
    print("Importing core.invoicing.views...")
    from core.invoicing import views as invoicing_views
    print("  - InvoiceListView:", invoicing_views.InvoiceListView)
    
    print("Importing core.invoicing.urls...")
    from core.invoicing import urls as invoicing_urls
    print("  - urlpatterns found.")
    
    print("Importing core.invoicing.payment_providers...")
    from core.invoicing import payment_providers
    print("  - module imported.")
    
    print("\nSUCCESS: All modules imported correctly.")
    
except ImportError as e:
    print(f"\nERROR: Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except AttributeError as e:
    print(f"\nERROR: Attribute error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\nERROR: Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
