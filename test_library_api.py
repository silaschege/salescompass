import os
import django
import sys
import json

# Add the project root to sys.path
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from quality_control.models import QualityCheckLibrary
from quality_control.views import library_list_api
from tenants.models import Tenant
from core.models import User

def test_api():
    # Setup
    tenant, _ = Tenant.objects.get_or_create(name="Test Tenant", defaults={'slug': 'test-tenant'})
    user, _ = User.objects.get_or_create(username="test_user", defaults={'tenant': tenant})
    
    # Create library items
    QualityCheckLibrary.objects.get_or_create(
        tenant=tenant,
        label="Cleanliness Check",
        check_type="bool",
        category="Safety"
    )
    QualityCheckLibrary.objects.get_or_create(
        tenant=tenant,
        label="Weight Measurement",
        check_type="number",
        category="Specs"
    )

    # Request
    factory = RequestFactory()
    request = factory.get('/api/library/')
    request.user = user
    request.tenant = tenant

    # Call API
    response = library_list_api(request)
    data = json.loads(response.content)

    print(f"Status Code: {response.status_code}")
    print(f"Items found: {len(data['items'])}")
    for item in data['items']:
        print(f"- {item['label']} ({item['type']}) in {item['category']}")

    if len(data['items']) >= 2:
        print("✅ API verification successful.")
    else:
        print("❌ API verification failed.")

if __name__ == "__main__":
    test_api()
