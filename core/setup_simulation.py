import os
import django
import sys

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/salescompass/salescompass')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.contrib.auth import get_user_model
from tenants.models import Tenant
from billing.models import Plan

User = get_user_model()

def setup():
    print("Setting up simulation environment...")

    # 1. Create Superuser
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Created superuser: admin/admin")
    else:
        print("Superuser 'admin' already exists.")

    # 2. Create Plan
    plan, created = Plan.objects.get_or_create(
        name='Standard',
        defaults={
            'slug': 'standard',
            'tier': 'pro',
            'price_monthly': 100.00,
            'price_yearly': 1000.00,
            'features': {'users': 10, 'storage': '10GB'},
            'is_active': True
        }
    )
    if created:
        print("Created Plan: Standard")
    else:
        print("Plan 'Standard' already exists.")

    # 3. Create Tenant in Trial
    tenant, created = Tenant.objects.get_or_create(
        name='Test Tenant',
        defaults={
            'subscription_status': 'trialing',
            'domain': 'test-tenant.example.com'
        }
    )
    if created:
        print("Created Tenant: Test Tenant (trialing)")
    else:
        # Ensure it is in trialing status
        if tenant.subscription_status != 'trialing':
            tenant.subscription_status = 'trialing'
            tenant.save()
            print("Updated Tenant 'Test Tenant' to trialing status.")
        else:
            print("Tenant 'Test Tenant' already exists and is in trial.")

    print("Setup complete.")

if __name__ == '__main__':
    setup()
