
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')

try:
    django.setup()
    print("Django setup success")
except Exception as e:
    print(f"Django setup failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Attempting to import tenants.models...")
    from tenants import models as tenants_models
    print("tenants.models imported")
except ImportError as e:
    print(f"Failed to import tenants.models: {e}")
    import traceback
    traceback.print_exc()

try:
    print("Attempting to import billing.models...")
    from billing import models as billing_models
    print("billing.models imported")
except ImportError as e:
    print(f"Failed to import billing.models: {e}")
    import traceback
    traceback.print_exc()
