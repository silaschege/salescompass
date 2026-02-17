
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.urls import reverse
from core.apps_registry import AVAILABLE_APPS

print("Verifying App URLs from Registry...")
all_valid = True
for app in AVAILABLE_APPS:
    try:
        url = reverse(app['url_name'])
        print(f"[OK] {app['name']} ({app['id']}) -> {url}")
    except Exception as e:
        print(f"[FAIL] {app['name']} ({app['id']}) -> {e}")
        all_valid = False

if all_valid:
    print("\nAll App URLs valid.")
    sys.exit(0)
else:
    print("\nSome URLs failed to resolve.")
    sys.exit(1)
