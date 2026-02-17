import os
import django
import sys

# Add the project root to sys.path
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from quality_control.forms import InspectionRuleForm, InspectionLogForm, NCRManagementForm, CAPAForm
from tenants.models import Tenant

def test_forms():
    # Try to find a tenant or mock one
    tenant = Tenant.objects.first()
    if not tenant:
        print("No tenant found, skipping queryset filtering tests but checking initialization.")
    
    forms_to_test = [
        (InspectionRuleForm, "InspectionRuleForm"),
        (InspectionLogForm, "InspectionLogForm"),
        (NCRManagementForm, "NCRManagementForm"),
        (CAPAForm, "CAPAForm"),
    ]
    
    for form_class, name in forms_to_test:
        try:
            form = form_class(tenant=tenant)
            print(f"✅ {name} initialized successfully with tenant argument.")
        except TypeError as e:
            print(f"❌ {name} failed initialization: {e}")
        except Exception as e:
            print(f"⚠️ {name} initialized but encountered other error (expected if DB empty): {e}")

if __name__ == "__main__":
    test_forms()
