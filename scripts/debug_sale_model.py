
import os
import django
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salescompass.settings")
django.setup()

from sales.models import Sale
from django.conf import settings

def inspect_sale_model():
    print(f"AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
    
    field = Sale._meta.get_field('account')
    print(f"Sale.account field: {field}")
    print(f"Sale.account related model: {field.related_model}")
    
    try:
        from core.models import User
        print(f"core.models.User: {User}")
        print(f"Is related model User? {field.related_model == User}")
    except ImportError:
        print("Could not import core.models.User")

    try:
        from accounts.models import Account
        print(f"accounts.models.Account: {Account}")
        print(f"Is related model Account? {field.related_model == Account}")
    except ImportError:
        print("Could not import accounts.models.Account")

if __name__ == "__main__":
    inspect_sale_model()
