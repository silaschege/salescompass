import os
import django
import sys

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from inventory.models import Warehouse, StockLocation, StockLevel
from pos.models import POSTerminal, POSSession, POSTransaction
from products.models import Product
from core.models import User
from decimal import Decimal

def verify_foundation():
    print("Verifying POS System Foundation...")
    
    # Check apps
    from django.apps import apps
    if not apps.is_installed('inventory'):
        print("FAIL: Inventory app not installed")
        return
    if not apps.is_installed('pos'):
        print("FAIL: POS app not installed")
        return
    print("PASS: Apps installed")
    
    # Check Product model fields
    fields = [f.name for f in Product._meta.get_fields()]
    expected = ['track_inventory', 'low_stock_threshold', 'weight']
    missing = [f for f in expected if f not in fields]
    if missing:
        print(f"FAIL: Missing fields on Product model: {missing}")
    else:
        print("PASS: Product model updated")
        
    print("Verification complete.")

if __name__ == '__main__':
    verify_foundation()
