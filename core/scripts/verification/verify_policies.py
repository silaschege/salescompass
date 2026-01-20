import os, sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from core.object_permissions import OBJECT_POLICIES

required = [
    'tenants.TenantMember',
    'tenants.TenantRole',
    'tenants.TenantTerritory'
]

missing = []
for m in required:
    if m not in OBJECT_POLICIES:
        missing.append(m)
    else:
        print(f"[OK] Policy found for {m}: {OBJECT_POLICIES[m].__name__}")

if missing:
    print(f"[FAIL] Missing policies for: {missing}")
    sys.exit(1)
else:
    print("[SUCCESS] All required policies are registered.")
