import os
import django
import sys

# Set up Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from core.models import User
from accounts.models import Account, AccountsUserProfile
from tenants.models import Tenant

def verify_upgrade():
    print("Verifying Accounts Upgrade...")
    
    # 1. Create a Test Tenant (if needed, usually User needs one)
    tenant, _ = Tenant.objects.get_or_create(name="Test Tenant", subdomain="testtenant")
    
    # 2. Create a User and verify Profile creation
    email = "testuser_accounts_upgrade@example.com"
    if User.objects.filter(email=email).exists():
        User.objects.filter(email=email).delete()
        
    user = User.objects.create_user(username="testuser_upgrade", email=email, password="password123", tenant=tenant)
    print(f"Created user: {user.email}")
    
    try:
        profile = user.accounts_profile
        print("PASS: AccountsUserProfile auto-created successfully.")
    except AccountsUserProfile.DoesNotExist:
        print("FAIL: AccountsUserProfile was NOT auto-created.")
        return

    # 3. Create an Account with new fields
    account = Account.objects.create(
        account_name="TechCorp Upgrade Test",
        tenant=tenant,
        billing_address_line1="123 Tech Lane",
        billing_city="San Francisco",
        annual_revenue=1000000.00,
        linkedin_url="https://linkedin.com/company/techcorp",
        tags=["tech", "high-growth"]
    )
    print(f"Created account: {account.account_name}")
    
    # Verify fields
    if account.annual_revenue == 1000000.00:
         print("PASS: Annual revenue saved correctly.")
    else:
         print(f"FAIL: Annual revenue mismatch: {account.annual_revenue}")

    if account.tags == ["tech", "high-growth"]:
        print("PASS: Tags saved correctly.")
    else:
        print(f"FAIL: Tags mismatch: {account.tags}")

    # 4. Verify Favorites
    profile.favorite_accounts.add(account)
    if profile.favorite_accounts.filter(id=account.id).exists():
        print("PASS: Account added to favorites successfully.")
    else:
        print("FAIL: Account NOT added to favorites.")

    # Cleanup
    account.delete()
    user.delete()
    print("Verification Complete.")

if __name__ == "__main__":
    verify_upgrade()
