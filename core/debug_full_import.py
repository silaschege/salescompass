
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')

try:
    print("Initializing Django...")
    django.setup()
    print("Django initialized successfully.")
except Exception as e:
    print(f"Django initialization failed: {e}")
    import traceback
    traceback.print_exc()

print("\nAttempting to import models explicitly...")
try:
    print("Importing core.models...")
    from core import models as core_models
    print("core.models imported.")

    print("Importing tenants.models...")
    from tenants import models as tenants_models
    print("tenants.models imported.")

    print("Importing billing.models...")
    from billing import models as billing_models
    print("billing.models imported.")

    print("Importing invoicing.models...")
    from invoicing import models as invoicing_models
    print("invoicing.models imported.")
    
    print("Importing access_control.models...")
    from access_control import models as ac_models
    print("access_control.models imported.")

    print("Importing accounting.models...")
    from accounting import models as acc_models
    print("accounting.models imported.")

except ImportError as e:
    print(f"\nImport Failed: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\nOther Error: {e}")
    import traceback
    traceback.print_exc()
