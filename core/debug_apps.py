import os
import django
import sys

sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

try:
    from inventory.apps import InventoryConfig
    from pos.apps import PosConfig
    print(f"Inventory Config: {InventoryConfig.name}")
    print(f"POS Config: {PosConfig.name}")
    
    from django.apps import apps
    print(f"Installed Apps: {apps.is_installed('inventory')}, {apps.is_installed('pos')}")
    
    from inventory.models import Warehouse
    print(f"Warehouse model loaded: {Warehouse}")
except Exception as e:
    print(f"Error: {e}")
